"""Real-time monitor loop — heartbeat, health checks, event bus."""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Awaitable, Callable, Deque

logger = logging.getLogger(__name__)

HealthFn = Callable[[], Awaitable[dict[str, Any]] | dict[str, Any]]


class RealTimeMonitor:
    def __init__(
        self,
        *,
        interval_seconds: float = 15.0,
        enabled: bool = True,
        health_fn: HealthFn | None = None,
    ) -> None:
        self.interval = max(3.0, float(interval_seconds))
        self.enabled = enabled
        self.health_fn = health_fn
        self._task: asyncio.Task | None = None
        self._events: Deque[dict[str, Any]] = deque(maxlen=300)
        self._ticks = 0
        self._started_at: float | None = None
        self._last_tick: float | None = None
        self._last_health: dict[str, Any] = {}

    def record(self, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("ts", time.time())
        self._events.appendleft(payload)

    def recent(self, limit: int = 30) -> list[dict[str, Any]]:
        return list(self._events)[: max(1, limit)]

    async def start(self) -> None:
        if not self.enabled or self._task is not None:
            return
        self._started_at = time.time()
        self._task = asyncio.create_task(self._loop(), name="monster-guard-monitor")
        logger.info("MonsterGuard real-time monitor started (interval=%ss)", self.interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("MonsterGuard real-time monitor stopped")

    async def _loop(self) -> None:
        while True:
            try:
                self._ticks += 1
                self._last_tick = time.time()
                if self.health_fn is not None:
                    res = self.health_fn()
                    if asyncio.iscoroutine(res):
                        res = await res
                    self._last_health = dict(res or {})
                    if self._ticks % 4 == 0:
                        self.record({"type": "health", "data": self._last_health})
                if self._ticks % 10 == 0:
                    self.record({"type": "heartbeat", "ticks": self._ticks})
            except Exception:  # noqa: BLE001
                logger.exception("monitor tick failed")
                self.record({"type": "error", "message": "monitor_tick_failed"})
            await asyncio.sleep(self.interval)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "running": self._task is not None and not self._task.done(),
            "ticks": self._ticks,
            "interval_seconds": self.interval,
            "started_at": self._started_at,
            "last_tick": self._last_tick,
            "last_health": self._last_health,
            "events": len(self._events),
        }
