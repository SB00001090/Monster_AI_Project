"""MonsterGuardCore — always-on security service facade."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from guardian_ai.monster_guard.core.auto_blocker import AutoBlocker
from guardian_ai.monster_guard.core.discord_scam_detector import DiscordScamDetector
from guardian_ai.monster_guard.core.real_time_monitor import RealTimeMonitor
from guardian_ai.monster_guard.core.self_repair import SelfRepair
from guardian_ai.monster_guard.core.url_reputation import UrlReputation
from monsterguard.service import MonsterGuardService

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_monster_guard_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (
        Path(__file__).resolve().parents[1] / "config" / "monster_guard_config.json"
    )
    if not cfg_path.is_file():
        return {
            "enabled": True,
            "security_level": "medium",
            "always_on": True,
            "monitor_interval_seconds": 15,
            "block_threshold": 70,
            "warn_threshold": 50,
            "auto_block": True,
            "auto_restart": True,
            "max_restarts_per_hour": 6,
            "restart_backoff_seconds": 5,
            "paths": {
                "scam_patterns": "guardian_ai/monster_guard/database/scam_patterns.json",
                "blocked_list": "guardian_ai/monster_guard/database/blocked_list.json",
                "threat_log": "data/monster_guard/reports/threat_log.json",
                "runtime_dir": "data/monster_guard",
            },
        }
    return json.loads(cfg_path.read_text(encoding="utf-8"))


class MonsterGuardCore:
    """24/7 MonsterGuard core: scan + reputation + block + monitor + logs."""

    def __init__(self, config: dict[str, Any] | None = None, *, config_path: Path | None = None) -> None:
        self.config = config or load_monster_guard_config(config_path)
        self.root = _repo_root()
        paths = self.config.get("paths") or {}
        runtime = self.root / str(paths.get("runtime_dir") or "data/monster_guard")
        runtime.mkdir(parents=True, exist_ok=True)
        (runtime / "reports").mkdir(parents=True, exist_ok=True)

        self.runtime_dir = runtime
        threat_log = self.root / str(paths.get("threat_log") or "data/monster_guard/reports/threat_log.json")
        threat_log.parent.mkdir(parents=True, exist_ok=True)
        self.threat_log_path = threat_log

        blocked_path = self.root / str(
            paths.get("blocked_list")
            or "guardian_ai/monster_guard/database/blocked_list.json"
        )
        scam_path = self.root / str(
            paths.get("scam_patterns")
            or "guardian_ai/monster_guard/database/scam_patterns.json"
        )

        level = str(self.config.get("security_level") or "medium")
        self.engine = MonsterGuardService(
            enabled=bool(self.config.get("enabled", True)),
            security_level=level,
            real_time=False,  # monitor owns the loop
            signatures_path=self.root / "monsterguard" / "database" / "threat_signatures.json",
            cache_dir=runtime / "cache",
        )
        self.discord = DiscordScamDetector(
            patterns_path=scam_path if scam_path.is_file() else None,
            url_scanner=self.engine.classifier.urls,
        )
        self.reputation = UrlReputation(
            signatures=self.engine.signatures,
            runtime_dir=runtime,
        )
        self.blocker = AutoBlocker(
            blocked_path,
            block_threshold=int(self.config.get("block_threshold", 70)),
            warn_threshold=int(self.config.get("warn_threshold", 50)),
            auto_block=bool(self.config.get("auto_block", True)),
        )
        self.self_repair = SelfRepair(
            auto_restart=bool(self.config.get("auto_restart", True)),
            max_restarts_per_hour=int(self.config.get("max_restarts_per_hour", 6)),
            backoff_seconds=float(self.config.get("restart_backoff_seconds", 5)),
        )
        self.monitor = RealTimeMonitor(
            interval_seconds=float(self.config.get("monitor_interval_seconds", 15)),
            enabled=bool(self.config.get("always_on", True)),
            health_fn=self.health,
        )

    def health(self) -> dict[str, Any]:
        return {
            "ok": bool(self.config.get("enabled", True)),
            "product": "MonsterGuard",
            "enabled": self.engine.enabled,
            "monitor": self.monitor.status().get("running"),
            "blocker_hosts": self.blocker.status().get("hosts"),
        }

    def status(self) -> dict[str, Any]:
        return {
            "product": "MonsterGuard",
            "package": "guardian_ai.monster_guard",
            "enabled": self.engine.enabled,
            "security_level": self.engine.security_level,
            "config_always_on": bool(self.config.get("always_on", True)),
            "engine": self.engine.status(),
            "reputation": self.reputation.status(),
            "blocker": self.blocker.status(),
            "monitor": self.monitor.status(),
            "self_repair": self.self_repair.status(),
            "runtime_dir": str(self.runtime_dir),
            "threat_log": str(self.threat_log_path),
        }

    def _log_threat(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("ts", time.time())
        # Append-friendly JSONL stored as .json path for simplicity
        log_path = self.threat_log_path
        if log_path.suffix == ".json":
            log_path = log_path.with_suffix(".jsonl")
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.debug("threat log write failed: %s", exc)
        self.monitor.record(event)

    def scan_url(self, url: str) -> dict[str, Any]:
        rep = self.reputation.check(url, security_level=self.engine.security_level)
        # merge with engine policy
        eng = self.engine.scan_urls([url])
        merged = {**eng, **{"reputation": rep}}
        merged["score"] = max(int(eng.get("score") or 0), int(rep.get("score") or 0))
        action = self.blocker.apply_scan(merged)
        merged["auto_block"] = action
        if action.get("action") in ("block", "warn"):
            self._log_threat({"type": "url_scan", "url": url, "result": merged})
        return merged

    def scan_discord(self, content: str, **kwargs: Any) -> dict[str, Any]:
        base = self.engine.scan_discord_message(content, **kwargs)
        local = self.discord.scan_message(
            content,
            urls=kwargs.get("urls"),
            attachment_names=kwargs.get("attachment_names"),
            security_level=self.engine.security_level,
        )
        for f in local.findings:
            if f.category != "clean":
                # engine already may include; boost score
                base["score"] = max(int(base.get("score") or 0), f.score)
                for r in f.reasons:
                    if r not in (base.get("reasons") or []):
                        base.setdefault("reasons", []).append(r)
        action = self.blocker.apply_scan(base)
        base["auto_block"] = action
        if action.get("action") in ("block", "warn"):
            self._log_threat({"type": "discord_scan", "preview": content[:120], "result": base})
        return base

    def scan_text(self, text: str) -> dict[str, Any]:
        result = self.engine.scan_text(text)
        action = self.blocker.apply_scan(result)
        result["auto_block"] = action
        if action.get("action") in ("block", "warn"):
            self._log_threat({"type": "text_scan", "preview": text[:120], "result": result})
        return result

    async def start(self) -> None:
        await self.monitor.start()
        logger.info("MonsterGuardCore started")

    async def stop(self) -> None:
        await self.monitor.stop()
        await self.engine.stop()
        logger.info("MonsterGuardCore stopped")
