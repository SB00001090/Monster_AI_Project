# Monster AI 訪客免費公測版 APK — 完整建置說明

**應用名稱：** Monster AI 公測  
**包名 / appId：** `com.monster_ai_hk.monsterai`  
**版本：** `1.0.0-public-beta`  
**開發者：** suckbob  
**發行商 / Publisher：** Monster_Ai_hk  
**最低 SDK：** Android 8.0（API 26）  
**目標 SDK：** Android 14（API 34）

---

## A. 目錄結構

```
monster-ai/                          # monorepo 根
├── capacitor.config.ts             # appId / appName / webDir
├── .env.public-beta.example
├── client/src/
│   ├── contexts/GuestContext.tsx   # 訪客 + 每日額度 + 鎖定模組
│   ├── components/
│   │   ├── PublicBetaChrome.tsx    # 標籤 / 水印 / Bug 回報 FAB
│   │   ├── BetaUpgradePrompt.tsx
│   │   └── BugReportModal.tsx      # 既有一鍵回報
│   ├── App.tsx                     # 自動訪客 + PublicBetaChrome
│   ├── components/DashboardLayout.tsx
│   └── pages/（Chat / Image 額度攔截）
└── apps/monster-ai-android/
    ├── 公測APK建置說明.md           # 本檔
    ├── build-public-beta-apk.bat    # 一鍵建置
    ├── gen-beta-keystore.bat
    └── android/                    # Android Studio 專案
        ├── app/build.gradle.kts    # signing + productFlavors
        ├── app/src/main/
        │   ├── AndroidManifest.xml
        │   └── java/.../MainActivity.kt
        ├── keystore.properties.example
        └── keystore/
```

> 也可在 monorepo 根執行 `npx cap add android`，把官方 Capacitor `android/` 與本專案對齊。

---

## B. capacitor.config.ts 要點

| 欄位 | 值 |
|------|-----|
| appId | `com.monster_ai_hk.monsterai` |
| appName | `Monster AI 公測` |
| webDir | `dist/public`（對應 Vite `build.outDir`） |
| androidScheme | `https` |
| Splash 背景 | `#0B0F1A`（Neon） |

完整內容見倉庫根 `capacitor.config.ts`。

---

## C. 訪客公測限制（Web GuestContext）

| 項目 | 限制 |
|------|------|
| 登入 | 開啟即訪客，無需登入 |
| 每日 RP 對話 | **50** 次 |
| 每日圖像生成 | **10** 次 |
| 完整 Guardian / 本地 LLM 全功能 / 網路學習等 | **鎖定** + 升級提示 |
| 水印 | 右下角半透明「公測訪客｜Monster_Ai_hk」 |
| 標籤 | 「公測版 · 訪客免費」 |
| Bug 回報 | 右下 FAB → `BugReportModal` |

額度 key：`monster_beta_day` / `monster_beta_rp_used` / `monster_beta_image_used`（按日重置）。

---

## D. 一鍵建置（Windows）

```bat
cd C:\Monster\monster-ai
apps\monster-ai-android\build-public-beta-apk.bat
```

Release（需 keystore）：

```bat
apps\monster-ai-android\gen-beta-keystore.bat
REM 編輯 apps\monster-ai-android\android\keystore.properties
apps\monster-ai-android\build-public-beta-apk.bat release
```

### 手動步驟

```bat
REM 1. 公測環境變數
set VITE_PUBLIC_BETA=true
set VITE_FORCE_GUEST=true

REM 2. 前端
pnpm install
pnpm build

REM 3. Capacitor（建議）
pnpm add @capacitor/core @capacitor/cli @capacitor/android
npx cap add android
npx cap sync android

REM 4. 或使用 apps 內原生殼
xcopy /E /I /Y dist\public\* apps\monster-ai-android\android\app\src\main\assets\public\

REM 5. Gradle
cd apps\monster-ai-android\android
gradlew.bat assemblePublicBetaDebug
```

### Android Studio

1. **File → Open** → `apps/monster-ai-android/android`
2. 等待 Gradle Sync
3. Build Variant：`publicBetaDebug` 或 `publicBetaRelease`
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**

---

## E. APK 輸出路徑

| Flavor / Type | 路徑 |
|---------------|------|
| publicBeta Debug | `apps/monster-ai-android/android/app/build/outputs/apk/publicBeta/debug/app-publicBeta-debug.apk` |
| publicBeta Release（已簽名） | `.../publicBeta/release/app-publicBeta-release.apk` |
| 一鍵副本 | `dist/MonsterAI-PublicBeta-1.0.0-debug.apk` |

Debug applicationId：`com.monster_ai_hk.monsterai.debug`  
Release applicationId：`com.monster_ai_hk.monsterai`

---

## F. 安裝與測試

```bat
adb devices
adb install -r dist\MonsterAI-PublicBeta-1.0.0-debug.apk
adb logcat | findstr /i monster
```

### 手動回歸

1. 開啟 App → **無需登入**，見「公測版 · 訪客免費」  
2. 右下角水印 + Bug 回報按鈕  
3. RP 對話：額度從 50 遞減；用盡 toast  
4. 圖像：額度 10；用盡 toast  
5. 側欄點「Guardian / LLM / 網路學習」→ 鎖定升級對話框  
6. Bug 回報可開 modal（後端在線時可送出）  
7. 清 App 資料後額度重置  

---

## G. 簽名（Release）

```bat
apps\monster-ai-android\gen-beta-keystore.bat
```

```properties
# android/keystore.properties
storeFile=keystore/monster-ai-public-beta.jks
storePassword=你的密碼
keyAlias=monster_ai_beta
keyPassword=你的密碼
```

```bat
gradlew.bat assemblePublicBetaRelease
```

---

## H. Google Play 內部測試 / 公測注意事項（簡短）

1. **Play Console → 測試 → 內部測試** 上傳 AAB 更佳（`bundlePublicBetaRelease`）  
2. 包名 `com.monster_ai_hk.monsterai` 必須全域唯一且終身固定  
3. 內容分級、隱私權政策 URL、資料安全表單必填  
4. 公測文案明確「訪客免費、功能受限」；避免暗示無限制 NSFW 上架風險  
5. 使用 **內部測試軌道** 邀請 email 清單；通過後再開放封閉式公測  
6. keystore 離線備份；遺失無法更新同一 appId  
7. 若另有 `ai.guardian.app` / `com.monster_ai_hk.guest` 可並存，勿混簽  

---

## I. 潛在 bug 清單

1. 額度先扣再送 API：網路失敗仍消耗 1 次（可改為成功後再扣）  
2. 僅 localStorage：清資料 / 換裝置額度重置  
3. Capacitor 未 sync 時只見 fallback HTML  
4. cleartext 開啟：僅建議內測，上架可收斂  
5. 鎖定路由若深連結直接進 URL 可能短暫看到頁面（可加 route guard）  
6. Bug 回報依 tRPC；離線僅 toast 失敗  
7. debug / release 包名不同，可同時安裝  
8. WebView 與 BridgeActivity 切換後需重測插件權限  

---

## J. 開發者 / 發行商

- **Developer：** suckbob  
- **Publisher / Issuer：** Monster_Ai_hk  
- **產品：** Monster AI 訪客免費公測 APK  

— 與 `apps/monster-ai-guest`（純原生試玩）可並存；本專案為 **Capacitor + 完整 client 公測殼**。
