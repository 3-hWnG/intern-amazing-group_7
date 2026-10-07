@echo off
setlocal
rem Start System 3 at http://127.0.0.1:8300 (close this window or press Ctrl+C to stop).
set "REPO=%~dp0"
set "REPO=%REPO:~0,-1%"
for %%I in ("%REPO%\..") do set "PYROOT=%%~fI\pyroot"

if not exist "%REPO%\.venv\Scripts\python.exe" goto :nosetup
if not exist "%PYROOT%\system3\server\main.py" goto :nosetup
if not exist "%REPO%\data\runtime\system3.db" goto :nosetup

set "PYTHONPATH=%PYROOT%"
set "PYTHONIOENCODING=utf-8"
rem LLM step (qwen3:4b via Ollama) is on. Set S3_USE_LLM=0 beforehand to run rules-only.
if not defined S3_USE_LLM set "S3_USE_LLM=1"
if "%S3_USE_LLM%"=="1" (
    ollama list >nul 2>nul || start "" /min ollama serve
)

cd /d "%REPO%\server"
if not defined NO_BROWSER start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8300"
echo Starting System 3 at http://127.0.0.1:8300 ...
"%REPO%\.venv\Scripts\python.exe" main.py
pause
exit /b

:nosetup
echo Setup has not been run yet. Run "Set up first time.bat" first.
pause
exit /b 1
