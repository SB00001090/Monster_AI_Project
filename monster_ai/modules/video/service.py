"""ComfyUI text-to-video / image-to-video — multi-backend unrestricted module."""
from __future__ import annotations

import logging
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from monster_ai.config import Settings
from monster_ai.core.generation_history import GenerationHistory
from monster_ai.core.generation_repair import GenerationRepair, validate_video_file
from monster_ai.core.progress import GenerationProgress
from monster_ai.core.self_repair import SelfRepairEngine
from monster_ai.core.vram_guard import VramGuard
from monster_ai.modules.image.comfyui import ComfyUIClient, ImageService
from monster_ai.modules.prompt.anti_collapse import build_negative
from monster_ai.modules.prompt.enhancer import PromptEnhancer
from monster_ai.modules.video.comfyui_video import build_animatediff_workflow, has_animatediff
from monster_ai.modules.video.presets import auto_backend, get_backend, list_backends, pick_profile
from monster_ai.modules.video.workflow_builder import (
    build_video_workflow,
    upload_image_to_comfy,
)

logger = logging.getLogger(__name__)


class VideoService:
    name = "video"

    def __init__(
        self,
        settings: Settings,
        repair: SelfRepairEngine,
        gen_repair: GenerationRepair,
        vram_guard: VramGuard,
        prompt_enhancer: PromptEnhancer,
        image_service: ImageService,
        progress: GenerationProgress | None = None,
        history: GenerationHistory | None = None,
    ) -> None:
        self.settings = settings
        self.gen_repair = gen_repair
        self.vram_guard = vram_guard
        self.prompt_enhancer = prompt_enhancer
        self.image_service = image_service
        self.progress = progress
        self.client = ComfyUIClient(settings.modules.video.comfyui_url)
        self.output_dir = Path(settings.modules.video.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(settings.modules.video.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.history = history

    async def health(self) -> dict[str, Any]:
        if not self.settings.modules.video.enabled:
            return {"enabled": False, "healthy": False, "message": "Module disabled"}
        ok = await self.client.ping()
        ad = await has_animatediff(self.client) if ok else False
        ffmpeg_ok = bool(shutil.which("ffmpeg"))
        vid_cfg = self.settings.modules.video

        if not ok:
            message = "Start ComfyUI on port 8188"
            healthy = False
        else:
            message = "ComfyUI ready for multi-backend video"
            healthy = True
            if not ffmpeg_ok and vid_cfg.require_ffmpeg:
                message += " (ffmpeg missing — webm may still work; mp4 stitch needs ffmpeg)"

        return {
            "enabled": True,
            "healthy": healthy,
            "message": message,
            "ffmpeg": ffmpeg_ok,
            "mode": vid_cfg.mode,
            "default_backend": vid_cfg.default_backend,
            "vram_gb": vid_cfg.vram_gb,
            "prefer_uncensored": vid_cfg.prefer_uncensored,
            "animatediff_plugin": ad,
            "backends": list_backends(),
        }

    def list_backends(self) -> list[dict[str, Any]]:
        return list_backends()

    def _require_ffmpeg(self) -> None:
        if self.settings.modules.video.require_ffmpeg and not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg is required for video generation (mp4 output). "
                "Install ffmpeg and ensure it is on PATH."
            )

    def _make_frames_dir(self) -> Path:
        frames_dir = self.temp_dir / f"frames_{uuid.uuid4().hex}"
        frames_dir.mkdir(parents=True, exist_ok=True)
        return frames_dir

    def _resolve_backend(self, backend: str | None, mode: str) -> str:
        vid = self.settings.modules.video
        bid = (backend or vid.default_backend or vid.mode or "auto").strip().lower()
        if bid in ("auto", "", "default"):
            return auto_backend(
                vid.vram_gb,
                want_uncensored=bool(getattr(vid, "prefer_uncensored", True)),
                mode=mode,
            )
        if bid == "animatediff":
            return "animatediff"
        try:
            get_backend(bid)
            return bid
        except KeyError as exc:
            raise RuntimeError(f"Unknown video backend: {bid}") from exc

    async def generate(
        self,
        prompt: str,
        *,
        frames: int | None = None,
        fps: int | None = None,
        width: int | None = None,
        height: int | None = None,
        backend: str | None = None,
        mode: str = "t2v",
        source_image: str | Path | None = None,
        negative: str | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        seed: int | None = None,
        lora: str | None = None,
        lora_strength: float | None = None,
        enhance_prompt: bool | None = None,
        from_image_url: str | None = None,
    ) -> dict[str, Any]:
        if not self.settings.modules.video.enabled:
            raise RuntimeError("Video module disabled")

        vid_cfg = self.settings.modules.video
        mode = mode if mode in ("t2v", "i2v") else "t2v"
        if source_image or from_image_url:
            mode = "i2v"

        backend_id = self._resolve_backend(backend, mode)

        if self.progress:
            self.progress.start("video", 1, f"Backend={backend_id} mode={mode}…")

        do_enhance = (
            enhance_prompt
            if enhance_prompt is not None
            else vid_cfg.auto_motion_prompt
        )
        if do_enhance:
            if self.progress:
                self.progress.set_frame(0, "Enhancing motion prompt (LLM)…")
            enhanced = await self.prompt_enhancer.for_video(prompt)
        else:
            enhanced = prompt

        # Image path from existing MonsterAI generation
        image_path: Path | None = None
        if source_image:
            image_path = Path(source_image)
            if not image_path.is_file():
                # try relative to image outputs
                alt = Path(self.settings.modules.image.output_dir) / Path(source_image).name
                if alt.is_file():
                    image_path = alt
                else:
                    raise FileNotFoundError(f"source_image not found: {source_image}")
        elif from_image_url:
            # /api/generate/files/images/<name>
            name = Path(from_image_url).name
            candidate = Path(self.settings.modules.image.output_dir) / name
            if candidate.is_file():
                image_path = candidate
            else:
                raise FileNotFoundError(f"from_image_url not resolved: {from_image_url}")

        try:
            if backend_id == "animatediff":
                return await self._generate_animatediff(
                    enhanced,
                    frames=frames,
                    fps=fps,
                    width=width,
                    height=height,
                )
            return await self._generate_native(
                enhanced,
                backend_id=backend_id,
                mode=mode,
                image_path=image_path,
                negative=negative,
                frames=frames,
                fps=fps,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg,
                seed=seed,
                lora=lora,
                lora_strength=lora_strength,
            )
        finally:
            if self.progress:
                self.progress.clear()

    async def _generate_native(
        self,
        enhanced: str,
        *,
        backend_id: str,
        mode: str,
        image_path: Path | None,
        negative: str | None,
        frames: int | None,
        fps: int | None,
        width: int | None,
        height: int | None,
        steps: int | None,
        cfg: float | None,
        seed: int | None,
        lora: str | None,
        lora_strength: float | None,
    ) -> dict[str, Any]:
        vid_cfg = self.settings.modules.video
        await self.client.require_online()
        profile = pick_profile(backend_id, vid_cfg.vram_gb)

        image_name: str | None = None
        if mode == "i2v":
            if image_path is None:
                raise ValueError("i2v requires source_image or from_image_url")
            if self.progress:
                self.progress.set_frame(0, "Uploading image to ComfyUI…")
            image_name = await upload_image_to_comfy(self.client.base, image_path)

        use_lora = lora or (vid_cfg.default_nsfw_lora or None)
        use_strength = (
            lora_strength
            if lora_strength is not None
            else vid_cfg.default_nsfw_lora_strength
        )

        try:
            workflow, meta = build_video_workflow(
                backend_id,
                mode=mode,
                positive=enhanced,
                negative=negative,
                vram_gb=vid_cfg.vram_gb,
                width=width,
                height=height,
                frames=frames,
                steps=steps,
                cfg=cfg,
                seed=seed,
                image_name=image_name,
                lora_name=use_lora if use_lora else None,
                lora_strength=use_strength,
            )
        except RuntimeError as exc:
            # Sulphur / Hunyuan full graphs not yet API-ready
            logger.warning("Native API workflow unavailable: %s", exc)
            raise

        if self.progress:
            self.progress.set_frame(
                0,
                f"ComfyUI {backend_id} {meta['width']}x{meta['height']} "
                f"×{meta['frames']}f steps={meta['steps']}…",
            )

        max_wait = int(getattr(vid_cfg, "max_wait_seconds", 900) or 900)

        async def _run() -> Path:
            async with self.vram_guard.acquire("video"):
                prompt_id = await self.client.queue_prompt(workflow)
                media = await self.client.wait_for_media(prompt_id, max_wait=max_wait)
                # Prefer video/gif over still frames
                media_sorted = sorted(
                    media,
                    key=lambda m: {"videos": 0, "gifs": 1, "images": 2}.get(
                        m.get("_kind", "images"), 9
                    ),
                )
                first = media_sorted[0]
                fname = first.get("filename", "out.webm")
                suffix = Path(fname).suffix.lower() or ".webm"
                raw_out = self.temp_dir / f"{uuid.uuid4().hex}{suffix}"
                await self.client.download_media(first, raw_out)

                if suffix == ".mp4":
                    final = self.output_dir / f"{uuid.uuid4().hex}.mp4"
                    shutil.move(str(raw_out), str(final))
                    return final

                # Convert webm/webp/png-sequence-like to mp4 when ffmpeg available
                if shutil.which("ffmpeg") and suffix in (".webm", ".webp", ".gif", ".png"):
                    if self.progress:
                        self.progress.set_frame(1, "Transcoding to .mp4…")
                    return self._transcode_to_mp4(raw_out, fps or profile.fps)

                # Keep webm if no ffmpeg
                final = self.output_dir / f"{uuid.uuid4().hex}{suffix}"
                shutil.move(str(raw_out), str(final))
                return final

        path = await self.gen_repair.run(
            "video",
            _run,
            validate=lambda p: p.exists() and p.stat().st_size > 1000,
        )
        result = self._result(
            path,
            enhanced,
            meta["frames"],
            fps or profile.fps,
            meta["width"],
            meta["height"],
            backend_id,
            extra={
                "mode": mode,
                "steps": meta["steps"],
                "cfg": meta["cfg"],
                "sampler": meta["sampler"],
                "workflow": meta.get("workflow"),
                "uncensored": meta.get("uncensored"),
                "source_image": str(image_path) if image_path else None,
                "lora": use_lora,
            },
        )
        return result

    def _transcode_to_mp4(self, src: Path, fps: int) -> Path:
        out = self.output_dir / f"{uuid.uuid4().hex}.mp4"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    "-r",
                    str(fps),
                    str(out),
                ],
                check=True,
                capture_output=True,
            )
        finally:
            src.unlink(missing_ok=True)
        return out

    async def _generate_animatediff(
        self,
        enhanced: str,
        *,
        frames: int | None,
        fps: int | None,
        width: int | None,
        height: int | None,
    ) -> dict[str, Any]:
        self._require_ffmpeg()
        vid_cfg = self.settings.modules.video
        frame_count = min(frames or 16, vid_cfg.max_frames)
        frame_fps = fps or 8
        vid_w = width or 512
        vid_h = height or 512

        await self.client.require_online()
        try:
            return await self._generate_batch(
                enhanced, frame_count, frame_fps, vid_w, vid_h
            )
        except Exception as exc:
            logger.warning("Batch video failed, falling back to frames: %s", exc)
            return await self._generate_frames(
                enhanced,
                frame_count,
                frame_fps,
                vid_w,
                vid_h,
                mode_used="frames_fallback",
            )

    async def _generate_batch(
        self,
        enhanced: str,
        frame_count: int,
        frame_fps: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        img_cfg = self.settings.modules.image
        checkpoint, _ = await self.client.resolve_checkpoint_name(img_cfg.checkpoint)

        if self.progress:
            self.progress.set_frame(
                1, f"Batch render {frame_count} frames (wait 30s–3min)…"
            )

        async def _run() -> Path:
            frames_dir = self._make_frames_dir()
            try:
                async with self.vram_guard.acquire("video"):
                    workflow = build_animatediff_workflow(
                        positive=enhanced,
                        negative=build_negative(),
                        checkpoint=checkpoint,
                        frames=frame_count,
                        width=width,
                        height=height,
                        steps=self.settings.modules.video.steps,
                        cfg=getattr(img_cfg, "cfg", 7.0),
                    )
                    prompt_id = await self.client.queue_prompt(workflow)
                    images = await self.client.wait_for_images(prompt_id, max_wait=300)
                    for i, img_info in enumerate(images[:frame_count]):
                        dest = frames_dir / f"frame_{i:04d}.png"
                        await self.client.download_image(img_info, dest)
                    if self.progress:
                        self.progress.set_frame(
                            frame_count, "Stitching frames to .mp4 (ffmpeg)…"
                        )
                    return self._stitch_frames(frames_dir, frame_fps)
            finally:
                shutil.rmtree(frames_dir, ignore_errors=True)

        path = await self.gen_repair.run(
            "video",
            _run,
            validate=lambda p: validate_video_file(p) and p.suffix == ".mp4",
        )
        if self.progress:
            self.progress.set_frame(frame_count, "Video ready")
        return self._result(
            path, enhanced, frame_count, frame_fps, width, height, "animatediff"
        )

    async def _generate_frames(
        self,
        enhanced: str,
        frame_count: int,
        frame_fps: int,
        width: int,
        height: int,
        *,
        mode_used: str,
    ) -> dict[str, Any]:
        img_cfg = self.settings.modules.image
        checkpoint, _ = await self.client.resolve_checkpoint_name(img_cfg.checkpoint)
        neg = build_negative()

        async def _run() -> Path:
            frames_dir = self._make_frames_dir()
            try:
                async with self.vram_guard.acquire("video"):
                    for i in range(frame_count):
                        if self.progress:
                            self.progress.set_frame(
                                i + 1, f"Rendering frame {i + 1}/{frame_count}"
                            )
                        motion = f"{enhanced}, frame {i + 1} of {frame_count}"
                        frame_path = await self.image_service._render_once(
                            positive=motion,
                            negative=neg,
                            checkpoint=checkpoint,
                            width=width,
                            height=height,
                            steps=img_cfg.steps,
                            cfg=img_cfg.cfg,
                            lora_name=None,
                            lora_strength=img_cfg.lora_strength,
                        )
                        dest = frames_dir / f"frame_{i:04d}.png"
                        shutil.copy(frame_path, dest)
                        frame_path.unlink(missing_ok=True)
                    if self.progress:
                        self.progress.set_frame(
                            frame_count, "Stitching frames to .mp4 (ffmpeg)…"
                        )
                    return self._stitch_frames(frames_dir, frame_fps)
            finally:
                shutil.rmtree(frames_dir, ignore_errors=True)

        path = await self.gen_repair.run(
            "video",
            _run,
            validate=lambda p: validate_video_file(p) and p.suffix == ".mp4",
        )
        if self.progress:
            self.progress.set_frame(frame_count, "Video ready")
        return self._result(
            path, enhanced, frame_count, frame_fps, width, height, mode_used
        )

    def _stitch_frames(self, frames_dir: Path, frame_fps: int) -> Path:
        self._require_ffmpeg()
        out = self.output_dir / f"{uuid.uuid4().hex}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(frame_fps),
                "-i",
                str(frames_dir / "frame_%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return out

    def _result(
        self,
        path: Path,
        enhanced: str,
        frame_count: int,
        frame_fps: int,
        width: int,
        height: int,
        mode: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": str(path),
            "url": f"/api/generate/files/videos/{path.name}",
            "prompt": enhanced,
            "type": "video",
            "format": path.suffix.lstrip(".") or "mp4",
            "frames": frame_count,
            "fps": frame_fps,
            "width": width,
            "height": height,
            "mode": mode,
            "backend": mode,
        }
        if extra:
            result.update(extra)
            if "mode" in extra:
                result["video_mode"] = extra["mode"]
        if self.history:
            self.history.record("video", result)
        return result
