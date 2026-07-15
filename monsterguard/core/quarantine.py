"""Quarantine adapter — prefers monster_ai.protection.quarantine when available."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SecurityQuarantine:
    """Local JSONL quarantine; delegates to protection.QuarantineZone if present."""

    def __init__(self, root: Path, protection_zone: Any | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "security_quarantine.jsonl"
        self._protection = protection_zone

    def isolate(
        self,
        *,
        target: str,
        reasons: list[str],
        score: int,
        category: str,
        source: str = "monsterguard_security",
    ) -> dict[str, Any]:
        if self._protection is not None:
            try:
                return self._protection.isolate(
                    ip=source,
                    path=target[:512],
                    reasons=reasons,
                    score=score,
                    body_preview=category,
                    action="security_block",
                )
            except Exception:  # noqa: BLE001
                pass

        entry = {
            "id": f"gsec-{int(time.time() * 1000)}",
            "target": target[:1024],
            "reasons": reasons,
            "score": score,
            "category": category,
            "source": source,
            "created_at": time.time(),
            "released": False,
            "hits": 1,
        }
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def list_active(self, limit: int = 20) -> list[dict[str, Any]]:
        if self._protection is not None and hasattr(self._protection, "list_active"):
            try:
                return self._protection.list_active(limit=limit)
            except Exception:  # noqa: BLE001
                pass
        entries: list[dict[str, Any]] = []
        if not self.index_path.is_file():
            return []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not e.get("released"):
                entries.append(e)
        return list(reversed(entries[-limit:]))

    def release(self, entry_id: str) -> dict[str, Any]:
        if self._protection is not None and hasattr(self._protection, "release"):
            try:
                return self._protection.release(entry_id)
            except Exception:  # noqa: BLE001
                pass
        if not self.index_path.is_file():
            return {"ok": False, "reason": "not_found"}
        lines = self.index_path.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        found = False
        for line in lines:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                out.append(line)
                continue
            if e.get("id") == entry_id:
                e["released"] = True
                e["released_at"] = time.time()
                found = True
            out.append(json.dumps(e, ensure_ascii=False))
        self.index_path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
        return {"ok": found, "id": entry_id}

    def status(self) -> dict[str, Any]:
        return {
            "active": len(self.list_active(limit=500)),
            "path": str(self.root),
            "backend": "protection" if self._protection else "local_jsonl",
        }
