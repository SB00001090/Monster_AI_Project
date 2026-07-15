"""MonsterGuard 24/7 core engines."""
from __future__ import annotations

from guardian_ai.monster_guard.core.discord_scam_detector import DiscordScamDetector
from guardian_ai.monster_guard.core.url_reputation import UrlReputation
from guardian_ai.monster_guard.core.real_time_monitor import RealTimeMonitor
from guardian_ai.monster_guard.core.auto_blocker import AutoBlocker
from guardian_ai.monster_guard.core.service_runner import ServiceRunner
from guardian_ai.monster_guard.core.self_repair import SelfRepair

__all__ = [
    "DiscordScamDetector",
    "UrlReputation",
    "RealTimeMonitor",
    "AutoBlocker",
    "ServiceRunner",
    "SelfRepair",
]
