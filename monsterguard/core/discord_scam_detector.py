"""Discord-specific scam detection (Nitro / verify / crypto / hacked DM).

Complements generic phishing — tuned for MonsterGuard Discord bot pipelines.
Non-NSFW only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from monsterguard.core.url_scanner import UrlScanner
from monsterguard.models import ScanFinding, ScanResult

_URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+|discord\.gg/[^\s]+", re.I)


class DiscordScamDetector:
    def __init__(
        self,
        patterns_path: Path | None = None,
        url_scanner: UrlScanner | None = None,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        path = patterns_path or (root / "database" / "discord_scam_patterns.json")
        self.patterns = self._load(path)
        self.urls = url_scanner
        self._safe = {h.lower() for h in (self.patterns.get("safe_discord_hosts") or [])}
        self._suspicious = [d.lower() for d in (self.patterns.get("suspicious_domains") or [])]

    def _load(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {"scam_types": {}, "suspicious_domains": [], "safe_discord_hosts": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def scan_message(
        self,
        content: str,
        *,
        urls: list[str] | None = None,
        attachment_names: list[str] | None = None,
        security_level: str = "medium",
    ) -> ScanResult:
        text = content or ""
        lower = text.lower()
        result = ScanResult(
            security_level=security_level,
            category="clean",
            engine="monsterguard",
        )

        scam_types: dict[str, Any] = self.patterns.get("scam_types") or {}
        for scam_type, cfg in scam_types.items():
            weight = int(cfg.get("weight") or 30)
            phrases = list(cfg.get("phrases_en") or []) + list(cfg.get("phrases_zh") or [])
            hits = [p for p in phrases if p.lower() in lower or p in text]
            if not hits:
                continue
            score = min(95, weight + 12 * min(3, len(hits)))
            # Map Discord scam types into security categories
            category = {
                "nitro": "phishing",
                "verification": "phishing",
                "crypto": "phishing",
                "hacked_dm": "phishing",
                "malware": "malware",
            }.get(scam_type, "phishing")
            result.merge_finding(
                ScanFinding(
                    category=category,
                    score=score,
                    reasons=[f"discord_{scam_type}:{h[:40]}" for h in hits[:4]],
                    target="discord_message",
                    recommended_action="block" if score >= 70 else "warn",
                )
            )
            # Keep scam_type in reasons for Discord bot compatibility
            result.reasons.append(f"scam_type:{scam_type}")

        found_urls = list(urls or [])
        found_urls.extend(_URL_RE.findall(text))
        # de-dupe
        found_urls = list(dict.fromkeys(found_urls))

        for url in found_urls:
            host = self._host(url)
            if not host:
                continue
            if any(host == s or host.endswith("." + s) for s in self._safe):
                continue
            for sus in self._suspicious:
                if sus in host or sus in url.lower():
                    result.merge_finding(
                        ScanFinding(
                            category="lookalike",
                            score=80,
                            reasons=[f"discord_suspicious_domain:{sus}"],
                            target=url,
                            recommended_action="block",
                        )
                    )
                    result.reasons.append("scam_type:nitro")

        if self.urls and found_urls:
            url_result = self.urls.scan(found_urls, security_level=security_level)
            for f in url_result.findings:
                if f.category != "clean":
                    result.merge_finding(f)

        for name in attachment_names or []:
            n = name.lower()
            if n.endswith((".exe", ".scr", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".msi")):
                result.merge_finding(
                    ScanFinding(
                        category="malware",
                        score=85,
                        reasons=[f"discord_attachment:{name}"],
                        target=name,
                        recommended_action="block",
                    )
                )
                result.reasons.append("scam_type:malware")

        if result.score == 0:
            result.category = "clean"
        return result

    @staticmethod
    def _host(url: str) -> str:
        try:
            raw = url if "://" in url else f"http://{url}"
            return (urlparse(raw).hostname or "").lower()
        except Exception:  # noqa: BLE001
            return ""
