"""Tests for guardian_ai.monster_guard 24/7 core."""
from __future__ import annotations

import json
from pathlib import Path

from guardian_ai.monster_guard.service import MonsterGuardCore, load_monster_guard_config
from guardian_ai.monster_guard.core.auto_blocker import AutoBlocker
from guardian_ai.monster_guard.core.self_repair import SelfRepair


def test_load_config() -> None:
    cfg = load_monster_guard_config()
    assert cfg.get("product") == "MonsterGuard" or cfg.get("enabled") is True
    assert "paths" in cfg or "security_level" in cfg


def test_core_status() -> None:
    core = MonsterGuardCore()
    st = core.status()
    assert st["product"] == "MonsterGuard"
    assert st["package"] == "guardian_ai.monster_guard"
    assert "blocker" in st
    assert "monitor" in st


def test_scan_discord_nitro(tmp_path: Path, monkeypatch) -> None:
    core = MonsterGuardCore()
    # redirect runtime/logs
    core.runtime_dir = tmp_path
    core.threat_log_path = tmp_path / "threat_log.json"
    core.blocker = AutoBlocker(
        tmp_path / "blocked_list.json",
        block_threshold=70,
        auto_block=True,
    )
    r = core.scan_discord("You've been gifted nitro! claim nitro free now")
    assert r["score"] >= 30
    assert "auto_block" in r


def test_scan_url_lookalike(tmp_path: Path) -> None:
    core = MonsterGuardCore()
    core.blocker = AutoBlocker(tmp_path / "bl.json", block_threshold=70, auto_block=True)
    r = core.scan_url("https://dlscord-nitro.xyz/gift")
    assert r["score"] >= 55
    assert r.get("auto_block", {}).get("action") in ("block", "warn", "allow")


def test_auto_blocker_thresholds(tmp_path: Path) -> None:
    b = AutoBlocker(tmp_path / "b.json", block_threshold=70, warn_threshold=50)
    assert b.decide(40) == "allow"
    assert b.decide(55) == "warn"
    assert b.decide(80) == "block"
    r = b.block_host("evil.example", reason="test", score=90)
    assert r["ok"] is True
    assert b.is_blocked_host("evil.example")


def test_self_repair_budget() -> None:
    sr = SelfRepair(auto_restart=True, max_restarts_per_hour=2, backoff_seconds=1)
    assert sr.can_restart()[0] is True
    sr.mark_restart()
    sr.mark_restart()
    ok, reason = sr.can_restart()
    assert ok is False
    assert reason == "restart_budget_exhausted"
