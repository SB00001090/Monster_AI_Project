"""Load and query local threat signature seed + runtime reputation cache."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


class SignatureStore:
    def __init__(
        self,
        signatures_path: Path,
        cache_dir: Path,
        *,
        reputation_ttl_hours: float = 24.0,
        max_cache_entries: int = 5000,
    ) -> None:
        self.signatures_path = Path(signatures_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.reputation_path = self.cache_dir / "reputation_cache.json"
        self.reputation_ttl = max(1.0, float(reputation_ttl_hours)) * 3600.0
        self.max_cache_entries = max_cache_entries
        self.data = self._load_signatures()
        self._reputation = self._load_reputation()
        self._lookalike_re = [
            re.compile(p, re.I) for p in self.data.get("lookalike_patterns") or []
        ]

    def _load_signatures(self) -> dict[str, Any]:
        if not self.signatures_path.is_file():
            return {
                "allowlist_hosts": [],
                "blacklist_hosts": [],
                "suspicious_tlds": [],
                "lookalike_patterns": [],
                "dangerous_extensions": [],
                "phishing_phrases_en": [],
                "phishing_phrases_zh": [],
            }
        return json.loads(self.signatures_path.read_text(encoding="utf-8"))

    def _load_reputation(self) -> dict[str, Any]:
        if not self.reputation_path.is_file():
            return {}
        try:
            return json.loads(self.reputation_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save_reputation(self) -> None:
        # prune expired + size
        now = time.time()
        pruned: dict[str, Any] = {}
        for key, entry in self._reputation.items():
            ts = float(entry.get("ts", 0))
            if now - ts <= self.reputation_ttl:
                pruned[key] = entry
        if len(pruned) > self.max_cache_entries:
            # keep newest
            items = sorted(pruned.items(), key=lambda kv: float(kv[1].get("ts", 0)), reverse=True)
            pruned = dict(items[: self.max_cache_entries])
        self._reputation = pruned
        self.reputation_path.write_text(
            json.dumps(self._reputation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_reputation(self, host: str) -> dict[str, Any] | None:
        entry = self._reputation.get(host.lower())
        if not entry:
            return None
        if time.time() - float(entry.get("ts", 0)) > self.reputation_ttl:
            return None
        return entry

    def set_reputation(self, host: str, *, score: int, category: str) -> None:
        self._reputation[host.lower()] = {
            "score": int(score),
            "category": category,
            "ts": time.time(),
        }

    @property
    def allowlist(self) -> set[str]:
        return {h.lower() for h in (self.data.get("allowlist_hosts") or [])}

    @property
    def blacklist(self) -> set[str]:
        return {h.lower() for h in (self.data.get("blacklist_hosts") or [])}

    @property
    def suspicious_tlds(self) -> set[str]:
        return {t.lower() for t in (self.data.get("suspicious_tlds") or [])}

    @property
    def dangerous_extensions(self) -> set[str]:
        return {e.lower() for e in (self.data.get("dangerous_extensions") or [])}

    def host_allowlisted(self, host: str) -> bool:
        h = host.lower().rstrip(".")
        if h in self.allowlist:
            return True
        return any(h == a or h.endswith("." + a) for a in self.allowlist)

    def host_blacklisted(self, host: str) -> bool:
        h = host.lower().rstrip(".")
        if h in self.blacklist:
            return True
        return any(h == b or h.endswith("." + b) for b in self.blacklist)

    def match_lookalike(self, text: str) -> list[str]:
        hits: list[str] = []
        for rx in self._lookalike_re:
            if rx.search(text):
                hits.append(rx.pattern)
        return hits

    def phishing_phrases(self) -> list[str]:
        en = list(self.data.get("phishing_phrases_en") or [])
        zh = list(self.data.get("phishing_phrases_zh") or [])
        return en + zh

    def status(self) -> dict[str, Any]:
        return {
            "signatures_version": self.data.get("version"),
            "blacklist_hosts": len(self.blacklist),
            "allowlist_hosts": len(self.allowlist),
            "reputation_entries": len(self._reputation),
            "cache_path": str(self.reputation_path),
        }
