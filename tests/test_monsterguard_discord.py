"""Discord scam pattern tests."""
from __future__ import annotations

from pathlib import Path

from monsterguard.service import MonsterGuardService


def _svc(tmp_path: Path) -> MonsterGuardService:
    root = Path(__file__).resolve().parents[1]
    return MonsterGuardService(
        enabled=True,
        security_level="medium",
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )


def test_free_nitro_message(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_discord_message(
        "You've been gifted nitro! Click here to claim nitro free"
    )
    assert r["score"] >= 40
    assert any("discord_nitro" in x or "scam_type:nitro" in x for x in r.get("reasons", []))


def test_verify_bot_scam(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_discord_message("Please verify your server and click verify below")
    assert r["score"] >= 30


def test_hacked_dm_pattern(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_discord_message("bro is this your account? is this you in the video")
    assert r["score"] >= 25


def test_attachment_exe(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_discord_message(
        "install this client update",
        attachment_names=["discord_update.exe"],
    )
    assert r["block"] is True
    assert r["score"] >= 80


def test_clean_normal_chat(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_discord_message("今晚要不要一起打遊戲？discord 語音見")
    assert r["block"] is False
