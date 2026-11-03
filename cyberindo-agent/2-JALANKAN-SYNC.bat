@echo off
title FAUKAY E-SPORT - Live Sync CyberIndo Agent
color 0A
echo ============================================================
echo   FAUKAY E-SPORT - CYBERINDO LIVE SYNC AGENT
echo ============================================================
echo.
set /p WEB_URL="Masukkan URL Website (Tekan ENTER langsung untuk https://faukayesport-fky.vercel.app): "
if "%WEB_URL%"=="" set WEB_URL=https://faukayesport-fky.vercel.app

echo.
echo Memeriksa modul Python (pywinauto ^& requests)...
pip install pywinauto requests --quiet

echo.
echo Menjalankan pembaca otomatis CyberIndo ke: %WEB_URL%
echo (Jangan tutup jendela ini selama warnet beroperasi)
echo ============================================================
python "%~dp0cyberindo-ui-reader.py" --url "%WEB_URL%"
pause
