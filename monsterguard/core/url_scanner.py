"""URL scanning with signatures, lookalike and reputation cache."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from monsterguard.core.signatures import SignatureStore
from monsterguard.models import ScanFinding, ScanResult

_HOMOGLYPH_O = re.compile(r"[\u043e\u03bf]")  # Cyrillic/Greek o
_URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.I)


class UrlScanner:
    def __init__(self, signatures: SignatureStore) -> None:
        self.sig = signatures

    @staticmethod
    def extract_urls(text: str) -> list[str]:
        return list(dict.fromkeys(_URL_RE.findall(text or "")))

    def normalize_host(self, url: str) -> str:
        try:
            raw = url if "://" in url else f"http://{url}"
            parsed = urlparse(raw)
            return (parsed.hostname or "").lower()
        except Exception:  # noqa: BLE001
            return ""

    def scan(self, urls: list[str], *, security_level: str = "medium") -> ScanResult:
        result = ScanResult(security_level=security_level, category="clean")
        for url in urls:
            host = self.normalize_host(url)
            if not host:
                continue

            # Reputation cache short-circuit
            rep = self.sig.get_reputation(host)
            if rep and int(rep.get("score", 0)) >= 70:
                result.merge_finding(
                    ScanFinding(
                        category=str(rep.get("category") or "phishing"),
                        score=int(rep["score"]),
                        reasons=[f"reputation_cache:{host}"],
                        target=url,
                        recommended_action="block",
                    )
                )
                continue

            if self.sig.host_allowlisted(host):
                result.merge_finding(
                    ScanFinding(
                        category="clean",
                        score=0,
                        reasons=[f"allowlist:{host}"],
                        target=url,
                        recommended_action="allow",
                    )
                )
                continue

            if self.sig.host_blacklisted(host):
                result.merge_finding(
                    ScanFinding(
                        category="phishing",
                        score=90,
                        reasons=[f"blacklist:{host}"],
                        target=url,
                        recommended_action="block",
                    )
                )
                self.sig.set_reputation(host, score=90, category="phishing")
                continue

            lookalike_hits = self.sig.match_lookalike(host) or self.sig.match_lookalike(url)
            tld = "." + host.rsplit(".", 1)[-1] if "." in host else ""
            brand_impersonation = any(
                any(k in h.lower() for k in ("disc", "dlscord", "nitro", "steam", "paypal", "microsoft"))
                for h in lookalike_hits
            ) or any(k in host for k in ("dlscord", "disc0rd", "discord-nitro", "free-nitro"))

            if lookalike_hits and not self.sig.host_allowlisted(host):
                # Genuine discord.com already allowlisted
                score = 75 if brand_impersonation else 55
                if tld in self.sig.suspicious_tlds:
                    score = min(100, score + 15)
                result.merge_finding(
                    ScanFinding(
                        category="lookalike",
                        score=score,
                        reasons=[f"lookalike:{h}" for h in lookalike_hits[:3]],
                        target=url,
                        recommended_action="block" if score >= 70 else "warn",
                    )
                )
                self.sig.set_reputation(host, score=score, category="lookalike")

            if _HOMOGLYPH_O.search(host):
                result.merge_finding(
                    ScanFinding(
                        category="phishing",
                        score=65,
                        reasons=[f"homoglyph_domain:{host}"],
                        target=url,
                        recommended_action="warn",
                    )
                )

            if tld in self.sig.suspicious_tlds and brand_impersonation and not lookalike_hits:
                result.merge_finding(
                    ScanFinding(
                        category="phishing",
                        score=70,
                        reasons=[f"suspicious_tld:{tld}", "brand_impersonation_host"],
                        target=url,
                        recommended_action="block",
                    )
                )

        # Collapse clean-only noise: if only clean findings, keep clean
        if result.score == 0:
            result.category = "clean"
        return result

    async def scan_async(self, urls: list[str], *, security_level: str = "medium") -> ScanResult:
        return self.scan(urls, security_level=security_level)
