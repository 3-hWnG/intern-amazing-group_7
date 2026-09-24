# ---------------------------------------------------------------------------
# Tro ly Thu tuc hanh chinh - V10.5
# (Chu thich trong script khong dau de hien dung tren moi console Windows.)
#
#   .\Utility\scripts\run.ps1                   -> CHAY UNG DUNG: http://127.0.0.1:8000
#   .\Utility\scripts\run.ps1 -Install          -> cai lai thu vien vao .venv roi chay
#   .\Utility\scripts\run.ps1 -Mcp              -> chay rieng MCP search server (HTTP, cong 8765)
#   .\Utility\scripts\run.ps1 -Eval [-Limit N]  -> cham diem pipeline (Evaluation\eval_set.jsonl)
#   .\Utility\scripts\run.ps1 -EvalIntent       -> chi cham buoc hieu y dinh / hoi lai (nhanh)
#   .\Utility\scripts\run.ps1 -Bench            -> do toc do / VRAM mo hinh
#
# Cai lan dau tren may moi: chay "Setup First Time.bat" o thu muc goc.
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

# Utility\scripts\run.ps1 -> len 2 cap la goc du an
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Chua co .venv. Hay chay 'Setup First Time.bat' o thu muc goc truoc." -ForegroundColor Red
    exit 1
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
    & $Py Backend\mcp_search\server.py --transport http --host 127.0.0.1 --port 8765
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
    & $Py Utility\finetune\benchmark_quant.py
    exit $LASTEXITCODE
}

Write-Host "=== Server: http://127.0.0.1:8000 ===" -ForegroundColor Cyan
Write-Host "    (Ctrl+C de dung)" -ForegroundColor DarkGray
& $Py Backend\main.py
