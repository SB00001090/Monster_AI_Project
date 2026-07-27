@echo off
REM 產生 Monster AI 公測 release keystore
REM 開發者：suckbob | 發行商：Monster_Ai_hk
setlocal
cd /d "%~dp0\android"
if not exist keystore mkdir keystore

echo 將互動輸入密碼；建議別名 monster_ai_beta
keytool -genkeypair -v ^
  -keystore keystore\monster-ai-public-beta.jks ^
  -alias monster_ai_beta ^
  -keyalg RSA -keysize 2048 -validity 10000 ^
  -dname "CN=Monster AI Public Beta, OU=Monster_Ai_hk, O=Monster_Ai_hk, L=HK, ST=HK, C=HK"

if errorlevel 1 (
  echo [ERROR] keytool 失敗，請確認 JAVA_HOME
  exit /b 1
)

if not exist keystore.properties (
  copy /Y keystore.properties.example keystore.properties >nul
  echo 已複製 keystore.properties.example → keystore.properties
  echo 請編輯填入密碼後再 assemblePublicBetaRelease
)

echo [OK] keystore\monster-ai-public-beta.jks
endlocal
