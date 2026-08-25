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

Write-Host "=== STEP 1/3: headless scrape (zhaopin/iguopin/yjs) ==="
& $py run.py --backend chrome_dump
$code = $LASTEXITCODE
if ($code -eq 2) {
    Write-Host "[WARN] zhaopin blocked (login expired?). run login_zhaopin.py to re-login."
}

Write-Host "=== STEP 1.5/3: sync to Feishu (no VPN needed) ==="
if (Test-Path "E:\work space\safety-job-hunter\feishu_config.json") {
    & $py src\sync_feishu.py
} else {
    Write-Host "feishu config missing, skip feishu sync"
}

Write-Host "=== STEP 2/3: push to GitHub ==="
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
    & $gitExe remote remove origin 2>$null | Out-Null
    & $gitExe remote add origin $remote 2>$null | Out-Null
    # push with retry: proxy first, fallback direct, then retry
    $pushCode = 1
    for ($i = 1; $i -le 3; $i++) {
        & $gitExe push origin main --force 2>&1 | Select-Object -Last 1 | Out-Null
        $pushCode = $LASTEXITCODE
        if ($pushCode -eq 0) { break }
        # proxy failed -> try direct (no proxy) once
        if ($i -eq 1) {
            Write-Host "proxy push failed, try direct..."
            & $gitExe -c http.proxy= -c https.proxy= push origin main --force 2>&1 | Select-Object -Last 1 | Out-Null
            $pushCode = $LASTEXITCODE
            if ($pushCode -eq 0) { break }
        }
        if ($i -lt 3) {
            Write-Host "push attempt $i failed, retry in 180s..."
            Start-Sleep -Seconds 180
        }
    }
    & $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"
    if ($pushCode -eq 0) {
        Write-Host "pushed OK"
    } else {
        Write-Host "PUSH FAILED after retries: run push_only.ps1 later when network recovers"
    }
} else {
    Write-Host "token/git missing, skip push"
}

Write-Host ""
Write-Host "DONE. feishu + site updated"
