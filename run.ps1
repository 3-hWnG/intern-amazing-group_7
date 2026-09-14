# ---------------------------------------------------------------------------
# Nhom 7 - Tro ly Thu tuc hanh chinh (Hybrid RAG + Tiers + Auth + Queue)
#
#   .\run.ps1              -> Chay Web Server (Mac dinh mo http://127.0.0.1:8000)
#   .\run.ps1 -Ingest      -> Nap lai CSDL ChromaDB da view + chi muc BM25
#   .\run.ps1 -Check       -> Kiem tra moi truong he thong (thu vien, models)
#   .\run.ps1 -Eval        -> Cham diem truy hoi tren Evaluation set (862 cau)
# ---------------------------------------------------------------------------
param(
    [switch]$Ingest,
    [switch]$Check,
    [switch]$Eval,
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# Xac dinh chinh xac file python.exe trong venv
$PythonExe = ""
if (Test-Path "$Root\venv\Scripts\python.exe") {
    $PythonExe = "$Root\venv\Scripts\python.exe"
} elseif (Test-Path "$Root\.venv\Scripts\python.exe") {
    $PythonExe = "$Root\.venv\Scripts\python.exe"
} else {
    Write-Host "[LOI] Khong tim thay venv hoac .venv trong $Root" -ForegroundColor Red
    exit 1
}

# 1. Nap lai du lieu neu yeu cau
if ($Ingest) {
    Write-Host "=== Nap du lieu vao ChromaDB & BM25 ===" -ForegroundColor Cyan
    & $PythonExe -X utf8 "$Root\app\ingest.py"
    exit $LASTEXITCODE
}

# 2. Kiem tra moi truong
if ($Check) {
    Write-Host "=== Kiem tra moi truong ===" -ForegroundColor Cyan
    & $PythonExe -X utf8 -c "
import torch, transformers, chromadb, rank_bm25, sentencepiece, google.protobuf, bcrypt, ollama
print('[ OK ] Tat ca thu vien can thiet da san sang!')
print(f'[ OK ] Torch version: {torch.__version__} | CUDA: {torch.cuda.is_available()}')
"
    exit $LASTEXITCODE
}

# 3. Cham diem Evaluation
if ($Eval) {
    Write-Host "=== Cham diem truy hoi (Evaluation) ===" -ForegroundColor Cyan
    $EvalScript = "$Root\Evaluation\evaluate_retrieval.py"
    if ($Limit -gt 0) {
        & $PythonExe -X utf8 $EvalScript --limit $Limit
    } else {
        & $PythonExe -X utf8 $EvalScript
    }
    exit $LASTEXITCODE
}

# 4. Mac dinh: Khoi dong Web Server
Write-Host "=== Dang khoi dong server va nap mo hinh (Vui long doi trong giay lat)... ===" -ForegroundColor DarkCyan
Set-Location (Join-Path $Root "app")
& $PythonExe -X utf8 -m uvicorn main:app --host 127.0.0.1 --port 8000
