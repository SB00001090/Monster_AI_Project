"""Background real-time protection loop (event queue + heartbeat)."""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Deque

logger = logging.getLogger(__name__)


class RealTimeProtection:
    def __init__(self, *, enabled: bool = True, interval_seconds: float = 30.0) -> None:
        self.enabled = enabled
        self.interval = max(5.0, float(interval_seconds))
        self._task: asyncio.Task | None = None
        self._events: Deque[dict[str, Any]] = deque(maxlen=200)
        self._started_at: float | None = None
        self._ticks = 0
        self._last_tick: float | None = None

    def record_event(self, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", time.time())
        self._events.appendleft(payload)

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._events)[: max(1, limit)]

    async def start(self) -> None:
        if not self.enabled or self._task is not None:
            return
        self._started_at = time.time()
        self._task = asyncio.create_task(self._loop(), name="guardian-security-rtp")
        logger.info("MonsterGuard real-time protection started")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("MonsterGuard real-time protection stopped")

    async def _loop(self) -> None:
        while True:
            try:
                self._ticks += 1
                self._last_tick = time.time()
                # Heartbeat only — actual scans are on-demand / Discord pipeline
                if self._ticks % 10 == 0:
                    self.record_event({"type": "heartbeat", "ticks": self._ticks})
            except Exception:  # noqa: BLE001
                logger.exception("real-time protection tick failed")
            await asyncio.sleep(self.interval)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "running": self._task is not None and not self._task.done(),
            "ticks": self._ticks,
            "started_at": self._started_at,
            "last_tick": self._last_tick,
            "recent_events": len(self._events),
        }
