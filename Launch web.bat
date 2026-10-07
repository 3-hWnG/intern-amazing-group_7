@echo off
setlocal
rem Start the web (System 3 Strict + System 4 Friendly) at http://127.0.0.1:8300 (close this window or press Ctrl+C to stop).
set "REPO=%~dp0"
set "REPO=%REPO:~0,-1%"
for %%I in ("%REPO%\..") do set "PYROOT=%%~fI\pyroot"

if not exist "%REPO%\.venv\Scripts\python.exe" goto :nosetup
if not exist "%PYROOT%\system3\server\main.py" goto :nosetup
if not exist "%REPO%\data\runtime\system3.db" goto :nosetup

set "PYTHONPATH=%PYROOT%"
set "PYTHONIOENCODING=utf-8"
rem LLM step of System 3 (qwen3:4b via Ollama) is on. Set S3_USE_LLM=0 beforehand to run rules-only.
if not defined S3_USE_LLM set "S3_USE_LLM=1"
rem System 4 (login + Friendly mode) is on. Set S4_ENABLED=0 beforehand to get the old System 3 web back.
if not defined S4_ENABLED set "S4_ENABLED=1"
rem Friendly mode always needs Ollama, so start it if it is not running.
ollama list >nul 2>nul || start "" /min ollama serve

cd /d "%REPO%\server"
if not defined NO_BROWSER start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8300"
echo Starting the web at http://127.0.0.1:8300 ...
"%REPO%\.venv\Scripts\python.exe" main.py
pause
exit /b

:nosetup
echo Setup has not been run yet. Run "Set up first time.bat" first.
pause
exit /b 1
