#!/usr/bin/env python3
"""Project layout + health check — 方便整理、確認仍可運作。

Usage:
  python scripts/project_status.py
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 概念名 → 實際路徑（給人看的整理表）
MAP = [
    ("Git 根目錄 (Monster_AI_Project)", "."),
    ("Monster AI 主項目 (monster_ai_file)", "monster_ai/"),
    ("Guardian + Guard (guardian_ai_file)", "guardian_ai/"),
    ("MonsterGuard 24/7", "guardian_ai/monster_guard/"),
    ("HTTP 掃描引擎", "monsterguard/"),
    ("Guardian 平台 (同步/學習)", "monster_ai/modules/guardian/"),
    ("討論區 Web", "client/ + server/"),
    ("啟動 AI", "start_monster_ai.py"),
    ("啟動 Guard", "start_monster_guard.py"),
    ("一鍵選單", "start.bat"),
    ("佈局文件", "docs/PROJECT_LAYOUT.md"),
    ("安全規格", "deploy/guardian/SECURITY_MODULE.md"),
]


def _ok(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK " if cond else "!! "
    extra = f"  — {detail}" if detail else ""
    print(f"  [{mark}] {label}{extra}")


def main() -> int:
    print()
    print("=" * 56)
    print(" Monster AI Project · 整理總覽 / 運作檢查")
    print(" Developed by Suckbob | Guardian Ai")
    print("=" * 56)
    print(f"\n根目錄: {ROOT}\n")

    print("【概念 ↔ 實際路徑】")
    for concept, path in MAP:
        p = ROOT / path.split("+")[0].strip().rstrip("/")
        exists = p.exists() if not path.endswith("/") or True else (ROOT / path.rstrip("/")).exists()
        # handle compound paths
        if "+" in path:
            parts = [ROOT / x.strip().rstrip("/") for x in path.split("+")]
            exists = all(x.exists() for x in parts)
            loc = path
        else:
            loc = path
            exists = (ROOT / path.rstrip("/")).exists() if path != "." else True
        mark = "✓" if exists else "✗"
        print(f"  {mark} {concept}")
        print(f"      → {loc}")

    print("\n【關鍵檔案】")
    for rel in (
        "start_monster_ai.py",
        "start_monster_guard.py",
        "start.bat",
        "main.py",
        "run.bat",
        "config.example.yaml",
        "guardian_ai/config/monster_guard_config.json",
        "guardian_ai/monster_guard/main_monster_guard.py",
        "monsterguard/service.py",
        "requirements.txt",
        ".gitignore",
    ):
        _ok(rel, (ROOT / rel).is_file())

    print("\n【Python import 健康】")
    sys.path.insert(0, str(ROOT))
    checks = [
        ("monster_ai.config", "load_settings"),
        ("guardian_ai.monster_guard", "MonsterGuardCore"),
        ("monsterguard.service", "MonsterGuardService"),
        ("monster_ai_file", None),
        ("guardian_ai_file", None),
    ]
    for mod_name, attr in checks:
        try:
            mod = importlib.import_module(mod_name)
            if attr and not hasattr(mod, attr):
                _ok(mod_name, False, f"缺 {attr}")
            else:
                _ok(mod_name, True)
        except Exception as exc:  # noqa: BLE001
            _ok(mod_name, False, str(exc)[:80])

    print("\n【MonsterGuard 狀態快照】")
    try:
        from guardian_ai.monster_guard.service import MonsterGuardCore

        st = MonsterGuardCore().status()
        print(f"  product     : {st.get('product')}")
        print(f"  package     : {st.get('package')}")
        print(f"  enabled     : {st.get('enabled')}")
        print(f"  level       : {st.get('security_level')}")
        print(f"  runtime_dir : {st.get('runtime_dir')}")
    except Exception as exc:  # noqa: BLE001
        print(f"  !! 無法載入: {exc}")

    print("\n【建議日常操作】")
    print("  1. 雙擊 start.bat 選服務（最省事）")
    print("  2. 只改業務碼：monster_ai/ 或 guardian_ai/monster_guard/")
    print("  3. 勿動/勿提交：config.yaml · .env · data/ · *.token.local")
    print("  4. 路徑對照：docs/PROJECT_LAYOUT.md")
    print("  5. 兩個進程可並跑：AI (7860) + Guard (背景)")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
