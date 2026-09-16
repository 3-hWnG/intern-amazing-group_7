# ---------------------------------------------------------------------------
# Tro ly Thu tuc hanh chinh
#
#   .\run.ps1                   -> CHAY UNG DUNG: http://127.0.0.1:8000
#   .\run.ps1 -Install          -> cai thu vien vao .venv roi chay
#   .\run.ps1 -Mcp              -> chay rieng MCP search server (HTTP, cong 8765)
#   .\run.ps1 -Eval [-Limit N]  -> cham diem pipeline (Evaluation\eval_set.jsonl)
#   .\run.ps1 -EvalIntent       -> chi cham buoc hieu y dinh / hoi lai (nhanh)
#   .\run.ps1 -Bench            -> do toc do / VRAM mo hinh (finetune\benchmark_quant.py)
# ---------------------------------------------------------------------------
param(
    [switch]$Install,
    [switch]$Mcp,
    [switch]$Eval,
    [switch]$EvalIntent,
    [switch]$Bench,
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Chua co .venv -> tao moi" -ForegroundColor Yellow
    python -m venv .venv
    $Install = $true
}
if ($Install) {
    & $Py -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Host "pip install that bai" -ForegroundColor Red; exit 1 }
}
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Da tao .env tu .env.example" -ForegroundColor DarkGray
}

if ($Mcp) {
    Write-Host "=== MCP search server: http://127.0.0.1:8765/mcp ===" -ForegroundColor Cyan
    & $Py app\mcp_search\server.py --transport http --host 127.0.0.1 --port 8765
    exit $LASTEXITCODE
}

if ($Eval -or $EvalIntent) {
    $EvalArgs = @("Evaluation\evaluate.py")
    if ($EvalIntent) { $EvalArgs += "--only-intent" }
    if ($Limit -gt 0) { $EvalArgs += @("--limit", "$Limit") }
    & $Py @EvalArgs
    exit $LASTEXITCODE
}

if ($Bench) {
    & $Py finetune\benchmark_quant.py
    exit $LASTEXITCODE
}

Write-Host "=== Server: http://127.0.0.1:8000 ===" -ForegroundColor Cyan
Write-Host "    (Ctrl+C de dung)" -ForegroundColor DarkGray
& $Py app\main.py
