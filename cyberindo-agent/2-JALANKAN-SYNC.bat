@echo off
title FAUKAY E-SPORT - Live Sync CyberIndo Agent
color 0A
echo ============================================================
echo   FAUKAY E-SPORT - CYBERINDO LIVE SYNC AGENT
echo ============================================================
echo.
set /p WEB_URL="Masukkan URL Website Anda (kosongkan jika http://localhost:3000): "
if "%WEB_URL%"=="" set WEB_URL=http://localhost:3000

echo.
echo Memeriksa modul Python (pywinauto ^& requests)...
pip install pywinauto requests --quiet

echo.
echo Menjalankan pembaca otomatis CyberIndo ke: %WEB_URL%/api/pcs
echo (Jangan tutup jendela ini selama warnet beroperasi)
echo ============================================================
python "%~dp0cyberindo-ui-reader.py" --url "%WEB_URL%/api/pcs"
pause
