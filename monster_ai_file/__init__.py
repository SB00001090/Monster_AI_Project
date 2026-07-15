"""Conceptual alias package: monster_ai_file → monster_ai.

Use for documentation-aligned imports. Prefer `import monster_ai` in production code.
"""
from __future__ import annotations

import monster_ai as _monster_ai
from monster_ai import *  # noqa: F403

__all__ = list(getattr(_monster_ai, "__all__", []))
__doc__ = (_monster_ai.__doc__ or "") + "\n\nAlias of monster_ai (concept: monster_ai_file)."
