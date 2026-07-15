"""FastAPI router factory for MonsterGuard.

Primary prefix: /api/monsterguard
Compat alias:   /api/guardian-security  (same handlers)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


class UrlScanBody(BaseModel):
    urls: list[str] = Field(default_factory=list)


class TextScanBody(BaseModel):
    text: str = ""


class DownloadScanBody(BaseModel):
    path_or_url: str = ""


class DiscordScanBody(BaseModel):
    content: str = ""
    urls: list[str] = Field(default_factory=list)
    attachment_names: list[str] = Field(default_factory=list)


class QuarantineReleaseBody(BaseModel):
    entry_id: str


def _svc(request: Request) -> Any:
    svc = getattr(request.app.state, "monsterguard", None)
    if svc is None:
        # backward compat attribute name
        svc = getattr(request.app.state, "guardian_security", None)
    if svc is None:
        raise HTTPException(503, "MonsterGuard not initialized")
    return svc


def _build_routes(router: APIRouter) -> APIRouter:
    @router.get("/status")
    async def status(request: Request) -> dict:
        return _svc(request).status()

    @router.get("/dashboard")
    async def dashboard(request: Request) -> dict:
        return _svc(request).dashboard()

    @router.get("/report")
    async def report(request: Request) -> dict:
        return _svc(request).report()

    @router.post("/scan/url")
    async def scan_url(body: UrlScanBody, request: Request) -> dict:
        if not body.urls:
            raise HTTPException(400, "urls required")
        return _svc(request).scan_urls(body.urls)

    @router.post("/scan/text")
    async def scan_text(body: TextScanBody, request: Request) -> dict:
        return await _svc(request).scan_text_async(body.text or "")

    @router.post("/scan/download")
    async def scan_download(body: DownloadScanBody, request: Request) -> dict:
        if not body.path_or_url:
            raise HTTPException(400, "path_or_url required")
        return _svc(request).scan_download(body.path_or_url)

    @router.post("/scan/discord")
    async def scan_discord(body: DiscordScanBody, request: Request) -> dict:
        return _svc(request).scan_discord_message(
            body.content or "",
            urls=body.urls or None,
            attachment_names=body.attachment_names or None,
        )

    @router.get("/quarantine")
    async def quarantine_list(request: Request, limit: int = 20) -> dict:
        return _svc(request).list_quarantine(limit=limit)

    @router.post("/quarantine/release")
    async def quarantine_release(body: QuarantineReleaseBody, request: Request) -> dict:
        return _svc(request).release_quarantine(body.entry_id)

    return router


def create_router() -> APIRouter:
    """Primary router under /api/monsterguard."""
    return _build_routes(APIRouter(prefix="/api/monsterguard", tags=["monsterguard"]))


def create_compat_router() -> APIRouter:
    """Legacy alias /api/guardian-security."""
    return _build_routes(
        APIRouter(prefix="/api/guardian-security", tags=["monsterguard-compat"])
    )
