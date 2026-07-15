"""Shared result types for MonsterGuard (non-NSFW threats only)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Allowed threat categories — content moderation / NSFW are intentionally absent.
SECURITY_CATEGORIES = frozenset(
    {
        "phishing",
        "malware",
        "scam_ad",
        "lookalike",
        "suspicious_download",
        "nitro",  # Discord free-nitro style (maps to phishing for policy)
        "clean",
        "unknown",
    }
)


@dataclass
class ScanFinding:
    category: str = "unknown"
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    target: str = ""
    recommended_action: str = "allow"  # allow | warn | block | quarantine

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    ok: bool = True
    score: int = 0
    category: str = "clean"
    findings: list[ScanFinding] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    block: bool = False
    quarantine: bool = False
    security_level: str = "medium"
    engine: str = "monsterguard"

    def merge_finding(self, finding: ScanFinding) -> None:
        self.findings.append(finding)
        self.score = min(100, max(self.score, finding.score))
        for r in finding.reasons:
            if r not in self.reasons:
                self.reasons.append(r)
        if finding.category in SECURITY_CATEGORIES and finding.category not in (
            "clean",
            "unknown",
        ):
            if finding.score >= self.score or self.category in ("clean", "unknown"):
                self.category = finding.category

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "category": self.category,
            "reasons": self.reasons,
            "block": self.block,
            "quarantine": self.quarantine,
            "security_level": self.security_level,
            "engine": self.engine,
            "findings": [f.to_dict() for f in self.findings],
        }

    # Discord ThreatResult compatibility helpers
    @property
    def scam_type(self) -> str | None:
        if self.category in ("clean", "unknown"):
            return "none" if self.category == "clean" else None
        return self.category

    @property
    def recommended_action(self) -> str:
        if self.block:
            return "delete"
        if self.score >= 50:
            return "warn"
        return "monitor"
