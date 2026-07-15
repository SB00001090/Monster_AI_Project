# Monster_AI_Project — 目錄佈局對照

**Developed by Suckbob | Guardian Ai**

概念上的 Git 根目錄名稱可以是 **Monster_AI_Project**；本倉庫實際 clone 名稱可能是 `monster-ai` / `Guardian-Ai-ZH-TW`，**根目錄就是 Git root**（含 `.git/`）。

## 概念樹 → 實際路徑

| 概念（文件/簡報用） | 本倉庫實際路徑 | 說明 |
|---------------------|----------------|------|
| `Monster_AI_Project/` | 倉庫根目錄 | Git 根 |
| `monster_ai_file/` | **`monster_ai/`** | 生成、RP、平台 API、protection |
| `monster_ai_file/forum/` | `client/` + `server/`（tRPC） | 討論區在 Web 層，非 Python forum 包 |
| `monster_ai_file/main_monster_ai.py` | **`main.py`** / **`start_monster_ai.py`** | 啟動 FastAPI |
| `guardian_ai_file/` | **`guardian_ai/`** | Guardian 命名空間 + MonsterGuard 24/7 |
| `guardian_ai_file/monster_guard/` | **`guardian_ai/monster_guard/`** | 24/7 監控、封鎖、自修復 |
| `guardian_ai_file/security_modules/` | **`guardian_ai/other_security_modules/`** | 未來擴充 |
| `guardian_ai_file/config/` | **`guardian_ai/config/`** | `monster_guard_config.json` |
| `shared/` | **`shared/`** | TS + Python 共用輔助 |
| `docs/` | **`docs/`** + `deploy/guardian/` | 本文件 + 規格 |
| `start_monster_ai.py` | **`start_monster_ai.py`** | 入口 |
| `start_monster_guard.py` | **`start_monster_guard.py`** | 入口 |
| （掃描引擎） | **`monsterguard/`** | HTTP `/api/monsterguard/*` |
| （Guardian 平台） | **`monster_ai/modules/guardian/`** | E2E / 幼兒學習 / OC |

> **為什麼不整庫 rename 成 `*_file/`？**  
> 既有 import、測試、部署腳本全部綁定 `monster_ai.*`。硬改路徑會破壞 monorepo。  
> 概念名 `monster_ai_file` / `guardian_ai_file` 僅作產品分層用語；執行請用實際路徑。

## 相容別名套件（可選 import）

```python
import monster_ai_file          # → re-export monster_ai
import guardian_ai_file         # → re-export guardian_ai
from guardian_ai_file.monster_guard import MonsterGuardCore
```

## 啟動（建議日常用選單）

```bat
start.bat
```

| 選項 | 作用 |
|------|------|
| 1 | Monster AI（生成 + Web） |
| 2 | MonsterGuard 24/7 |
| 3 | Guard 狀態 |
| 4 | 整理總覽 `scripts/project_status.py` |
| 5 | 完整 `run.bat` |
| 6 | 開啟本文件 |

```bash
# 指令列等價
python start_monster_ai.py
python start_monster_guard.py
python start_monster_guard.py status
python scripts/project_status.py
run.bat
```

日常清單：[日常操作.md](日常操作.md)

## 雙引擎關係

```
start_monster_ai.py
    └── monster_ai (FastAPI)
            ├── modules/guardian   ← 平台（同步/學習）
            ├── monsterguard API   ← 掃描 HTTP
            └── Discord bot        ← 可委派掃描

start_monster_guard.py
    └── guardian_ai.monster_guard  ← 24/7 監控 + 自動封鎖 + 自修復
```

兩者可同時跑：AI 服務與守護服務分離進程，本地優先。

## GitHub Desktop

1. File → Add Local Repository → 選本倉庫根目錄  
2. 確認 `.gitignore` 已排除 `.env`、`config.yaml`、`data/*` 密文、`node_modules`  
3. 勿提交 `discord.token.local`、keystore、`.jks`

詳見根目錄 [README.md](../README.md) · [SECURITY_MODULE.md](../deploy/guardian/SECURITY_MODULE.md)
