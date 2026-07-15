"""Phishing text / message heuristics (zh + en). Non-NSFW only."""
from __future__ import annotations

from monsterguard.core.signatures import SignatureStore
from monsterguard.core.url_scanner import UrlScanner
from monsterguard.models import ScanFinding, ScanResult


class PhishingDetector:
    def __init__(self, signatures: SignatureStore, url_scanner: UrlScanner | None = None) -> None:
        self.sig = signatures
        self.urls = url_scanner or UrlScanner(signatures)

    def scan_text(self, text: str, *, security_level: str = "medium") -> ScanResult:
        text = text or ""
        result = ScanResult(security_level=security_level, category="clean")
        lower = text.lower()

        phrase_hits: list[str] = []
        for phrase in self.sig.phishing_phrases():
            if phrase.lower() in lower or phrase in text:
                phrase_hits.append(phrase)

        if phrase_hits:
            score = min(90, 40 + 15 * len(phrase_hits))
            result.merge_finding(
                ScanFinding(
                    category="phishing",
                    score=score,
                    reasons=[f"phrase:{p[:40]}" for p in phrase_hits[:5]],
                    target="text",
                    recommended_action="warn" if score < 70 else "block",
                )
            )

        # urgency + credential combo
        urgency = any(
            k in lower or k in text
            for k in ("immediately", "urgent", "suspend", "立即", "緊急", "停用", "異常")
        )
        credential = any(
            k in lower or k in text
            for k in ("password", "seed phrase", "private key", "密碼", "助記詞", "私鑰", "驗證碼")
        )
        if urgency and credential:
            result.merge_finding(
                ScanFinding(
                    category="phishing",
                    score=75,
                    reasons=["urgency+credential_combo"],
                    target="text",
                    recommended_action="block",
                )
            )

        extracted = self.urls.extract_urls(text)
        if extracted:
            url_result = self.urls.scan(extracted, security_level=security_level)
            for f in url_result.findings:
                if f.category != "clean":
                    result.merge_finding(f)
            result.score = min(100, max(result.score, url_result.score))
            if url_result.category not in ("clean", "unknown") and url_result.score >= result.score:
                result.category = url_result.category

        if result.score == 0:
            result.category = "clean"
        return result
