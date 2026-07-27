"""Build / patch ComfyUI API workflows for MonsterAI video backends."""
from __future__ import annotations

import copy
import json
import random
import shutil
from pathlib import Path
from typing import Any

from monster_ai.modules.video.presets import VideoBackend, get_backend, pick_profile


def workflows_dir() -> Path:
    return Path(__file__).resolve().parent / "workflows"


def load_api_workflow(filename: str) -> dict[str, Any]:
    path = workflows_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(f"Workflow not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "_meta" in data and len(data) == 1:
        raise RuntimeError(
            f"{filename} is meta-only. Use ComfyUI UI template + model swap "
            f"(see docs/LOCAL_UNRESTRICTED_VIDEO_MODULE.md)."
        )
    return data


def _set_text(node: dict[str, Any], text: str) -> None:
    if "inputs" in node and "text" in node["inputs"]:
        node["inputs"]["text"] = text


def _set_seed(node: dict[str, Any], seed: int | None = None) -> None:
    inputs = node.get("inputs", {})
    s = seed if seed is not None else random.randint(0, 2**32 - 1)
    if "seed" in inputs:
        inputs["seed"] = s
    if "noise_seed" in inputs:
        inputs["noise_seed"] = s


def patch_wan_workflow(
    workflow: dict[str, Any],
    *,
    positive: str,
    negative: str | None,
    width: int,
    height: int,
    length: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    seed: int | None = None,
    image_name: str | None = None,
    unet_name: str | None = None,
    unet_high: str | None = None,
    unet_low: str | None = None,
    lora_name: str | None = None,
    lora_strength: float = 0.8,
) -> dict[str, Any]:
    """Patch Wan 2.2 API graph (5B or 14B)."""
    wf = copy.deepcopy(workflow)
    neg = negative or (
        "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，"
        "最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，"
        "画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，"
        "三条腿，背景人很多，倒着走"
    )

    for node_id, node in wf.items():
        if not isinstance(node, dict):
            continue
        ct = node.get("class_type")
        inputs = node.setdefault("inputs", {})

        if ct == "CLIPTextEncode":
            # Heuristic: first encode with non-neg-looking text is positive;
            # we set by content: empty / POSITIVE_PROMPT / known placeholder
            cur = str(inputs.get("text", ""))
            if cur in ("POSITIVE_PROMPT",) or (
                cur
                and not cur.startswith("色调")
                and "低质量" not in cur
                and cur != neg
            ):
                # Only rewrite the positive slot once — track via marker
                if "POSITIVE" in cur or cur == "POSITIVE_PROMPT" or node_id == "6":
                    _set_text(node, positive)
                elif node_id == "7":
                    _set_text(node, neg)
            if node_id == "6":
                _set_text(node, positive)
            if node_id == "7":
                _set_text(node, neg)

        if ct == "KSampler":
            inputs["steps"] = steps
            inputs["cfg"] = cfg
            inputs["sampler_name"] = sampler
            inputs["scheduler"] = scheduler
            _set_seed(node, seed)

        if ct == "KSamplerAdvanced":
            inputs["steps"] = steps
            inputs["cfg"] = cfg
            inputs["sampler_name"] = sampler
            inputs["scheduler"] = scheduler
            if inputs.get("add_noise") == "enable":
                _set_seed(node, seed)

        if ct in ("Wan22ImageToVideoLatent", "EmptyHunyuanLatentVideo", "WanImageToVideo"):
            if "width" in inputs:
                inputs["width"] = width
            if "height" in inputs:
                inputs["height"] = height
            if "length" in inputs:
                inputs["length"] = length

        if ct == "LoadImage" and image_name:
            inputs["image"] = image_name

        if ct == "UNETLoader":
            uname = str(inputs.get("unet_name", ""))
            if unet_name and ("5B" in uname or "ti2v" in uname.lower()):
                inputs["unet_name"] = unet_name
            if unet_high and "high" in uname.lower():
                inputs["unet_name"] = unet_high
            if unet_low and "low" in uname.lower():
                inputs["unet_name"] = unet_low

        if ct == "LoraLoaderModelOnly" and lora_name:
            inputs["lora_name"] = lora_name
            inputs["strength_model"] = lora_strength

        if ct == "SaveWEBM":
            inputs.setdefault("filename_prefix", "MonsterAI_Video")

    return wf


def build_video_workflow(
    backend_id: str,
    *,
    mode: str = "t2v",
    positive: str,
    negative: str | None = None,
    vram_gb: int = 12,
    width: int | None = None,
    height: int | None = None,
    frames: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    seed: int | None = None,
    image_name: str | None = None,
    unet_override: str | None = None,
    unet_high: str | None = None,
    unet_low: str | None = None,
    lora_name: str | None = None,
    lora_strength: float = 0.8,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Returns (api_workflow, meta).
    Raises RuntimeError for backends that require UI template (Sulphur/Hunyuan full graph).
    """
    backend: VideoBackend = get_backend(backend_id)
    if mode not in backend.modes:
        raise ValueError(f"Backend {backend_id} does not support mode={mode}")

    profile = pick_profile(backend_id, vram_gb)
    w = width or profile.width
    h = height or profile.height
    length = frames or profile.frames
    use_steps = steps if steps is not None else profile.steps
    use_cfg = cfg if cfg is not None else profile.cfg

    # Ensure Wan-friendly frame length (4n+1)
    if backend_id.startswith("wan") and length % 4 != 1:
        length = max(5, (length // 4) * 4 + 1)

    meta = {
        "backend": backend_id,
        "mode": mode,
        "width": w,
        "height": h,
        "frames": length,
        "steps": use_steps,
        "cfg": use_cfg,
        "sampler": profile.sampler,
        "scheduler": profile.scheduler,
        "fps": profile.fps,
        "vram_profile_gb": profile.vram_gb,
        "uncensored": backend.uncensored,
    }

    if backend_id == "sulphur2":
        raise RuntimeError(
            "Sulphur 2 uses LTX-2.3 multi-stage UI template. "
            "Open ComfyUI → Templates → Video → LTX-2.3 T2V/I2V, "
            "set checkpoint to sulphur_dev_fp8mixed.safetensors, "
            "or POST /api/generate/video with backend=wan22_5b / wan22_remix for API path. "
            "See docs/LOCAL_UNRESTRICTED_VIDEO_MODULE.md §3."
        )

    if backend_id == "hunyuan15":
        raise RuntimeError(
            "HunyuanVideo 1.5: use ComfyUI Template Library (HunyuanVideo 1.5) "
            "with models from Comfy-Org/HunyuanVideo_1.5_repackaged. "
            "API path coming after template export."
        )

    if backend_id == "animatediff":
        from monster_ai.modules.video.comfyui_video import build_animatediff_workflow

        wf = build_animatediff_workflow(
            positive=positive,
            negative=negative or "low quality, blurry, static",
            checkpoint=unet_override or "model.safetensors",
            frames=length,
            width=w,
            height=h,
            steps=use_steps,
            cfg=use_cfg,
        )
        return wf, meta

    wf_name = backend.workflow_i2v if mode == "i2v" else backend.workflow_t2v
    if not wf_name or not wf_name.startswith("api_"):
        raise RuntimeError(f"No API workflow for {backend_id} mode={mode}")

    if mode == "i2v" and not image_name:
        raise ValueError("image_name required for i2v mode")

    raw = load_api_workflow(wf_name)
    wf = patch_wan_workflow(
        raw,
        positive=positive,
        negative=negative,
        width=w,
        height=h,
        length=length,
        steps=use_steps,
        cfg=use_cfg,
        sampler=profile.sampler,
        scheduler=profile.scheduler,
        seed=seed,
        image_name=image_name,
        unet_name=unet_override,
        unet_high=unet_high or backend.model_files.get("unet_high"),
        unet_low=unet_low or backend.model_files.get("unet_low"),
        lora_name=lora_name,
        lora_strength=lora_strength,
    )
    meta["workflow"] = wf_name
    return wf, meta


async def upload_image_to_comfy(comfy_url: str, image_path: Path) -> str:
    """Upload local image to ComfyUI input folder; returns filename for LoadImage."""
    import httpx

    data = image_path.read_bytes()
    files = {"image": (image_path.name, data, "image/png")}
    form = {"overwrite": "true"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{comfy_url.rstrip('/')}/upload/image", files=files, data=form)
        r.raise_for_status()
        body = r.json()
        # {"name": "...", "subfolder": "", "type": "input"}
        name = body.get("name") or image_path.name
        sub = body.get("subfolder") or ""
        return f"{sub}/{name}".lstrip("/") if sub else name


def copy_image_to_comfy_input(image_path: Path, comfy_input_dir: Path) -> str:
    """Filesystem fallback when upload API unavailable."""
    comfy_input_dir.mkdir(parents=True, exist_ok=True)
    dest = comfy_input_dir / image_path.name
    shutil.copy2(image_path, dest)
    return dest.name
