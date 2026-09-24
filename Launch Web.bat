@echo off
chcp 65001 >nul
title Tro ly Thu tuc hanh chinh - V10.5
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  [LOI] Chua cai dat xong.
    echo  Hay bam doi "Setup First Time.bat" truoc, roi quay lai day.
    echo.
    pause
    exit /b 1
)

echo.
echo  ===============================================
echo   Dang khoi dong may chu...
echo   Dia chi:  http://127.0.0.1:8000
echo   Trinh duyet se tu mo sau vai giay.
echo   Dong cua so nay (hoac Ctrl+C) de tat.
echo  ===============================================
echo.

start "" /b cmd /c "timeout /t 8 /nobreak >nul && start http://127.0.0.1:8000"
".venv\Scripts\python.exe" "Backend\main.py"

echo.
echo  === May chu da dung. ===
pause
