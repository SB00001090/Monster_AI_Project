"""MonsterGuard service facade."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from monsterguard.core.quarantine import SecurityQuarantine
from monsterguard.core.real_time_protection import RealTimeProtection
from monsterguard.core.signatures import SignatureStore
from monsterguard.core.threat_classifier import ThreatClassifier
from monsterguard.models import ScanResult
from monsterguard.ui.dashboard import build_dashboard
from monsterguard.ui.threat_report import build_threat_report


class MonsterGuardService:
    def __init__(
        self,
        *,
        enabled: bool = True,
        security_level: str = "medium",
        real_time: bool = True,
        block_downloads: bool = True,
        use_llm_classifier: bool = False,
        signatures_path: str | Path,
        cache_dir: str | Path,
        reputation_ttl_hours: float = 24.0,
        prompt_path: str | Path | None = None,
        protection_quarantine: Any | None = None,
        chat_fn: Any | None = None,
    ) -> None:
        self.enabled = enabled
        self.security_level = security_level
        self.block_downloads = block_downloads
        self.use_llm_classifier = use_llm_classifier
        root = Path(__file__).resolve().parent
        sig_path = Path(signatures_path)
        if not sig_path.is_file():
            sig_path = root / "database" / "threat_signatures.json"
        prompt = Path(prompt_path) if prompt_path else root / "prompts" / "monsterguard_security_prompt.txt"

        self.signatures = SignatureStore(
            sig_path,
            Path(cache_dir),
            reputation_ttl_hours=reputation_ttl_hours,
        )
        self.classifier = ThreatClassifier(
            self.signatures,
            security_level=security_level,
            use_llm=use_llm_classifier,
            chat_fn=chat_fn,
            prompt_path=prompt if prompt.is_file() else None,
        )
        self.quarantine = SecurityQuarantine(
            Path(cache_dir) / "quarantine",
            protection_zone=protection_quarantine,
        )
        self.rtp = RealTimeProtection(enabled=enabled and real_time)

    def status(self) -> dict[str, Any]:
        return {
            "product": "MonsterGuard",
            "distinct_from": "Guardian Platform (monster_ai.modules.guardian)",
            "enabled": self.enabled,
            "security_level": self.security_level,
            "block_downloads": self.block_downloads,
            "use_llm_classifier": self.use_llm_classifier,
            "thresholds": self.classifier.thresholds(),
            "signatures": self.signatures.status(),
            "quarantine": self.quarantine.status(),
            "real_time": self.rtp.status(),
        }

    def _maybe_quarantine(self, result: ScanResult, target: str) -> ScanResult:
        if result.quarantine and self.enabled:
            entry = self.quarantine.isolate(
                target=target,
                reasons=result.reasons,
                score=result.score,
                category=result.category,
            )
            result.reasons = list(result.reasons) + [f"quarantined:{entry.get('id')}"]
            self.rtp.record_event(
                {
                    "type": "quarantine",
                    "target": target[:200],
                    "score": result.score,
                    "category": result.category,
                }
            )
        elif result.block:
            self.rtp.record_event(
                {
                    "type": "block",
                    "target": target[:200],
                    "score": result.score,
                    "category": result.category,
                }
            )
        self.signatures.save_reputation()
        return result

    def scan_urls(self, urls: list[str]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "enabled": False, "score": 0, "category": "clean", "block": False}
        result = self.classifier.classify_urls(urls)
        target = ",".join(urls)[:500]
        result = self._maybe_quarantine(result, target)
        return result.to_dict()

    def scan_text(self, text: str) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "enabled": False, "score": 0, "category": "clean", "block": False}
        result = self.classifier.classify_text(text)
        result = self._maybe_quarantine(result, text[:200])
        return result.to_dict()

    async def scan_text_async(self, text: str) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "enabled": False, "score": 0, "category": "clean", "block": False}
        result = await self.classifier.classify_text_async(text)
        result = self._maybe_quarantine(result, text[:200])
        return result.to_dict()

    def scan_download(self, path_or_url: str) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "enabled": False, "score": 0, "category": "clean", "block": False}
        result = self.classifier.classify_download(
            path_or_url, block_downloads=self.block_downloads
        )
        result = self._maybe_quarantine(result, path_or_url)
        return result.to_dict()

    def scan_discord_message(
        self,
        content: str,
        *,
        urls: list[str] | None = None,
        attachment_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Discord-focused scam scan (Nitro / verify / crypto / hacked DM)."""
        if not self.enabled:
            return {"ok": True, "enabled": False, "score": 0, "category": "clean", "block": False}
        result = self.classifier.classify_discord_message(
            content, urls=urls, attachment_names=attachment_names
        )
        result = self._maybe_quarantine(result, (content or "")[:200])
        return result.to_dict()

    def list_quarantine(self, limit: int = 20) -> dict[str, Any]:
        return {"entries": self.quarantine.list_active(limit=limit)}

    def release_quarantine(self, entry_id: str) -> dict[str, Any]:
        return self.quarantine.release(entry_id)

    def report(self) -> dict[str, Any]:
        return build_threat_report(self)

    def dashboard(self) -> dict[str, Any]:
        return build_dashboard(self)

    async def start(self) -> None:
        if self.enabled:
            await self.rtp.start()

    async def stop(self) -> None:
        await self.rtp.stop()
        self.signatures.save_reputation()
