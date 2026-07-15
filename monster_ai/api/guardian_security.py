"""Mount MonsterGuard API (primary + legacy alias)."""
from __future__ import annotations

from fastapi import APIRouter

from monsterguard.api import create_compat_router, create_router

router = APIRouter()
router.include_router(create_router())
router.include_router(create_compat_router())
