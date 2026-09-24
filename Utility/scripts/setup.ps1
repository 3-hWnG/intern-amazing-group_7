# ---------------------------------------------------------------------------
# CAI DAT LAN DAU - Tro ly Thu tuc hanh chinh V10.5
# (Chu thich khong dau de hien dung tren moi console Windows.)
#
# Chay MOT LAN tren may moi. Chay lai nhieu lan cung khong sao: moi buoc deu
# kiem tra truoc, CAI GI CO ROI THI BO QUA - khong tai lai.
#
#   Cach dung: bam doi "Setup First Time.bat" o thu muc goc
#   Tham so:
#       -IncludeFinetune   cai them thu vien huan luyen (torch, ~3GB)
#       -SkipOllama        bo qua buoc cai Ollama / tai mo hinh
#       -SkipScrape        bo qua buoc cao CSDL thu tuc (He thong 2)
# ---------------------------------------------------------------------------
param(
    [switch]$IncludeFinetune,
    [switch]$SkipOllama,
    [switch]$SkipScrape
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

function Write-Step($n, $text) { Write-Host "" ; Write-Host "[$n] $text" -ForegroundColor Cyan }
function Write-Ok($text)       { Write-Host "    OK  - $text" -ForegroundColor Green }
function Write-Skip($text)     { Write-Host "    BO QUA - $text" -ForegroundColor DarkGray }
function Write-Warn($text)     { Write-Host "    CHU Y - $text" -ForegroundColor Yellow }
function Write-Die($text)      { Write-Host "    LOI - $text" -ForegroundColor Red; exit 1 }

function Test-Cmd($name) {
    return ($null -ne (Get-Command $name -ErrorAction SilentlyContinue))
}

function Update-PathFromRegistry {
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

Write-Host "=======================================================" -ForegroundColor White
Write-Host " CAI DAT LAN DAU - Tro ly Thu tuc hanh chinh V10.5" -ForegroundColor White
Write-Host " Thu muc: $Root" -ForegroundColor DarkGray
Write-Host "=======================================================" -ForegroundColor White

# 1 ------------------------------------------------------------- Python ----
Write-Step 1 "Kiem tra Python 3.12"
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $Py) {
    Write-Ok ".venv da co san -> khong can Python he thong"
} else {
    $sysPyExe = $null
    $sysPyArgs = @()
    foreach ($cand in @(@("py", "-3.12"), @("py", "-3"), @("python"))) {
        if (-not (Test-Cmd $cand[0])) { continue }
        $probeArgs = @()
        if ($cand.Length -gt 1) { $probeArgs = $cand[1..($cand.Length - 1)] }
        try {
            $v = & $cand[0] @probeArgs -c "import sys;print('%d.%d' % sys.version_info[:2])"
            if ($v -and ([version]$v -ge [version]"3.10")) {
                $sysPyExe = $cand[0]; $sysPyArgs = $probeArgs
                Write-Ok "tim thay Python $v"
                break
            }
        } catch { }
    }
    if (-not $sysPyExe) {
        Write-Warn "chua co Python -> thu cai bang winget"
        if (Test-Cmd winget) {
            winget install --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
            Update-PathFromRegistry
            if (Test-Cmd py) { $sysPyExe = "py"; $sysPyArgs = @("-3.12") }
            elseif (Test-Cmd python) { $sysPyExe = "python"; $sysPyArgs = @() }
        }
        if (-not $sysPyExe) {
            Write-Die "khong cai duoc Python. Tai thu cong tai https://www.python.org/downloads/ (nho tick 'Add python.exe to PATH') roi chay lai."
        }
        Write-Ok "da cai Python"
    }

    Write-Step "1b" "Tao .venv"
    & $sysPyExe @sysPyArgs -m venv .venv
    if (-not (Test-Path $Py)) { Write-Die "tao .venv that bai" }
    Write-Ok ".venv da tao"
}

# 2 ---------------------------------------------- sua duong dan trong .venv --
Write-Step 2 "Kiem tra duong dan ben trong .venv (phong khi thu muc bi di chuyen)"
& $Py "Utility\scripts\fix_venv.py"

# 3 ------------------------------------------------------- thu vien Python --
Write-Step 3 "Kiem tra thu vien Python"
$probe = "import fastapi,uvicorn,pydantic,ollama,mcp,ddgs,httpx,trafilatura,bcrypt,pandas,openpyxl,pypdf,docx"
& $Py -c $probe
if ($LASTEXITCODE -eq 0) {
    Write-Skip "tat ca thu vien da co -> khong cai lai"
} else {
    Write-Warn "thieu thu vien -> dang cai tu requirements.txt"
    & $Py -m pip install --disable-pip-version-check -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Die "pip install that bai. Kiem tra ket noi mang roi chay lai script nay." }
    Write-Ok "da cai xong thu vien"
}

