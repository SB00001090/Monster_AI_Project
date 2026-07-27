# Monster AI 完整加速開發包

**發行商：** Monster_Ai_hk  
**開發者：** suckbob  

## 核心行為

| 項目 | 狀態 |
|------|------|
| 無限額 | `unlimited_mode: true` + 前端 `UNLIMITED_MODE` |
| 無審查 RP | `uncensored: true`（仍禁未成年/真實犯罪） |
| 自癒 | `self_healing` 預設開，45s / 3 次 / fallback |
| 情緒自學 | TW + HK 口語 → 注入 LLM 自行生成對話 |
| 即時回報 | `/api/accel/feedback` + Webhook |
| 自動更新 | `/api/accel/update/check` → GitHub Release |
| 50 UI 主題 | 設定 → 介面 |
| 藍玫瑰和籠子 | 關於頁版本號連點 7 次 |
| 手勢 | 設定 → 手勢操作 |

## 後端檔案

- `monster_ai/learning/emotion_analyzer.py`
- `monster_ai/core/self_healing.py`
- `monster_ai/api/accel.py`
- `monster_ai/config.py`（新區塊）
- `config.yaml` / `config.example.yaml`

## 前端檔案

- `client/src/lib/themes/uiThemeCatalog.ts`
- `client/src/contexts/UiThemeContext.tsx`
- `client/src/contexts/GestureContext.tsx`
- `client/src/components/themes/*`
- `client/src/components/gestures/GestureLayer.tsx`
- `client/src/components/feedback/InstantFeedbackModal.tsx`
- `client/src/components/AccelShell.tsx`
- `client/src/hooks/useAutoUpdate.ts`

## API

```
GET  /api/accel/status
POST /api/accel/emotion/analyze
GET  /api/accel/emotion/recent
GET  /api/accel/healing/status
POST /api/accel/feedback
GET  /api/accel/update/check
```

## 快速驗證

```bash
# 情緒
curl -X POST http://127.0.0.1:7860/api/accel/emotion/analyze -H "Content-Type: application/json" -d "{\"text\":\"好攰呀，點算\"}"

# 狀態
curl http://127.0.0.1:7860/api/accel/status
```

## 已修 bug（delBug）

1. ~~soft_reply 洩漏 debug~~ → 僅日誌保留錯誤
2. ~~「好攰呀點算」誤判焦慮~~ → 疲累優先 + 片語權重
3. ~~極短句誤判~~ → ≤2 字無命中→中性
4. ~~GitHub rate limit 無 UA~~ → 加上 User-Agent
5. ~~主題 CSS 映射不全~~ → 補齊 shadcn 變數 + body 背景
6. ~~長按選單未掛聊天~~ → ChatPage MessageLongPress
7. ~~截圖回報完全空~~ → SVG 快照 fallback
8. 藍玫瑰仍僅 localStorage（可接受）
