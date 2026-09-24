@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo === Chay bo 72 test System 2 ===
echo.
echo [1/3] Test Extractor...
.\.venv\Scripts\python.exe system2\test_extractor.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo [2/3] Test Customer Care...
.\.venv\Scripts\python.exe system2\test_customer_care.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo [3/3] Test Pipeline...
.\.venv\Scripts\python.exe system2\test_pipeline.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo === TAT CA TEST DA PASS ===
