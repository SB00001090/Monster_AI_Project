# MonsterGuard 安全模組架構

**Developed by Suckbob | Guardian Ai**

## 雙產品命名（強制）

| 產品 | 職責 | 路徑 | API / 入口 |
|------|------|------|------------|
| **Guardian 平台** | E2E 同步、幼兒教育式學習、OC 反抄襲 | `monster_ai/modules/guardian/` | `/api/guardian/*` |
| **MonsterGuard 掃描引擎** | URL/釣魚/分類（供 HTTP + bot 共用） | `monsterguard/` | `/api/monsterguard/*` |
| **MonsterGuard 24/7 核心** | 實時監控、自動封鎖、自修復 | `guardian_ai/monster_guard/` | `python run_monster_guard.py` |
| **Discord Bot 管線** | 伺服器訊息攔截 | `monster_ai/modules/discord/guard/` | 委派掃描引擎 |

**不會**用安全模組審查本地 NSFW RP / 圖像生成。

## 目錄（概念 `MonsterAI_Project` → 本 monorepo）

```
guardian_ai/
├── monster_guard/                 # 24/7 核心服務
│   ├── core/
│   │   ├── discord_scam_detector.py
│   │   ├── url_reputation.py
│   │   ├── real_time_monitor.py
│   │   ├── auto_blocker.py
│   │   ├── service_runner.py
│   │   └── self_repair.py
│   ├── database/
│   │   ├── scam_patterns.json
│   │   └── blocked_list.json
│   ├── reports/                   # 執行期日誌見 data/monster_guard/
│   ├── service.py                 # MonsterGuardCore
│   └── main_monster_guard.py
├── other_security_modules/        # 未來擴充
└── config/
    └── monster_guard_config.json

monsterguard/                      # HTTP 掃描引擎（共用）
run_monster_guard.py               # 24/7 入口
```

## 24/7 啟動

```bash
python run_monster_guard.py
# 或
python -m guardian_ai.monster_guard.main_monster_guard run
python run_monster_guard.py status
python run_monster_guard.py scan-discord "free nitro"
```

設定：`guardian_ai/config/monster_guard_config.json`  
執行期：`data/monster_guard/`（gitignore）

## HTTP 掃描（既有）

```yaml
monsterguard:
  enabled: true
  security_level: medium
  cache_dir: "./data/monsterguard"
```

```bash
pytest tests/test_monsterguard_*.py tests/test_monster_guard_core.py -q
```