if ($IncludeFinetune) {
    Write-Step "3b" "Thu vien huan luyen (torch...)"
    & $Py -c "import torch,transformers,peft"
    if ($LASTEXITCODE -eq 0) {
        Write-Skip "da co"
    } else {
        & $Py -m pip install --disable-pip-version-check -r Utility\finetune\requirements-finetune.txt
        if ($LASTEXITCODE -ne 0) { Write-Warn "cai thu vien huan luyen that bai - ung dung chinh VAN CHAY duoc" }
        else { Write-Ok "da cai" }
    }
}

# 4 ----------------------------------------------------------------- .env ---
Write-Step 4 "Tep cau hinh .env"
if (Test-Path ".env") {
    Write-Skip ".env da co -> giu nguyen (khong ghi de cau hinh cua ban)"
} else {
    Copy-Item ".env.example" ".env"
    Write-Ok "da tao .env tu .env.example"
}

# 5 -------------------------------------------------------------- Ollama ----
$Model = (& $Py -c "import sys;sys.path.insert(0, r'$Root');import config;print(config.LLM_MODEL)").Trim()
$Verifier = (& $Py -c "import sys;sys.path.insert(0, r'$Root');import config;print(config.VERIFIER_MODEL)").Trim()

if ($SkipOllama) {
    Write-Step 5 "Ollama"
    Write-Skip "bo qua theo tham so -SkipOllama"
} else {
    Write-Step 5 "Kiem tra Ollama (may chu mo hinh chay cuc bo)"
    if (Test-Cmd ollama) {
        Write-Ok "ollama da cai"
    } else {
        Write-Warn "chua co Ollama -> thu cai bang winget"
        if (Test-Cmd winget) {
            winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements --silent
            Update-PathFromRegistry
        }
        if (-not (Test-Cmd ollama)) {
            Write-Warn "khong cai duoc Ollama tu dong. Tai tai https://ollama.com/download roi chay lai script nay."
            Write-Warn "Ung dung van khoi dong duoc, nhung chua tra loi duoc cau hoi nao."
        } else {
            Write-Ok "da cai Ollama"
        }
    }

    if (Test-Cmd ollama) {
        Write-Step "5b" "Kiem tra dich vu Ollama"
        $up = $false
        try { ollama list | Out-Null; $up = ($LASTEXITCODE -eq 0) } catch { $up = $false }
        if (-not $up) {
            Write-Warn "dich vu chua chay -> dang bat 'ollama serve'"
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            for ($i = 0; $i -lt 20; $i++) {
                Start-Sleep -Seconds 1
                try { ollama list | Out-Null; if ($LASTEXITCODE -eq 0) { $up = $true; break } } catch { }
            }
        }
        if ($up) { Write-Ok "dich vu Ollama dang chay" }
        else { Write-Warn "dich vu Ollama khong len - mo ung dung Ollama thu cong roi chay lai" }

        if ($up) {
            Write-Step "5c" "Mo hinh ngon ngu"
            $have = (ollama list | Out-String)
            foreach ($m in (@($Model, $Verifier) | Select-Object -Unique)) {
                if (-not $m) { continue }
                if ($have -match [regex]::Escape($m)) {
                    Write-Skip "$m da co -> khong tai lai"
                } else {
                    Write-Warn "dang tai $m (lan dau hoi lau, tuy mang)"
                    ollama pull $m
                    if ($LASTEXITCODE -eq 0) { Write-Ok "$m da san sang" }
                    else { Write-Warn "tai $m that bai - chay lai sau bang: ollama pull $m" }
                }
            }
        }
    }
}

