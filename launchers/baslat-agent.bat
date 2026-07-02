@echo off
setlocal enabledelayedexpansion
title FULL Servis - Agent (Windows)

REM =====================================================================
REM  BU MAKINEYE OZEL AYARLAR  (yalnizca BIR KEZ duzenle)
REM =====================================================================
REM  NODE_ID     : bu makinenin kimligi (win_wifi)
REM  SERVER_URL  : Linux sunucunun adresi
REM  REPO_DIR    : fullservice_automation klasorunun TAM yolu
REM  AGENT_PORT  : agent'in dinledigi port (varsayilan 7531)
set "NODE_ID=win_wifi"
set "SERVER_URL=http://192.168.1.10:8770"
set "REPO_DIR=%USERPROFILE%\Desktop\aliimran\fullservice_automation"
set "AGENT_PORT=7531"
REM =====================================================================
REM  NOT: Bu dosya git pull YAPMAZ. Kod guncellemesi USB ile REPO_DIR'e
REM       elle kopyalanir; bu dosya sadece eskisini durdurup yenisini baslatir.
REM =====================================================================

cd /d "%REPO_DIR%" || (echo Repo klasoru bulunamadi: %REPO_DIR% & pause & exit /b 1)

echo.
echo [1/2] Calisan eski agent kapatiliyor (port %AGENT_PORT%)...
for /f "tokens=5" %%P in ('netstat -aon ^| findstr ":%AGENT_PORT% " ^| findstr LISTENING') do (
    taskkill /F /PID %%P >nul 2>&1
)

echo.
echo [2/2] Agent baslatiliyor: %NODE_ID%  ->  %SERVER_URL%
cd fullservice-backend
call venv\Scripts\activate.bat
python run_agent.py %NODE_ID% %SERVER_URL%

echo.
echo Agent durdu. Bu pencereyi kapatabilirsiniz.
pause >nul
