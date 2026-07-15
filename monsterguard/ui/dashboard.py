"""CLI / API dashboard summary for MonsterGuard (antivirus-style)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monsterguard.service import MonsterGuardService


def build_dashboard(svc: MonsterGuardService) -> dict[str, Any]:
    st = svc.status()
    level = st.get("security_level", "medium")
    shield = "ACTIVE" if st.get("enabled") and st.get("real_time", {}).get("running") else "IDLE"
    return {
        "title": "MonsterGuard 安全防護",
        "subtitle": "本地優先 · 防毒風格 · Discord 防詐騙（非內容審查）",
        "shield": shield,
        "security_level": level,
        "stats": {
            "signature_hosts": st.get("signatures", {}).get("blacklist_hosts", 0),
            "reputation_cache": st.get("signatures", {}).get("reputation_entries", 0),
            "quarantine_active": st.get("quarantine", {}).get("active", 0),
            "rtp_ticks": st.get("real_time", {}).get("ticks", 0),
        },
        "thresholds": st.get("thresholds"),
        "note": "與 Guardian 平台（E2E 同步 / 幼兒教育式學習）分離 · Discord 管線可共用",
        "raw": st,
    }
