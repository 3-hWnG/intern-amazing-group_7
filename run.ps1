# ---------------------------------------------------------------------------
# Nhom 7 - Tro ly Thu tuc hanh chinh
#
#   .\run.ps1              -> CHAY UNG DUNG (tu nap chi muc neu can). Mot dong duy nhat.
#   .\run.ps1 -Eval        -> cham diem TRUY HOI tren 862 cau hoi
#   .\run.ps1 -Routing     -> cham diem CHON CONG CU (agent v6)
#   .\run.ps1 -Reingest    -> ep nap lai chi muc roi chay
#   .\run.ps1 -Check       -> kiem tra moi truong day du (co nap model)
#   .\run.ps1 -Test        -> kiem thu tu dong
# ---------------------------------------------------------------------------
param(
    [switch]$Eval,
    [switch]$Routing,
    [string]$Save = "",
    [switch]$Reingest,
    [switch]$Check,
    [switch]$Test,
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Khong tim thay .\.venv trong $Root" -ForegroundColor Red
    exit 1
}
& ".\.venv\Scripts\Activate.ps1"

python -m pip install -q rank_bm25 sentencepiece protobuf 2>&1 | Out-Null
Set-Location "$Root\app"

# --- kiem tra chi muc: chi doc 1 file JSON, KHONG nap model -> gan nhu tuc thi
Write-Host "=== Chi muc ===" -ForegroundColor Cyan
python check_index.py
$needIngest = ($LASTEXITCODE -eq 2)

if ($Reingest -or $needIngest) {
    Write-Host "=== Nap chi muc ===" -ForegroundColor Cyan
    python ingest.py
    if ($LASTEXITCODE -ne 0) { Write-Host "ingest that bai" -ForegroundColor Red; exit 1 }
}

if ($Check) {
    python preflight.py
    exit $LASTEXITCODE
}

if ($Test) {
    Write-Host "=== Kiem thu tu dong ===" -ForegroundColor Cyan
    python selftest.py
    exit $LASTEXITCODE
}

if ($Routing) {
    Set-Location $Root
    Write-Host "=== Cham diem chon cong cu (agent) ===" -ForegroundColor Cyan
    $RoutingArgs = @("Evaluation\evaluate_routing.py")
    if ($Limit -gt 0) { $RoutingArgs += @("--limit", "$Limit") }
    if ($Save -ne "") { $RoutingArgs += @("--save", $Save) }
    & ".\.venv\Scripts\python.exe" @RoutingArgs
    exit $LASTEXITCODE
}

if ($Eval) {
    $EvalCsv = Resolve-Path "$Root\Evaluation\eval_questions.csv"
    $OutCsv  = "$Root\Evaluation\eval_results.csv"
    Write-Host "=== Cham diem ===" -ForegroundColor Cyan
    if ($Limit -gt 0) {
        python evaluate_retrieval.py --eval "$EvalCsv" --out "$OutCsv" --limit $Limit
    } else {
        python evaluate_retrieval.py --eval "$EvalCsv" --out "$OutCsv"
    }
    Write-Host "`nKet qua: $OutCsv" -ForegroundColor Green
    exit 0
}

# --- mac dinh: chay ung dung. Model chi nap MOT lan, trong lifespan cua server.
Write-Host "=== Server: http://127.0.0.1:8000 ===" -ForegroundColor Cyan
Write-Host "    (Ctrl+C de dung)" -ForegroundColor DarkGray
python main.py
