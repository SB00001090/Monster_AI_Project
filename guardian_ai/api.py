"""Shim re-export of monsterguard API routers."""
from __future__ import annotations

from monsterguard.api import create_compat_router, create_router

__all__ = ["create_router", "create_compat_router"]
