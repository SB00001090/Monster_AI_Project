"""URL normalization and blacklist scanning.

Delegates to top-level `monsterguard` package when available so Discord
MonsterGuard bot and HTTP API share one engine.

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from monster_ai.modules.discord.guard.threat import ThreatResult

_SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".gq", ".tk", ".ml", ".cf", ".ga", ".buzz", ".icu"}
_DISCORD_LOOKALIKE = re.compile(r"disc[o0]rd|dlscord|discord[\s.-]?app|discord[\s.-]?gift", re.I)
_HOMOGLYPH_O = re.compile(r"[\u043e\u03bf]")


def _to_threat_result(payload: dict) -> ThreatResult:
    score = int(payload.get("score") or 0)
    category = str(payload.get("category") or "none")
    if category in ("clean", "unknown"):
        scam = "none" if category == "clean" else None
    else:
        scam = category if category in (
            "nitro",
            "verification",
            "crypto",
            "hacked_dm",
            "malware",
            "raid",
            "phishing",
        ) else "phishing"
    # Map lookalike/scam_ad into phishing for Discord action layer
    if scam is None and category in ("lookalike", "scam_ad", "suspicious_download"):
        scam = "phishing" if category != "suspicious_download" else "malware"
    action = "delete" if payload.get("block") else ("warn" if score >= 50 else "monitor")
    # Prefer scam_type hint from reasons
    for r in payload.get("reasons") or []:
        if str(r).startswith("scam_type:"):
            st = str(r).split(":", 1)[1]
            if st in ("nitro", "verification", "crypto", "hacked_dm", "malware", "phishing"):
                scam = st
    return ThreatResult(
        score=score,
        reasons=list(payload.get("reasons") or []),
        scam_type=scam,
        recommended_action=action,
        confidence=min(1.0, score / 100.0),
    )


class UrlScanner:
    def __init__(self, blacklist_path: Path | None = None) -> None:
        self._domains: set[str] = set()
        self._mg = None
        if blacklist_path and blacklist_path.exists():
            for line in blacklist_path.read_text(encoding="utf-8").splitlines():
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    self._domains.add(line)
        try:
            from monsterguard.service import MonsterGuardService

            root = Path(__file__).resolve().parents[4]
            self._mg = MonsterGuardService(
                enabled=True,
                security_level="medium",
                real_time=False,
                signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
                cache_dir=root / "data" / "monsterguard",
            )
            for d in self._domains:
                bl = list(self._mg.signatures.data.get("blacklist_hosts") or [])
                if d not in bl:
                    bl.append(d)
                    self._mg.signatures.data["blacklist_hosts"] = bl
        except Exception:  # noqa: BLE001
            self._mg = None

    def add_domain(self, domain: str) -> None:
        self._domains.add(domain.lower().strip())
        if self._mg is not None:
            bl = list(self._mg.signatures.data.get("blacklist_hosts") or [])
            host = domain.lower().strip()
            if host not in bl:
                bl.append(host)
                self._mg.signatures.data["blacklist_hosts"] = bl

    def _normalize_host(self, url: str) -> str:
        try:
            parsed = urlparse(url if "://" in url else f"http://{url}")
            return (parsed.hostname or "").lower()
        except Exception:  # noqa: BLE001
            return ""

    async def scan(self, urls: list[str]) -> ThreatResult:
        if self._mg is not None:
            payload = self._mg.scan_urls(urls)
            return _to_threat_result(payload)

        result = ThreatResult()
        for url in urls:
            host = self._normalize_host(url)
            if not host:
                continue
            if host in self._domains:
                result.merge(
                    ThreatResult(
                        score=80,
                        reasons=[f"blacklist:{host}"],
                        scam_type="phishing",
                        recommended_action="delete",
                    )
                )
                continue
            if _DISCORD_LOOKALIKE.search(host) and "discord.com" not in host and "discord.gg" not in host:
                result.merge(
                    ThreatResult(
                        score=55,
                        reasons=[f"lookalike_domain:{host}"],
                        scam_type="nitro",
                    )
                )
            if _HOMOGLYPH_O.search(host):
                result.merge(
                    ThreatResult(score=60, reasons=[f"homoglyph_domain:{host}"], scam_type="phishing")
                )
            tld = "." + host.rsplit(".", 1)[-1] if "." in host else ""
            if tld in _SUSPICIOUS_TLDS and _DISCORD_LOOKALIKE.search(url):
                result.merge(
                    ThreatResult(score=40, reasons=[f"suspicious_tld:{tld}"], scam_type="phishing")
                )
        return result
