"""URL reputation check — local cache + signature allow/block lists."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from monsterguard.core.signatures import SignatureStore
from monsterguard.core.url_scanner import UrlScanner


class UrlReputation:
    def __init__(
        self,
        *,
        signatures: SignatureStore | None = None,
        runtime_dir: Path | None = None,
        ttl_hours: float = 24.0,
    ) -> None:
        root = Path(__file__).resolve().parents[3]  # repo-ish: guardian_ai parent = repo
        # Prefer monorepo root (guardian_ai/monster_guard/core -> parents[3] = repo)
        repo = Path(__file__).resolve().parents[3]
        sig_path = repo / "monsterguard" / "database" / "threat_signatures.json"
        cache = Path(runtime_dir or (repo / "data" / "monster_guard"))
        cache.mkdir(parents=True, exist_ok=True)
        self.signatures = signatures or SignatureStore(
            sig_path if sig_path.is_file() else repo / "guardian_ai" / "monster_guard" / "database" / "scam_patterns.json",
            cache,
            reputation_ttl_hours=ttl_hours,
        )
        # If we pointed at scam_patterns by mistake, reload signatures when available
        if sig_path.is_file() and signatures is None:
            self.signatures = SignatureStore(sig_path, cache, reputation_ttl_hours=ttl_hours)
        self.scanner = UrlScanner(self.signatures)
        self.runtime_dir = cache
        self.log_path = cache / "url_reputation_log.jsonl"

    def check(self, url: str, *, security_level: str = "medium") -> dict[str, Any]:
        result = self.scanner.scan([url], security_level=security_level)
        host = self.scanner.normalize_host(url)
        payload = {
            "url": url,
            "host": host,
            "score": result.score,
            "category": result.category,
            "block": result.block,
            "reasons": result.reasons,
            "ts": time.time(),
        }
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            pass
        self.signatures.save_reputation()
        return payload

    def check_many(self, urls: list[str], *, security_level: str = "medium") -> dict[str, Any]:
        result = self.scanner.scan(urls, security_level=security_level)
        return result.to_dict()

    def status(self) -> dict[str, Any]:
        return {
            "engine": "url_reputation",
            "signatures": self.signatures.status(),
            "runtime_dir": str(self.runtime_dir),
        }
