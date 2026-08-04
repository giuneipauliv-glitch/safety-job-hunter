# Upgrade: push new sources -> local full scrape (with Zhaopin) -> push data
# Prereq: token saved to E:\work space\.gh_token (repo scope)
# Usage: powershell -ExecutionPolicy Bypass -File upgrade_all.ps1
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

if (-not (Test-Path "E:\work space\.gh_token")) { Write-Host "ERROR: no token file. save token to E:\work space\.gh_token first"; exit 1 }

# locate python
$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") { $py = $cmd.Source }
if (-not $py) { foreach ($c in @("E:\work space\.tools\py312\python.exe", "$env:USERPROFILE\.tools\py312\python.exe")) { if (Test-Path $c) { $py = $c; break } } }
if (-not $py) { Write-Host "ERROR: python not found"; exit 1 }

# locate git (HanaAgent bundled or system)
$gitExe = ""
foreach ($c in @("C:\Program Files\HanaAgent\resources\git\mingw64\bin\git.exe",
                  "C:\Program Files\Git\cmd\git.exe",
                  "$env:ProgramFiles\Git\bin\git.exe",
                  "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
    if (Test-Path $c) { $gitExe = $c; break }
}
if (-not $gitExe) {
    $g = Get-Command git -ErrorAction SilentlyContinue
    if ($g) { $gitExe = $g.Source }
}
if (-not $gitExe) { Write-Host "ERROR: git not found"; exit 1 }
Write-Host "git: $gitExe"

# read token
$env:GH_TOKEN = (Get-Content "E:\work space\.gh_token" -Raw).Trim()
Write-Host "token loaded (len $($env:GH_TOKEN.Length))"

# STEP 1: push code (incl. workflow update) via git
Write-Host "=== STEP 1/4: push code ==="
if (-not (Test-Path ".git")) { Write-Host "ERROR: not a git repo at $PSScriptRoot"; exit 1 }
& $gitExe config user.name "job-radar" | Out-Null
& $gitExe config user.email "job-radar@localhost" | Out-Null
$remote = "https://giuneipauliv-glitch:$env:GH_TOKEN@github.com/giuneipauliv-glitch/safety-job-hunter.git"
& $gitExe remote remove origin 2>$null | Out-Null
& $gitExe remote add origin $remote 2>$null | Out-Null
& $gitExe remote -v
& $gitExe push -u origin main --force 2>&1 | Select-Object -Last 4
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: git push code"; exit 1 }
& $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"

# STEP 2: local full scrape (Zhaopin via home IP + all sources)
Write-Host "=== STEP 2/4: local full scrape ==="
& $py run.py --backend chrome_dump
if ($LASTEXITCODE -eq 2) { Write-Host "WARN: scrape partially blocked (Zhaopin IP issue), continuing with other sources" }
if ($LASTEXITCODE -gt 2) { exit $LASTEXITCODE }

# STEP 3: push data + site
Write-Host "=== STEP 3/4: push data ==="
& $gitExe add data docs
& $gitExe commit -m "data update $(Get-Date -Format 'yyyy-MM-dd')" 2>&1 | Out-Null
& $gitExe remote remove origin 2>$null | Out-Null
& $gitExe remote add origin $remote 2>$null | Out-Null
& $gitExe push origin main --force 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: git push data"; exit 1 }
& $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"

# STEP 4: cleanup token file
Write-Host "=== STEP 4/4: cleanup ==="
Remove-Item "E:\work space\.gh_token" -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "ALL DONE."
Write-Host "  site: https://giuneipauliv-glitch.github.io/safety-job-hunter/"
Write-Host "NOTE: revoke this token on GitHub when done."
