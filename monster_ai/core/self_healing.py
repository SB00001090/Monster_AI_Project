"""
對話級自癒系統 — 防當機、防逾時、Fallback、會話保留
開發者：suckbob | 發行商：Monster_Ai_hk

與 self_heal_orchestrator（系統健康）互補：
本模組專注「單次對話生成」逾時重試與狀態恢復。
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class SelfHealingSettings:
    enabled: bool = True
    conversation_timeout_sec: float = 45.0
    max_retries: int = 3
    auto_fallback_llm: bool = True
    watchdog_enabled: bool = True
    preserve_session_on_restart: bool = True
    log_dir: str = "./data/logs"


@dataclass
class HealEvent:
    ts: float
    level: str  # info | warn | error | recover
    action: str
    message: str
    attempt: int = 0
    session_id: str | None = None
    ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionSnapshot:
    session_id: str
    payload: dict[str, Any]
    saved_at: float = field(default_factory=time.time)


GenerateFn = Callable[[str, str | None], Awaitable[str]]


class ConversationSelfHealing:
    """Wraps LLM generate with timeout, retry, fallback, and session preserve."""

    def __init__(
        self,
        settings: SelfHealingSettings | None = None,
        *,
        root: Path | None = None,
    ) -> None:
        self.settings = settings or SelfHealingSettings()
        self.root = root or Path(".")
        log_dir = Path(self.settings.log_dir)
        if not log_dir.is_absolute():
            log_dir = self.root / log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / "self_healing.jsonl"
        self.session_path = log_dir / "session_preserve.json"
        self.events: list[HealEvent] = []
        self._sessions: dict[str, SessionSnapshot] = {}
        self._load_sessions()

    # ── public API ──────────────────────────────────────────

    async def generate_with_heal(
        self,
        prompt: str,
        *,
        system: str | None = None,
        primary: GenerateFn,
        fallback: GenerateFn | None = None,
        session_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Return (text, meta). Never raises if fallback/rules available."""
        if not self.settings.enabled:
            text = await primary(prompt, system)
            return text, {"healed": False, "attempts": 1, "backend": "primary"}

        timeout = float(self.settings.conversation_timeout_sec)
        max_retries = max(0, int(self.settings.max_retries))
        last_err: str | None = None
        attempts = 0

        for attempt in range(max_retries + 1):
            attempts = attempt + 1
            try:
                text = await asyncio.wait_for(
                    primary(prompt, system),
                    timeout=timeout,
                )
                if text and str(text).strip():
                    if attempt > 0:
                        self._log(
                            "recover",
                            "retry_success",
                            f"attempt={attempts} ok",
                            attempt=attempts,
                            session_id=session_id,
                        )
                    return text, {
                        "healed": attempt > 0,
                        "attempts": attempts,
                        "backend": "primary",
                        "timeout_sec": timeout,
                    }
                last_err = "empty_response"
                self._log("warn", "empty_response", last_err, attempt=attempts, session_id=session_id, ok=False)
            except asyncio.TimeoutError:
                last_err = f"timeout>{timeout}s"
                self._log("warn", "timeout", last_err, attempt=attempts, session_id=session_id, ok=False)
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                self._log("error", "primary_fail", last_err, attempt=attempts, session_id=session_id, ok=False)
            # brief backoff
            await asyncio.sleep(min(0.5 * attempts, 2.0))

        # Fallback LLM
        if self.settings.auto_fallback_llm and fallback is not None:
            try:
                text = await asyncio.wait_for(fallback(prompt, system), timeout=timeout)
                self._log(
                    "recover",
                    "fallback_llm",
                    f"primary failed: {last_err}",
                    attempt=attempts,
                    session_id=session_id,
                )
                return text, {
                    "healed": True,
                    "attempts": attempts,
                    "backend": "fallback",
                    "last_error": last_err,
                }
            except Exception as exc:  # noqa: BLE001
                last_err = f"fallback: {exc}"
                self._log("error", "fallback_fail", last_err, attempt=attempts, session_id=session_id, ok=False)

        # Ultimate soft recovery — never crash the conversation
        soft = self._soft_reply(prompt, last_err)
        self._log("recover", "soft_reply", soft[:120], attempt=attempts, session_id=session_id)
        return soft, {
            "healed": True,
            "attempts": attempts,
            "backend": "soft",
            "last_error": last_err,
        }

    def preserve_session(self, session_id: str, payload: dict[str, Any]) -> None:
        if not self.settings.preserve_session_on_restart:
            return
        self._sessions[session_id] = SessionSnapshot(session_id=session_id, payload=payload)
        self._save_sessions()

    def restore_session(self, session_id: str) -> dict[str, Any] | None:
        snap = self._sessions.get(session_id)
        return snap.payload if snap else None

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.events[-limit:]]

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.settings.enabled,
            "conversation_timeout_sec": self.settings.conversation_timeout_sec,
            "max_retries": self.settings.max_retries,
            "auto_fallback_llm": self.settings.auto_fallback_llm,
            "watchdog_enabled": self.settings.watchdog_enabled,
            "preserve_session_on_restart": self.settings.preserve_session_on_restart,
            "events": len(self.events),
            "preserved_sessions": len(self._sessions),
            "developer": "suckbob",
            "publisher": "Monster_Ai_hk",
        }

    # ── internal ────────────────────────────────────────────

    def _soft_reply(self, prompt: str, err: str | None) -> str:
        # 不向用戶洩漏 debug 細節；錯誤只寫自癒日誌
        snippet = (prompt or "").replace("\n", " ").strip()[:80]
        if snippet:
            return (
                "剛才連線有點不穩，但我還在。"
                f"你剛說的「{snippet}」我有收到，可以再說一次或換個說法嗎？"
            )
        return "剛才連線有點不穩，但我還在。再說一次就好，我們繼續。"

    def _log(
        self,
        level: str,
        action: str,
        message: str,
        *,
        attempt: int = 0,
        session_id: str | None = None,
        ok: bool = True,
    ) -> None:
        ev = HealEvent(
            ts=time.time(),
            level=level,
            action=action,
            message=message,
            attempt=attempt,
            session_id=session_id,
            ok=ok,
        )
        self.events.append(ev)
        if len(self.events) > 500:
            self.events = self.events[-400:]
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass
        log_fn = logger.warning if level in ("warn", "error") else logger.info
        log_fn("self_healing [%s] %s: %s", level, action, message)

    def _load_sessions(self) -> None:
        if not self.session_path.exists():
            return
        try:
            data = json.loads(self.session_path.read_text(encoding="utf-8"))
            for sid, row in (data or {}).items():
                self._sessions[sid] = SessionSnapshot(
                    session_id=sid,
                    payload=row.get("payload") or {},
                    saved_at=float(row.get("saved_at") or time.time()),
                )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    def _save_sessions(self) -> None:
        try:
            dump = {
                sid: {"payload": s.payload, "saved_at": s.saved_at}
                for sid, s in list(self._sessions.items())[-50:]
            }
            self.session_path.write_text(
                json.dumps(dump, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
