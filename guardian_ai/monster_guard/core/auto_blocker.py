"""Automatic block list + warn/block decisions for MonsterGuard."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class AutoBlocker:
    def __init__(
        self,
        blocked_list_path: Path,
        *,
        block_threshold: int = 70,
        warn_threshold: int = 50,
        auto_block: bool = True,
    ) -> None:
        self.path = Path(blocked_list_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.block_threshold = block_threshold
        self.warn_threshold = warn_threshold
        self.auto_block = auto_block
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"version": 1, "updated_at": None, "hosts": [], "users": [], "urls": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"version": 1, "updated_at": None, "hosts": [], "users": [], "urls": []}

    def save(self) -> None:
        self.data["updated_at"] = time.time()
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def decide(self, score: int) -> str:
        """Return allow | warn | block."""
        if score >= self.block_threshold:
            return "block"
        if score >= self.warn_threshold:
            return "warn"
        return "allow"

    def is_blocked_host(self, host: str) -> bool:
        h = (host or "").lower().strip()
        return any(e.get("value") == h for e in self.data.get("hosts") or [])

    def is_blocked_url(self, url: str) -> bool:
        u = (url or "").strip()
        return any(e.get("value") == u for e in self.data.get("urls") or [])

    def block_host(self, host: str, *, reason: str = "", score: int = 0) -> dict[str, Any]:
        if not self.auto_block:
            return {"ok": False, "reason": "auto_block_disabled"}
        h = host.lower().strip()
        if not h:
            return {"ok": False, "reason": "empty_host"}
        if self.is_blocked_host(h):
            return {"ok": True, "already": True, "value": h}
        entry = {
            "value": h,
            "reason": reason,
            "score": score,
            "ts": time.time(),
        }
        self.data.setdefault("hosts", []).append(entry)
        self.save()
        return {"ok": True, "value": h, "entry": entry}

    def block_url(self, url: str, *, reason: str = "", score: int = 0) -> dict[str, Any]:
        if not self.auto_block:
            return {"ok": False, "reason": "auto_block_disabled"}
        u = url.strip()
        if not u:
            return {"ok": False, "reason": "empty_url"}
        if self.is_blocked_url(u):
            return {"ok": True, "already": True, "value": u}
        entry = {"value": u, "reason": reason, "score": score, "ts": time.time()}
        self.data.setdefault("urls", []).append(entry)
        self.save()
        return {"ok": True, "value": u, "entry": entry}

    def apply_scan(self, scan: dict[str, Any]) -> dict[str, Any]:
        score = int(scan.get("score") or 0)
        action = self.decide(score)
        out: dict[str, Any] = {
            "action": action,
            "score": score,
            "blocked": False,
        }
        if action != "block":
            return out
        # Prefer host from findings/target
        target = ""
        findings = scan.get("findings") or []
        if findings:
            target = str(findings[0].get("target") or "")
        if not target and scan.get("reasons"):
            target = str(scan["reasons"][0])
        if target.startswith("http") or "." in target:
            # crude host extract
            host = target
            if "://" in target:
                try:
                    from urllib.parse import urlparse

                    host = urlparse(target).hostname or target
                except Exception:  # noqa: BLE001
                    host = target
            r = self.block_host(host, reason=",".join(scan.get("reasons") or [])[:200], score=score)
            if r.get("ok"):
                out["blocked"] = True
                out["block_result"] = r
            else:
                r2 = self.block_url(target, reason=str(scan.get("category")), score=score)
                out["blocked"] = bool(r2.get("ok"))
                out["block_result"] = r2
        return out

    def status(self) -> dict[str, Any]:
        return {
            "auto_block": self.auto_block,
            "block_threshold": self.block_threshold,
            "warn_threshold": self.warn_threshold,
            "hosts": len(self.data.get("hosts") or []),
            "urls": len(self.data.get("urls") or []),
            "users": len(self.data.get("users") or []),
            "path": str(self.path),
        }
