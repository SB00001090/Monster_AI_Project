"""Discord scam detector — wraps shared monsterguard engine + local patterns."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from monsterguard.core.discord_scam_detector import (
    DiscordScamDetector as _BaseDiscordScamDetector,
)


class DiscordScamDetector(_BaseDiscordScamDetector):
    """Prefer package-local scam_patterns.json when present."""

    def __init__(self, patterns_path: Path | None = None, **kwargs: Any) -> None:
        if patterns_path is None:
            local = (
                Path(__file__).resolve().parents[1] / "database" / "scam_patterns.json"
            )
            if local.is_file():
                patterns_path = local
        super().__init__(patterns_path=patterns_path, **kwargs)
