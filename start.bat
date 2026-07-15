@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Monster AI Project · 啟動選單

:menu
cls
echo.
echo  ========================================
echo   Monster AI Project · 本地啟動選單
echo   Developed by Suckbob ^| Guardian Ai
echo  ========================================
echo.
echo   [1] 啟動 Monster AI（生成 + Web :7860）
echo       → start_monster_ai.py / 等同 run.bat 核心
echo.
echo   [2] 啟動 MonsterGuard 24/7 守護
echo       → start_monster_guard.py
echo.
echo   [3] MonsterGuard 狀態（不長跑）
echo.
echo   [4] 專案整理總覽（路徑對照 + 健康檢查）
echo.
echo   [5] 完整一鍵 run.bat（ComfyUI + UI 安裝流）
echo.
echo   [6] 開啟文件：docs\PROJECT_LAYOUT.md
echo.
echo   [0] 離開
echo.
set /p choice=請選 0-6: 

if "%choice%"=="1" goto ai
if "%choice%"=="2" goto guard
if "%choice%"=="3" goto guard_status
if "%choice%"=="4" goto status
if "%choice%"=="5" goto full
if "%choice%"=="6" goto docs
if "%choice%"=="0" exit /b 0
echo 無效選項
timeout /t 2 >nul
goto menu

:ai
echo.
echo 啟動 Monster AI ...
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python start_monster_ai.py
pause
goto menu

:guard
echo.
echo 啟動 MonsterGuard 24/7（Ctrl+C 停止）...
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python start_monster_guard.py
pause
goto menu

:guard_status
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python start_monster_guard.py status
pause
goto menu

:status
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python scripts\project_status.py
pause
goto menu

:full
call run.bat
goto menu

:docs
start "" "%~dp0docs\PROJECT_LAYOUT.md"
goto menu