# 6 ---------------------------------------------------------------- CSDL ----
Write-Step 6 "Khoi tao co so du lieu (Database\runtime\app.db)"
$initDb = "import sys;sys.path.insert(0, r'$Root');sys.path.insert(0, r'$Root\Backend');" +
          "from db import connection;connection.init_db();from config import DB_PATH;print(DB_PATH)"
$dbOut = & $Py -c $initDb
if ($LASTEXITCODE -eq 0) { Write-Ok "CSDL san sang: $dbOut" } else { Write-Die "khoi tao CSDL that bai" }

# 7 --------------------------------------------- CSDL thu tuc hanh chinh ----
# He thong 2 (mac dinh) tra cuu tu Database\runtime\procedures.db.
# File .db VA thu muc bieu mau (Database\raw\files - 774 thu muc .docx) DEU
# KHONG commit vao git: kho se nang va khong diff duoc. Vi vay may moi phai tu
# cao lai. Pham vi mac dinh (--scope xa): thu tuc cap Xa/Phuong (level=COMMUNE)
# + thu tuc rieng cua UBND TP.HCM (H29), ~1.350 thu tuc, mat khoang 15-25 phut
# (gioi han 2 req/s de khong lam phien cong dich vu cong).
#
# Chay lai nhieu lan khong sao: import_db.py so sanh content_hash, khong doi
# thi bo qua. Dung -SkipScrape neu chi muon cai lai thu vien.
Write-Step 7 "Co so du lieu thu tuc hanh chinh (He thong 2)"
$procDb = Join-Path $Root "Database\runtime\procedures.db"
$needScrape = $false

# Dem thu tuc dang co. Dung here-string + "python -" de khoi phai long nhau
# dau nhay giua PowerShell, Python va SQL.
$countPy = @'
import sqlite3, sys
try:
    print(sqlite3.connect(sys.argv[1]).execute(
        "select count(*) from procedures where status='active'").fetchone()[0])
except Exception:
    print(0)
'@

if ($SkipScrape) {
    Write-Skip "-SkipScrape -> bo qua buoc cao du lieu"
} elseif (Test-Path $procDb) {
    $n = 0
    try { $n = [int]($countPy | & $Py - $procDb) } catch { $n = 0 }
    if ($n -gt 0) {
        Write-Skip "da co $n thu tuc trong CSDL -> khong cao lai"
        Write-Host "    (muon cap nhat: python -m Database.pipeline.run_pipeline --all)" -ForegroundColor DarkGray
    } else {
        $needScrape = $true
    }
} else {
    $needScrape = $true
}

if ($needScrape) {
    Write-Host "    Dang cao ~1.350 thu tuc cap Xa/Phuong tu dichvucong.gov.vn..." -ForegroundColor DarkGray
    Write-Host "    Viec nay mat 15-25 phut va CAN MANG." -ForegroundColor DarkGray
    Write-Host "    Ctrl+C de bo qua: luc do He thong 2 bao chua co CSDL," -ForegroundColor DarkGray
    Write-Host "    va ban van dung duoc He thong 1 (Web search) binh thuong." -ForegroundColor DarkGray
    $env:PYTHONPATH = $Root
    & $Py -m Database.pipeline.run_pipeline --all
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "CSDL thu tuc san sang"
    } else {
        # Cao hong KHONG duoc lam hong ca buoc cai dat: He thong 1 van chay duoc.
        Write-Warn "cao du lieu chua xong (mat mang hoac cong bi gioi han)."
        Write-Warn "chay lai sau bang: python -m Database.pipeline.run_pipeline --all"
    }
}

# ---------------------------------------------------------------- xong ------
Write-Host ""
Write-Host "=======================================================" -ForegroundColor Green
Write-Host " CAI DAT XONG." -ForegroundColor Green
Write-Host " Tu gio chi can bam doi: Launch Web.bat" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
