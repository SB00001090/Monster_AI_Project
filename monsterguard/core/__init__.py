"""MonsterGuard core engines."""
from __future__ import annotations

from monsterguard.core.url_scanner import UrlScanner
from monsterguard.core.phishing_detector import PhishingDetector
from monsterguard.core.discord_scam_detector import DiscordScamDetector
from monsterguard.core.threat_classifier import ThreatClassifier
from monsterguard.core.ad_malware_blocker import AdMalwareBlocker
from monsterguard.core.quarantine import SecurityQuarantine
from monsterguard.core.real_time_protection import RealTimeProtection

__all__ = [
    "UrlScanner",
    "PhishingDetector",
    "DiscordScamDetector",
    "ThreatClassifier",
    "AdMalwareBlocker",
    "SecurityQuarantine",
    "RealTimeProtection",
]
