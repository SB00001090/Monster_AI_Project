"""
加速開發包 API — 情緒 / 自癒 / 即時回報 / 自動更新
開發者：suckbob | 發行商：Monster_Ai_hk
"""
from __future__ import annotations

import base64
import json
import platform
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/accel", tags=["accel"])


class EmotionRequest(BaseModel):
    text: str
    save: bool = True


class FeedbackRequest(BaseModel):
    title: str = ""
    message: str
    screenshot_base64: str | None = None
    emotion_summary: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class UpdateCheckResponse(BaseModel):
    ok: bool
    update_available: bool = False
    current_version: str = ""
    latest_version: str = ""
    html_url: str = ""
    body: str = ""
    message: str = ""


@router.get("/status")
async def accel_status(request: Request) -> dict:
    settings = request.app.state.settings
    emotion = getattr(request.app.state, "emotion_analyzer", None)
    healing = getattr(request.app.state, "conversation_healing", None)
    return {
        "unlimited_mode": getattr(settings, "unlimited_mode", True),
        "uncensored": getattr(settings, "uncensored", True),
        "self_learning_analysis": getattr(settings, "self_learning_analysis", None)
        and settings.self_learning_analysis.model_dump()
        if hasattr(settings, "self_learning_analysis")
        else {},
        "self_healing": healing.status() if healing else {"enabled": False},
        "feedback": settings.feedback.model_dump() if hasattr(settings, "feedback") else {},
        "auto_update": settings.auto_update.model_dump() if hasattr(settings, "auto_update") else {},
        "ui_themes": settings.ui_themes.model_dump() if hasattr(settings, "ui_themes") else {},
        "gestures": settings.gestures.model_dump() if hasattr(settings, "gestures") else {},
        "emotion_ready": emotion is not None,
        "developer": "suckbob",
        "publisher": "Monster_Ai_hk",
        "version": getattr(request.app.state, "version", "1.0.0"),
    }


@router.post("/emotion/analyze")
async def analyze_emotion(body: EmotionRequest, request: Request) -> dict:
    analyzer = getattr(request.app.state, "emotion_analyzer", None)
    if analyzer is None:
        from monster_ai.learning.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
    # 暫時覆寫是否寫入
    prev = analyzer.save_to_training
    if not body.save:
        analyzer.save_to_training = False
    try:
        result = analyzer.analyze(body.text)
    finally:
        analyzer.save_to_training = prev
    return {"ok": True, **result.to_dict()}


@router.get("/emotion/recent")
async def emotion_recent(request: Request, limit: int = 20) -> dict:
    analyzer = getattr(request.app.state, "emotion_analyzer", None)
    if analyzer is None:
        return {"ok": True, "items": []}
    return {"ok": True, "items": analyzer.recent(limit=min(limit, 100))}


@router.get("/healing/status")
async def healing_status(request: Request) -> dict:
    healing = getattr(request.app.state, "conversation_healing", None)
    if not healing:
        return {"ok": False, "enabled": False}
    return {"ok": True, **healing.status(), "recent": healing.recent_events(30)}


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest, request: Request) -> dict:
    settings = request.app.state.settings
    fb = getattr(settings, "feedback", None)
    if fb is not None and not fb.enabled:
        return {"ok": False, "message": "feedback disabled"}

    healing = getattr(request.app.state, "conversation_healing", None)
    emotion = getattr(request.app.state, "emotion_analyzer", None)
    version = getattr(request.app.state, "version", "1.0.0")

    payload = {
        "title": body.title or "Monster AI 即時回報",
        "message": body.message,
        "emotion_summary": body.emotion_summary,
        "device": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "version": version,
        "healing_recent": healing.recent_events(10) if healing else [],
        "emotion_recent": emotion.recent(5) if emotion else [],
        "extra": body.extra,
        "ts": time.time(),
        "developer": "suckbob",
        "publisher": "Monster_Ai_hk",
        "has_screenshot": bool(body.screenshot_base64),
    }

    # 本地落盤
    log_dir = Path("./data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "instant_feedback.jsonl").open("a", encoding="utf-8") as f:
        row = dict(payload)
        if body.screenshot_base64:
            # 不把完整 base64 塞爆 jsonl，只記長度
            row["screenshot_len"] = len(body.screenshot_base64)
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if body.screenshot_base64:
        try:
            raw = body.screenshot_base64.split(",")[-1]
            img = base64.b64decode(raw)
            shot_dir = log_dir / "feedback_shots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            (shot_dir / f"shot_{int(time.time())}.png").write_bytes(img)
        except Exception:  # noqa: BLE001
            pass

    webhook = (fb.webhook_url if fb else "") or ""
    webhook_ok = False
    if webhook:
        try:
            content = (
                f"**{payload['title']}**\n"
                f"{body.message[:1800]}\n"
                f"ver={version} · emotion={body.emotion_summary or '-'}"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(webhook, json={"content": content[:2000]})
                webhook_ok = r.status_code < 300
        except Exception as exc:  # noqa: BLE001
            return {"ok": True, "saved": True, "webhook_ok": False, "webhook_error": str(exc)}

    return {"ok": True, "saved": True, "webhook_ok": webhook_ok}


@router.get("/update/check", response_model=UpdateCheckResponse)
async def check_update(request: Request) -> UpdateCheckResponse:
    settings = request.app.state.settings
    au = getattr(settings, "auto_update", None)
    current = getattr(request.app.state, "version", "1.0.0")
    if au is not None and not au.enabled:
        return UpdateCheckResponse(
            ok=True,
            update_available=False,
            current_version=current,
            message="auto_update disabled",
        )
    repo = (au.repo if au else "SB00001090/Monster_AI_Project") or "SB00001090/Monster_AI_Project"
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "MonsterAI-Accel/1.0 (Monster_Ai_hk; suckbob)",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        ) as client:
            r = await client.get(url)
            if r.status_code == 404:
                return UpdateCheckResponse(
                    ok=True,
                    update_available=False,
                    current_version=current,
                    message="no releases yet",
                    html_url=f"https://github.com/{repo}/releases",
                )
            r.raise_for_status()
            data = r.json()
            latest = (data.get("tag_name") or data.get("name") or "").lstrip("v")
            html = data.get("html_url") or f"https://github.com/{repo}/releases/latest"
            body = (data.get("body") or "")[:2000]
            available = bool(latest) and latest != current and latest not in (f"v{current}",)
            return UpdateCheckResponse(
                ok=True,
                update_available=available,
                current_version=current,
                latest_version=latest,
                html_url=html,
                body=body,
                message="ok",
            )
    except Exception as exc:  # noqa: BLE001
        return UpdateCheckResponse(
            ok=False,
            current_version=current,
            message=str(exc),
            html_url=f"https://github.com/{repo}/releases",
        )
