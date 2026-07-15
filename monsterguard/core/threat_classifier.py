"""Aggregate threat classifier — rules first, optional LLM (non-NSFW only)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable

from monsterguard.core.ad_malware_blocker import AdMalwareBlocker
from monsterguard.core.discord_scam_detector import DiscordScamDetector
from monsterguard.core.phishing_detector import PhishingDetector
from monsterguard.core.signatures import SignatureStore
from monsterguard.core.url_scanner import UrlScanner
from monsterguard.models import SECURITY_CATEGORIES, ScanResult

logger = logging.getLogger(__name__)

LEVEL_THRESHOLDS = {
    "low": {"block": 85, "quarantine": 95},
    "medium": {"block": 70, "quarantine": 80},
    "high": {"block": 55, "quarantine": 65},
}

ChatFn = Callable[[str, str], Awaitable[str]]


class ThreatClassifier:
    def __init__(
        self,
        signatures: SignatureStore,
        *,
        security_level: str = "medium",
        use_llm: bool = False,
        chat_fn: ChatFn | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        self.sig = signatures
        self.security_level = security_level if security_level in LEVEL_THRESHOLDS else "medium"
        self.use_llm = use_llm
        self.chat_fn = chat_fn
        self.prompt_path = prompt_path
        self.urls = UrlScanner(signatures)
        self.phishing = PhishingDetector(signatures, self.urls)
        self.downloads = AdMalwareBlocker(signatures)
        self.discord = DiscordScamDetector(url_scanner=self.urls)

    def thresholds(self) -> dict[str, int]:
        return dict(LEVEL_THRESHOLDS[self.security_level])

    def apply_policy(self, result: ScanResult) -> ScanResult:
        th = self.thresholds()
        result.security_level = self.security_level
        result.block = result.score >= th["block"]
        result.quarantine = result.score >= th["quarantine"]
        if result.category not in SECURITY_CATEGORIES:
            result.category = "unknown"
        # Never invent content-moderation categories
        forbidden = {"nsfw", "adult", "porn", "sexual", "roleplay"}
        if result.category.lower() in forbidden:
            result.category = "unknown"
            result.reasons.append("stripped_non_security_category")
            result.block = False
            result.quarantine = False
        return result

    def classify_urls(self, urls: list[str]) -> ScanResult:
        result = self.urls.scan(urls, security_level=self.security_level)
        return self.apply_policy(result)

    def classify_text(self, text: str) -> ScanResult:
        result = self.phishing.scan_text(text, security_level=self.security_level)
        discord_result = self.discord.scan_message(text, security_level=self.security_level)
        for f in discord_result.findings:
            if f.category != "clean":
                result.merge_finding(f)
        for r in discord_result.reasons:
            if r not in result.reasons:
                result.reasons.append(r)
        result.score = min(100, max(result.score, discord_result.score))
        if discord_result.score >= result.score and discord_result.category not in (
            "clean",
            "unknown",
        ):
            result.category = discord_result.category
        return self.apply_policy(result)

    def classify_discord_message(
        self,
        content: str,
        *,
        urls: list[str] | None = None,
        attachment_names: list[str] | None = None,
    ) -> ScanResult:
        result = self.discord.scan_message(
            content,
            urls=urls,
            attachment_names=attachment_names,
            security_level=self.security_level,
        )
        # Also run generic phishing pass
        ph = self.phishing.scan_text(content, security_level=self.security_level)
        for f in ph.findings:
            if f.category != "clean":
                result.merge_finding(f)
        result.score = min(100, max(result.score, ph.score))
        return self.apply_policy(result)

    def classify_download(self, path_or_url: str, *, block_downloads: bool = True) -> ScanResult:
        result = self.downloads.scan_download(
            path_or_url,
            security_level=self.security_level,
            block_downloads=block_downloads,
        )
        return self.apply_policy(result)

    async def classify_text_async(self, text: str) -> ScanResult:
        result = self.classify_text(text)
        if not self.use_llm or self.chat_fn is None or result.score >= 80:
            return result
        # Only enhance borderline cases
        if result.score > 0 and result.score < 80:
            enhanced = await self._llm_enhance(text, result)
            if enhanced:
                return self.apply_policy(enhanced)
        return result

    async def _llm_enhance(self, text: str, base: ScanResult) -> ScanResult | None:
        system = (
            "You are MonsterGuard. Only non-NSFW security threats. "
            "Never moderate adult/RP content. JSON only."
        )
        if self.prompt_path and self.prompt_path.is_file():
            system = self.prompt_path.read_text(encoding="utf-8")
        prompt = (
            f"{system}\n\n"
            f"text={text[:1500]!r}\n"
            f"rule_score={base.score} category={base.category} reasons={base.reasons}"
        )
        try:
            raw = await self.chat_fn(prompt, system)
            if not raw or "{" not in raw:
                return None
            blob = raw[raw.index("{") : raw.rindex("}") + 1]
            data: dict[str, Any] = json.loads(blob)
            cat = str(data.get("category") or "unknown")
            if cat not in SECURITY_CATEGORIES:
                return None
            base.score = min(100, max(base.score, int(data.get("score") or 0)))
            base.category = cat if cat != "clean" else base.category
            for r in data.get("reasons") or []:
                if str(r) not in base.reasons:
                    base.reasons.append(str(r))
            if data.get("block"):
                base.block = True
            base.reasons.append("llm_classifier")
            return base
        except Exception:  # noqa: BLE001
            logger.debug("LLM classifier enhance failed", exc_info=True)
            return None
