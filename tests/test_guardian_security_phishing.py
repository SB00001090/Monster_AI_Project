"""Compat re-export — phishing covered in test_monsterguard_discord."""
from __future__ import annotations

from pathlib import Path

from monsterguard.service import MonsterGuardService


def test_rp_not_blocked(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    svc = MonsterGuardService(
        enabled=True,
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )
    r = svc.scan_text("在奇幻酒館裡，兩位冒險者討論明天的旅程。")
    assert r["block"] is False
