"""Self-repair + restart policy for 24/7 MonsterGuard service."""
from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any, Deque

logger = logging.getLogger(__name__)


class SelfRepair:
    def __init__(
        self,
        *,
        auto_restart: bool = True,
        max_restarts_per_hour: int = 6,
        backoff_seconds: float = 5.0,
    ) -> None:
        self.auto_restart = auto_restart
        self.max_restarts_per_hour = max(1, int(max_restarts_per_hour))
        self.backoff_seconds = max(1.0, float(backoff_seconds))
        self._restart_times: Deque[float] = deque(maxlen=50)
        self._incidents: Deque[dict[str, Any]] = deque(maxlen=100)
        self.total_repairs = 0

    def record_incident(self, kind: str, message: str, **extra: Any) -> dict[str, Any]:
        entry = {
            "kind": kind,
            "message": message,
            "ts": time.time(),
            **extra,
        }
        self._incidents.appendleft(entry)
        logger.warning("MonsterGuard incident [%s]: %s", kind, message)
        return entry

    def can_restart(self) -> tuple[bool, str]:
        if not self.auto_restart:
            return False, "auto_restart_disabled"
        now = time.time()
        recent = [t for t in self._restart_times if now - t < 3600]
        if len(recent) >= self.max_restarts_per_hour:
            return False, "restart_budget_exhausted"
        return True, ""

    def mark_restart(self) -> None:
        self._restart_times.append(time.time())
        self.total_repairs += 1

    def next_backoff(self) -> float:
        # simple linear backoff by recent restarts
        n = len([t for t in self._restart_times if time.time() - t < 3600])
        return min(120.0, self.backoff_seconds * (1 + n))

    def status(self) -> dict[str, Any]:
        now = time.time()
        return {
            "auto_restart": self.auto_restart,
            "max_restarts_per_hour": self.max_restarts_per_hour,
            "restarts_last_hour": len([t for t in self._restart_times if now - t < 3600]),
            "total_repairs": self.total_repairs,
            "recent_incidents": list(self._incidents)[:10],
            "next_backoff_seconds": self.next_backoff(),
        }
