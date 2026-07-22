@echo off
REM ============================================================================
REM  FULL Servis — WINDOWS AGENT uygulamasini derler (gelistirici calistirir)
REM
REM  Ciktisi:  cikti\FULLSERVIS-WINDOWS-WIFI\
REM              FULLSERVIS-WINDOWS-WIFI.exe   <- son kullanici buna cift tiklar
REM              ayarlar\config.json           <- topoloji/IP (disaridan degistirilebilir)
REM
REM  Bu klasoru oldugu gibi USB ile Windows (Wi-Fi) makinesine kopyalayin.
REM  Calistirma: bu dosyaya cift tiklayin ya da  derle-windows.bat
REM ============================================================================
setlocal
cd /d "%~dp0"

set "REPO=%~dp0..\.."
set "PY=%REPO%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo [1/4] Bagimliliklar kontrol ediliyor...
"%PY%" -m pip install --quiet --disable-pip-version-check -r "%REPO%\fullservice-backend\requirements.txt" || goto :hata
"%PY%" -m pip install --quiet --disable-pip-version-check pyinstaller || goto :hata

echo [2/4] Eski cikti temizleniyor...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "cikti\FULLSERVIS-WINDOWS-WIFI" rmdir /s /q "cikti\FULLSERVIS-WINDOWS-WIFI"

echo [3/4] Uygulama derleniyor (birkac dakika surebilir)...
set "FS_APP_NAME=FULLSERVIS-WINDOWS-WIFI"
"%PY%" -m PyInstaller --noconfirm --clean fullservis_agent.spec || goto :hata

echo [4/4] Dagitim klasoru hazirlaniyor...
mkdir "cikti\FULLSERVIS-WINDOWS-WIFI\ayarlar" 2>nul
copy /y "dist\FULLSERVIS-WINDOWS-WIFI.exe" "cikti\FULLSERVIS-WINDOWS-WIFI\" >nul || goto :hata
copy /y "%REPO%\fullservice-backend\config.json" "cikti\FULLSERVIS-WINDOWS-WIFI\ayarlar\" >nul

echo.
echo ============================================================
echo  TAMAM. Dagitilacak klasor:
echo    %cd%\cikti\FULLSERVIS-WINDOWS-WIFI
echo.
echo  Bu klasoru USB ile Windows makinesine kopyalayin;
echo  son kullanici .exe dosyasina cift tiklasin.
echo ============================================================
pause
exit /b 0

:hata
echo.
echo HATA: Derleme basarisiz. Yukaridaki mesaja bakin.
pause
exit /b 1
