@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo === Dang khoi dong Web Server: http://127.0.0.1:8000 ===
echo (Bam Ctrl+C de dung server)
echo.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
