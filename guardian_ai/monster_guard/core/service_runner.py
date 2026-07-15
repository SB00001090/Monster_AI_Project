"""24/7 service runner — starts monitor, handles crash/restart policy."""
from __future__ import annotations

import asyncio
import logging
import signal
from typing import TYPE_CHECKING, Any

from guardian_ai.monster_guard.core.self_repair import SelfRepair

if TYPE_CHECKING:
    from guardian_ai.monster_guard.service import MonsterGuardCore

logger = logging.getLogger(__name__)


class ServiceRunner:
    def __init__(self, core: MonsterGuardCore, *, self_repair: SelfRepair | None = None) -> None:
        self.core = core
        self.self_repair = self_repair or SelfRepair(
            auto_restart=bool(core.config.get("auto_restart", True)),
            max_restarts_per_hour=int(core.config.get("max_restarts_per_hour", 6)),
            backoff_seconds=float(core.config.get("restart_backoff_seconds", 5)),
        )
        self._stop = asyncio.Event()
        self._running = False

    async def run_forever(self) -> int:
        """Blocking async loop until SIGINT/SIGTERM or stop()."""
        self._install_signals()
        self._running = True
        logger.info("MonsterGuard service runner starting (always_on)")
        try:
            while not self._stop.is_set():
                try:
                    await self.core.start()
                    # Wait until stop requested; monitor runs inside core
                    while not self._stop.is_set():
                        st = self.core.health()
                        if not st.get("ok", True):
                            raise RuntimeError(st.get("error") or "health_failed")
                        await asyncio.sleep(2.0)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    self.self_repair.record_incident("crash", str(exc))
                    ok, reason = self.self_repair.can_restart()
                    if not ok:
                        logger.error("MonsterGuard giving up restart: %s", reason)
                        return 1
                    backoff = self.self_repair.next_backoff()
                    self.self_repair.mark_restart()
                    logger.warning("MonsterGuard restarting in %.1fs…", backoff)
                    try:
                        await self.core.stop()
                    except Exception:  # noqa: BLE001
                        pass
                    await asyncio.sleep(backoff)
        finally:
            self._running = False
            await self.core.stop()
            logger.info("MonsterGuard service runner stopped")
        return 0

    def request_stop(self) -> None:
        self._stop.set()

    def _install_signals(self) -> None:
        loop = asyncio.get_running_loop()

        def _handler(*_args: Any) -> None:
            logger.info("Stop signal received")
            self.request_stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _handler)
            except (NotImplementedError, RuntimeError):
                # Windows: signal handlers limited
                signal.signal(sig, lambda *_: _handler())

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "stop_requested": self._stop.is_set(),
            "self_repair": self.self_repair.status(),
            "core": self.core.status(),
        }
