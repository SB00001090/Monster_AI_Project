@echo off
REM Monster AI 訪客試玩版 — 一鍵建置
REM 開發者：Suckbob | 發行商：Monster_Ai_hk
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo  Monster AI 訪客試玩版  APK 建置
echo  開發者：Suckbob  發行商：Monster_Ai_hk
echo  包名：com.monster_ai_hk.guest
echo  版本：1.0.0-guest
echo ============================================

REM 自動偵測 JAVA_HOME（Android Studio JBR）
if not defined JAVA_HOME (
  if exist "C:\Program Files\Android\Android Studio\jbr\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
  ) else if exist "%LOCALAPPDATA%\Programs\Android\Android Studio\jbr\bin\java.exe" (
    set "JAVA_HOME=%LOCALAPPDATA%\Programs\Android\Android Studio\jbr"
  )
)
if defined JAVA_HOME set "PATH=%JAVA_HOME%\bin;%PATH%"

REM 自動寫入 local.properties（若尚未存在）
if not exist "local.properties" (
  if defined ANDROID_HOME (
    echo sdk.dir=%ANDROID_HOME:\=\\%> local.properties
    echo [OK] 已由 ANDROID_HOME 產生 local.properties
  ) else if defined ANDROID_SDK_ROOT (
    echo sdk.dir=%ANDROID_SDK_ROOT:\=\\%> local.properties
    echo [OK] 已由 ANDROID_SDK_ROOT 產生 local.properties
  ) else if exist "%LOCALAPPDATA%\Android\Sdk" (
    powershell -NoProfile -Command "$p=Join-Path $env:LOCALAPPDATA 'Android\Sdk'; $esc=$p -replace '\\','\\'; Set-Content -Path 'local.properties' -Value ('sdk.dir='+$esc) -Encoding ASCII"
    echo [OK] 已偵測 %%LOCALAPPDATA%%\Android\Sdk
  ) else (
    echo [ERROR] 找不到 Android SDK。請設定 ANDROID_HOME 或建立 local.properties
    echo 範例見 local.properties.example
    exit /b 1
  )
)

REM 若本目錄無 gradle wrapper，嘗試從 guardian 專案複製
if not exist "gradlew.bat" (
  if exist "..\guardian-ai-android\gradlew.bat" (
    echo [INFO] 複製 Gradle Wrapper 自 guardian-ai-android ...
    copy /Y "..\guardian-ai-android\gradlew.bat" "gradlew.bat" >nul
    if exist "..\guardian-ai-android\gradlew" copy /Y "..\guardian-ai-android\gradlew" "gradlew" >nul
    if not exist "gradle\wrapper" mkdir "gradle\wrapper"
    if exist "..\guardian-ai-android\gradle\wrapper\gradle-wrapper.jar" (
      copy /Y "..\guardian-ai-android\gradle\wrapper\gradle-wrapper.jar" "gradle\wrapper\gradle-wrapper.jar" >nul
    )
  )
)

if not exist "gradlew.bat" (
  echo [ERROR] 缺少 gradlew.bat。請安裝 Gradle 或複製 wrapper。
  exit /b 1
)

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=debug

if /I "%BUILD_TYPE%"=="release" (
  echo [BUILD] assembleRelease ...
  call gradlew.bat --no-daemon clean assembleRelease
) else (
  echo [BUILD] assembleDebug ...
  call gradlew.bat --no-daemon clean assembleDebug
)

if errorlevel 1 (
  echo [FAIL] 建置失敗
  exit /b 1
)

set OUT_DIR=..\..\dist
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

if /I "%BUILD_TYPE%"=="release" (
  set APK_SRC=app\build\outputs\apk\release\app-release.apk
  set APK_DST=%OUT_DIR%\MonsterAi-Guest-1.0.0-guest-release.apk
  if not exist "%APK_SRC%" (
    REM 未簽名時檔名可能不同
    set APK_SRC=app\build\outputs\apk\release\app-release-unsigned.apk
  )
) else (
  set APK_SRC=app\build\outputs\apk\debug\app-debug.apk
  set APK_DST=%OUT_DIR%\MonsterAi-Guest-1.0.0-guest-debug.apk
)

if exist "%APK_SRC%" (
  copy /Y "%APK_SRC%" "%APK_DST%" >nul
  echo.
  echo [SUCCESS] APK 已輸出：
  echo   原始：%CD%\%APK_SRC%
  echo   副本：%CD%\%APK_DST%
) else (
  echo [WARN] 建置成功但找不到 APK，請檢查 app\build\outputs\apk\
  dir /s /b app\build\outputs\apk\*.apk 2>nul
)

echo.
echo 完成。訪客限制：每日 30 分、僅 3 角色、無存檔/付費/帳號。
endlocal
