@echo off
setlocal
rem Download the "no-thinking" Qwen3 4B model (Qwen3-4B-Instruct-2507, 4-bit, about 2.5 GB) for System 4.
rem Safe to run again: Ollama resumes an interrupted download and skips it if the model is already there.
set "MODEL=qwen3:4b-instruct-2507-q4_K_M"

where ollama >nul 2>nul || (
    echo ERROR: Ollama is not installed. Install it from https://ollama.com and try again.
    goto :fail
)
ollama list >nul 2>nul || (
    start "" /min ollama serve
    timeout /t 5 >nul
)

echo [1/2] Downloading %MODEL% (about 2.5 GB)...
ollama pull %MODEL% || goto :fail

echo.
echo [2/2] Quick test (the model should answer one short sentence in Vietnamese)...
ollama run %MODEL% "Chao ban, hay tra loi bang mot cau tieng Viet ngan." || goto :fail

echo.
echo Done. Models now on this computer:
ollama list
pause
exit /b 0

:fail
echo.
echo Download did not finish. Check your internet connection and run this file again (it resumes).
pause
exit /b 1
