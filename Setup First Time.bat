@echo off
chcp 65001 >nul
title Cai dat lan dau - LLM for Procedures V10.3
cd /d "%~dp0"

echo.
echo  Dang chay cai dat lan dau. Cai gi co roi se duoc bo qua.
echo  Lan dau tren may moi co the mat 10-30 phut (tai thu vien + mo hinh).
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "Utility\scripts\setup.ps1" %*

echo.
pause
