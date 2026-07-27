"""Video backend presets for MonsterAI unrestricted local video module.

Backends:
  - sulphur2: NSFW-first LTX-2.3 finetune (T2V/I2V)
  - wan22_5b: Wan 2.2 TI2V hybrid (8–12GB friendly)
  - wan22_remix: Wan 2.2 Remix / Spicy community uncensored (I2V/T2V)
  - wan22_14b: Wan 2.2 14B dual-expert quality (16–24GB)
  - hunyuan15: HunyuanVideo 1.5 (quality / consistency)
  - animatediff: legacy SD1.5 AnimateDiff fallback
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

VideoBackendId = Literal[
    "sulphur2",
    "wan22_5b",
    "wan22_remix",
    "wan22_14b",
    "hunyuan15",
    "animatediff",
]

VideoMode = Literal["t2v", "i2v"]


@dataclass(frozen=True)
class VramProfile:
    vram_gb: int
    width: int
    height: int
    frames: int  # latent length (Wan/LTX: often 4n+1)
    steps: int
    cfg: float
    sampler: str
    scheduler: str
    fps: int
    notes: str = ""


@dataclass(frozen=True)
class VideoBackend:
    id: str
    label: str
    modes: tuple[str, ...]
    workflow_t2v: str | None
    workflow_i2v: str | None
    uncensored: bool
    min_vram_gb: int
    priority: int  # lower = preferred when auto
    description: str
    model_files: dict[str, str] = field(default_factory=dict)
    profiles: dict[int, VramProfile] = field(default_factory=dict)


# Frame lengths must often be 4n+1 for Wan/LTX families.
def _p(
    vram: int,
    w: int,
    h: int,
    frames: int,
    steps: int,
    cfg: float,
    sampler: str = "uni_pc",
    scheduler: str = "simple",
    fps: int = 16,
    notes: str = "",
) -> VramProfile:
    return VramProfile(vram, w, h, frames, steps, cfg, sampler, scheduler, fps, notes)


BACKENDS: dict[str, VideoBackend] = {
    "sulphur2": VideoBackend(
        id="sulphur2",
        label="Sulphur 2 (NSFW / LTX-2.3)",
        modes=("t2v", "i2v"),
        workflow_t2v="official/ltx23_t2v.json",
        workflow_i2v="official/ltx23_i2v.json",
        uncensored=True,
        min_vram_gb=8,
        priority=1,
        description="主推無審查影片。以 LTX-2.3 原生 workflow 載入 sulphur_dev_fp8mixed。",
        model_files={
            "checkpoint": "sulphur_dev_fp8mixed.safetensors",
            "text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors",
            "spatial_upscaler": "ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
            "distill_lora": "ltx-2.3-22b-distilled-lora-1.1_fro90_ceil72_condsafe.safetensors",
            "gemma_abliterated_lora": "gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors",
        },
        profiles={
            8: _p(8, 512, 320, 25, 12, 3.5, "euler", "simple", 24, "GGUF Q4 或 fp8 + offload"),
            12: _p(12, 640, 384, 33, 16, 3.5, "euler", "simple", 24),
            16: _p(16, 768, 432, 49, 20, 4.0, "euler", "simple", 24),
            24: _p(24, 960, 544, 73, 24, 4.0, "euler", "simple", 24, "可開 spatial x2 二階段"),
        },
    ),
    "wan22_5b": VideoBackend(
        id="wan22_5b",
        label="Wan 2.2 TI2V 5B",
        modes=("t2v", "i2v"),
        workflow_t2v="api_wan22_5b_t2v.json",
        workflow_i2v="api_wan22_5b_i2v.json",
        uncensored=False,
        min_vram_gb=8,
        priority=2,
        description="官方 5B 混合模型，8GB 可跑，MonsterAI 圖像→影片入門首選。",
        model_files={
            "unet": "wan2.2_ti2v_5B_fp16.safetensors",
            "vae": "wan2.2_vae.safetensors",
            "text_encoder": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        },
        profiles={
            8: _p(8, 640, 368, 25, 16, 5.0, "uni_pc", "simple", 16),
            12: _p(12, 832, 480, 41, 20, 5.0, "uni_pc", "simple", 16),
            16: _p(16, 1024, 576, 49, 24, 5.0, "uni_pc", "simple", 16),
            24: _p(24, 1280, 704, 81, 30, 5.0, "uni_pc", "simple", 16),
        },
    ),
    "wan22_remix": VideoBackend(
        id="wan22_remix",
        label="Wan 2.2 Remix / Spicy",
        modes=("t2v", "i2v"),
        workflow_t2v="api_wan22_14b_t2v.json",
        workflow_i2v="api_wan22_14b_i2v.json",
        uncensored=True,
        min_vram_gb=12,
        priority=3,
        description="社群無審查 Remix 權重，角色一致性佳；可搭配 Lightning LoRA 加速。",
        model_files={
            "unet_high": "Wan2.2-Remix-I2V-high.safetensors",
            "unet_low": "Wan2.2-Remix-I2V-low.safetensors",
            "vae": "wan_2.1_vae.safetensors",
            "text_encoder": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        },
        profiles={
            8: _p(8, 480, 480, 17, 8, 1.0, "euler", "simple", 16, "GGUF Q4 + Lightx2v 4–8 steps"),
            12: _p(12, 576, 576, 33, 12, 2.0, "euler", "simple", 16, "fp8 + Lightning LoRA"),
            16: _p(16, 640, 640, 41, 16, 3.0, "euler", "simple", 16),
            24: _p(24, 768, 768, 57, 20, 3.5, "euler", "simple", 16, "角色一致性優先"),
        },
    ),
    "wan22_14b": VideoBackend(
        id="wan22_14b",
        label="Wan 2.2 14B Official",
        modes=("t2v", "i2v"),
        workflow_t2v="api_wan22_14b_t2v.json",
        workflow_i2v="api_wan22_14b_i2v.json",
        uncensored=False,
        min_vram_gb=16,
        priority=4,
        description="官方 14B 雙專家高品質。",
        model_files={
            "unet_high_t2v": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
            "unet_low_t2v": "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
            "unet_high_i2v": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            "unet_low_i2v": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
            "vae": "wan_2.1_vae.safetensors",
            "text_encoder": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        },
        profiles={
            8: _p(8, 480, 320, 17, 8, 3.0, "euler", "simple", 16, "GGUF only"),
            12: _p(12, 640, 368, 25, 12, 3.5, "euler", "simple", 16, "fp8 + block swap"),
            16: _p(16, 768, 432, 41, 16, 3.5, "euler", "simple", 16),
            24: _p(24, 960, 544, 57, 20, 3.5, "euler", "simple", 16),
        },
    ),
    "hunyuan15": VideoBackend(
        id="hunyuan15",
        label="HunyuanVideo 1.5",
        modes=("t2v", "i2v"),
        workflow_t2v=None,  # ComfyUI template
        workflow_i2v=None,
        uncensored=False,
        min_vram_gb=12,
        priority=5,
        description="騰訊 8.3B 輕量高畫質；用 Comfy-Org repackaged + 模板。",
        model_files={
            "repo": "Comfy-Org/HunyuanVideo_1.5_repackaged",
        },
        profiles={
            8: _p(8, 480, 480, 25, 16, 6.0, "euler", "simple", 16, "重度 offload"),
            12: _p(12, 640, 640, 33, 20, 6.0, "euler", "simple", 16),
            16: _p(16, 720, 720, 49, 20, 6.0, "euler", "simple", 24),
            24: _p(24, 960, 540, 65, 24, 6.0, "euler", "simple", 24),
        },
    ),
    "animatediff": VideoBackend(
        id="animatediff",
        label="AnimateDiff (legacy SD1.5)",
        modes=("t2v",),
        workflow_t2v="animatediff_sd15_lowvram.json",
        workflow_i2v=None,
        uncensored=True,
        min_vram_gb=6,
        priority=99,
        description="舊版相容後備，品質與時序弱於 Wan/Sulphur。",
        profiles={
            8: _p(8, 512, 512, 16, 15, 7.0, "euler", "normal", 8),
            12: _p(12, 512, 768, 16, 18, 7.0, "euler", "normal", 8),
            16: _p(16, 768, 768, 24, 20, 7.0, "euler", "normal", 8),
            24: _p(24, 768, 1024, 32, 24, 7.0, "euler", "normal", 8),
        },
    ),
}


def list_backends() -> list[dict[str, Any]]:
    return [
        {
            "id": b.id,
            "label": b.label,
            "modes": list(b.modes),
            "uncensored": b.uncensored,
            "min_vram_gb": b.min_vram_gb,
            "priority": b.priority,
            "description": b.description,
            "profiles": {
                str(k): {
                    "width": p.width,
                    "height": p.height,
                    "frames": p.frames,
                    "steps": p.steps,
                    "cfg": p.cfg,
                    "sampler": p.sampler,
                    "scheduler": p.scheduler,
                    "fps": p.fps,
                    "notes": p.notes,
                }
                for k, p in b.profiles.items()
            },
        }
        for b in sorted(BACKENDS.values(), key=lambda x: x.priority)
    ]


def get_backend(backend_id: str) -> VideoBackend:
    if backend_id not in BACKENDS:
        raise KeyError(f"Unknown video backend: {backend_id}")
    return BACKENDS[backend_id]


def pick_profile(backend_id: str, vram_gb: int) -> VramProfile:
    b = get_backend(backend_id)
    # nearest lower-or-equal profile key
    keys = sorted(b.profiles.keys())
    chosen = keys[0]
    for k in keys:
        if vram_gb >= k:
            chosen = k
    return b.profiles[chosen]


# Backends with ready-to-queue API workflow JSON (not UI-template-only).
API_READY = frozenset({"wan22_5b", "wan22_remix", "wan22_14b", "animatediff"})


def auto_backend(
    vram_gb: int,
    *,
    want_uncensored: bool = True,
    mode: str = "t2v",
    api_only: bool = True,
) -> str:
    """Pick best backend for day-1 reliability.

    api_only=True skips sulphur2/hunyuan15 (UI templates) until full API export.
    Default path prefers Wan 2.2 5B (always API-ready). Uncensored Remix/AnimateDiff
    are available via explicit backend= selection.
    """
    del want_uncensored  # reserved for future file-presence-aware routing
    candidates = [
        b
        for b in BACKENDS.values()
        if mode in b.modes and vram_gb >= b.min_vram_gb
    ]
    if api_only:
        # Prefer production API graphs; exclude remix until user installs weights
        preferred = [b for b in candidates if b.id == "wan22_5b"]
        if preferred:
            return "wan22_5b"
        candidates = [b for b in candidates if b.id in API_READY and b.id != "wan22_remix"]
    if not candidates:
        if mode in BACKENDS["wan22_5b"].modes:
            return "wan22_5b"
        return "animatediff"
    return sorted(candidates, key=lambda b: b.priority)[0].id
