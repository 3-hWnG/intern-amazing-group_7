@echo off
setlocal
rem One-time setup for System 3 + System 4: Python env, packages, "system3" package link, AI models, database.
rem Needs internet here. After setup everything runs offline, except the ABI domain refreshing its abi.com.vn data (it keeps answering from the last snapshot without internet).
rem Total download the first time: about 11.5 GB (packages ~3 GB incl. GPU torch, models ~8.5 GB).
set "REPO=%~dp0"
set "REPO=%REPO:~0,-1%"
for %%I in ("%REPO%\..") do set "PYROOT=%%~fI\pyroot"
cd /d "%REPO%"

echo [1/10] Creating Python environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv 2>nul || python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: could not create .venv. Install Python 3.12 from python.org and try again.
    goto :fail
)

echo [2/10] Installing packages from requirements.txt (System 4 adds GPU torch, about 2.5 GB, first time only)...
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail

echo [3/10] Linking package "system3" -^> this folder...
rem The code imports itself as "system3.*", so PYTHONPATH needs a folder named system3.
if not exist "%PYROOT%\system3\server\main.py" (
    if exist "%PYROOT%\system3" rmdir "%PYROOT%\system3"
    mkdir "%PYROOT%" 2>nul
    mklink /J "%PYROOT%\system3" "%REPO%" >nul || goto :fail
)

if not defined LLM_MODEL set "LLM_MODEL=qwen3:4b"
echo [4/10] Downloading LLM model %LLM_MODEL% (about 2.5 GB, first time only)...
where ollama >nul 2>nul || (
    echo ERROR: Ollama is not installed. Install it from https://ollama.com and try again.
    goto :fail
)
ollama list >nul 2>nul || (
    start "" /min ollama serve
    timeout /t 5 >nul
)
ollama pull %LLM_MODEL% || goto :fail

echo [5/10] System 4: downloading search model bge-m3 (about 1.2 GB, first time only)...
ollama pull bge-m3 || goto :fail

echo [6/10] System 4: downloading fast-answer model qwen3:4b-instruct-2507-q4_K_M (about 2.5 GB, first time only)...
rem The "no-thinking" twin of qwen3:4b, tested for fast answers (docs/SYSTEM4_NV5_TOC_DO_CHINH_XAC.md).
ollama pull qwen3:4b-instruct-2507-q4_K_M || goto :fail

echo [7/10] System 4: downloading reranker BAAI/bge-reranker-v2-m3 (about 2.3 GB, first time only)...
"%REPO%\.venv\Scripts\python.exe" "%REPO%\system4\setup_models.py" reranker || goto :fail

echo [8/10] Building database (about 1 minute)...
set "PYTHONPATH=%PYROOT%"
set "PYTHONIOENCODING=utf-8"
cd /d "%PYROOT%"
"%REPO%\.venv\Scripts\python.exe" -m system3.data.build || goto :fail
"%REPO%\.venv\Scripts\python.exe" -m system3.data.tests.test_data || goto :fail
rem System 4: if the admin page applied another version of the procedures data, rebuild from that version again.
"%REPO%\.venv\Scripts\python.exe" -m system3.system4.server.procs reapply || goto :fail

echo [9/10] System 4: downloading a snapshot of abi.com.vn for the ABI domain (about 3 minutes the first time, seconds later)...
rem Only public read-only APIs of abi.com.vn, 2 requests/second. Re-running setup only downloads what changed.
rem The search index is built by the web itself after the first dev account exists (or press "Dong bo ngay" in the domain manager).
rem No internet / site down: setup continues; the web can download the data later with that button.
"%REPO%\.venv\Scripts\python.exe" -m system3.system4.abi.sync --no-index || echo WARNING: could not download abi.com.vn data now. Use "Dong bo ngay" in the web later.

echo [10/10] System 4: checking that the GPU is usable for the reranker...
"%REPO%\.venv\Scripts\python.exe" "%REPO%\system4\setup_models.py" check-gpu

echo.
echo Setup complete. Run "Launch web.bat" to start the website.
pause
exit /b 0

:fail
echo.
echo Setup FAILED - see the messages above.
pause
exit /b 1
