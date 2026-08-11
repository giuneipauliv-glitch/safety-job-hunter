# Daily full update: all sources headless (no popup), auto push to GitHub
# ASCII-only on purpose: Windows PowerShell 5.1 mis-parses UTF-8 Chinese (GBK issue)
# Usage: powershell -ExecutionPolicy Bypass -File run_daily.ps1
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") { $py = $cmd.Source }
if (-not $py) { foreach ($c in @("E:\work space\.tools\py312\python.exe", "$env:USERPROFILE\.tools\py312\python.exe")) { if (Test-Path $c) { $py = $c; break } } }
if (-not $py) { Write-Host "ERROR: python not found"; exit 1 }

Write-Host "=== STEP 1/2: headless scrape (zhaopin/iguopin/yjs) ==="
& $py run.py --backend chrome_dump
$code = $LASTEXITCODE
if ($code -eq 2) {
    Write-Host "[WARN] zhaopin blocked (login expired?). run login_zhaopin.py to re-login."
}

Write-Host "=== STEP 2/2: push to GitHub ==="
$gitExe = ""
foreach ($c in @("C:\Program Files\HanaAgent\resources\git\mingw64\bin\git.exe",
                 "C:\Program Files\Git\cmd\git.exe")) { if (Test-Path $c) { $gitExe = $c; break } }
if ($gitExe -and (Test-Path "E:\work space\.gh_token")) {
    $env:GH_TOKEN = (Get-Content "E:\work space\.gh_token" -Raw).Trim()
    $remote = "https://giuneipauliv-glitch:$env:GH_TOKEN@github.com/giuneipauliv-glitch/safety-job-hunter.git"
    & $gitExe remote remove origin 2>$null | Out-Null
    & $gitExe remote add origin $remote 2>$null | Out-Null
    & $gitExe add data docs
    & $gitExe commit -m "daily data $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
    & $gitExe push origin main --force 2>&1 | Select-Object -Last 2
    $pushCode = $LASTEXITCODE
    & $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"
    if ($pushCode -eq 0) {
        Write-Host "pushed OK"
    } else {
        Write-Host "PUSH FAILED (exit $pushCode): network/token issue, run push_only.ps1 later"
    }
} else {
    Write-Host "token/git missing, skip push"
}

Write-Host ""
Write-Host "DONE. site: https://giuneipauliv-glitch.github.io/safety-job-hunter/"
