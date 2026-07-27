@echo off
REM ============================================================
REM Monster AI 公測訪客版 — 一鍵建置 APK
REM 開發者：suckbob | 發行商：Monster_Ai_hk
REM appId: com.monster_ai_hk.monsterai
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0\..\.."

echo [1/5] 環境檢查...
if not defined JAVA_HOME (
  if exist "C:\Program Files\Android\Android Studio\jbr\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
  )
)
if defined JAVA_HOME set "PATH=%JAVA_HOME%\bin;%PATH%"

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=debug

echo [2/5] Web 建置（Vite → dist/public）+ 公測旗標...
set VITE_PUBLIC_BETA=true
set VITE_FORCE_GUEST=true
call pnpm build
if errorlevel 1 (
  echo [WARN] pnpm build 失敗，嘗試 npx vite build...
  call npx vite build
  if errorlevel 1 (
    echo [ERROR] 前端建置失敗
    exit /b 1
  )
)

echo [3/5] Capacitor sync（若已安裝 @capacitor/android）...
if exist "node_modules\@capacitor\android" (
  if not exist "android" (
    echo [INFO] 首次：cap add android...
    call npx cap add android
  )
  call npx cap sync android
) else (
  echo [WARN] 未安裝 @capacitor/android，改用 apps\monster-ai-android 原生殼
  echo        請執行: pnpm add -D @capacitor/android @capacitor/cli @capacitor/core
)

echo [4/5] 同步 web 資產到公測專案 assets...
set ASSET_DIR=apps\monster-ai-android\android\app\src\main\assets\public
if not exist "%ASSET_DIR%" mkdir "%ASSET_DIR%"
if exist "dist\public" (
  xcopy /E /I /Y "dist\public\*" "%ASSET_DIR%\" >nul
  echo [OK] 已複製 dist\public → %ASSET_DIR%
) else (
  echo [WARN] 找不到 dist\public，APK 將顯示 fallback 頁
)

REM local.properties
set AND_DIR=apps\monster-ai-android\android
if not exist "%AND_DIR%\local.properties" (
  if exist "%LOCALAPPDATA%\Android\Sdk" (
    powershell -NoProfile -Command "$p=Join-Path $env:LOCALAPPDATA 'Android\Sdk'; $esc=$p -replace '\\','\\'; Set-Content -Path '%AND_DIR%\local.properties' -Value ('sdk.dir='+$esc) -Encoding ASCII"
  )
)

REM gradle wrapper
if not exist "%AND_DIR%\gradlew.bat" (
  if exist "apps\guardian-ai-android\gradlew.bat" (
    copy /Y "apps\guardian-ai-android\gradlew.bat" "%AND_DIR%\gradlew.bat" >nul
    copy /Y "apps\guardian-ai-android\gradle\wrapper\gradle-wrapper.jar" "%AND_DIR%\gradle\wrapper\gradle-wrapper.jar" >nul
  )
  if exist "apps\monster-ai-guest\gradlew.bat" (
    copy /Y "apps\monster-ai-guest\gradlew.bat" "%AND_DIR%\gradlew.bat" >nul
    copy /Y "apps\monster-ai-guest\gradle\wrapper\gradle-wrapper.jar" "%AND_DIR%\gradle\wrapper\gradle-wrapper.jar" >nul
  )
)

echo [5/5] Gradle assemble publicBeta%BUILD_TYPE% ...
pushd "%AND_DIR%"
if /I "%BUILD_TYPE%"=="release" (
  call gradlew.bat --no-daemon assemblePublicBetaRelease
) else (
  call gradlew.bat --no-daemon assemblePublicBetaDebug
)
set ERR=%ERRORLEVEL%
popd

if not "%ERR%"=="0" (
  echo [FAIL] Gradle 建置失敗 code=%ERR%
  exit /b %ERR%
)

if not exist "dist" mkdir dist
if /I "%BUILD_TYPE%"=="release" (
  set APK_SRC=%AND_DIR%\app\build\outputs\apk\publicBeta\release\app-publicBeta-release.apk
  set APK_DST=dist\MonsterAI-PublicBeta-1.0.0-release.apk
) else (
  set APK_SRC=%AND_DIR%\app\build\outputs\apk\publicBeta\debug\app-publicBeta-debug.apk
  set APK_DST=dist\MonsterAI-PublicBeta-1.0.0-debug.apk
)

if exist "%APK_SRC%" (
  copy /Y "%APK_SRC%" "%APK_DST%" >nul
  echo.
  echo ========== 建置成功 ==========
  echo APK: %APK_SRC%
  echo 副本: %APK_DST%
  echo 包名: com.monster_ai_hk.monsterai  ^(debug 另加 .debug^)
  echo 安裝: adb install -r %APK_DST%
) else (
  echo [WARN] 找不到輸出 APK，請檢查:
  dir /s /b "%AND_DIR%\app\build\outputs\apk\*.apk" 2>nul
)

endlocal
