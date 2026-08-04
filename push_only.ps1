# Push code + data to GitHub (keep token for daily auto-push)
# Usage: powershell -ExecutionPolicy Bypass -File push_only.ps1
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

if (-not (Test-Path "E:\work space\.gh_token")) { Write-Host "ERROR: no token at E:\work space\.gh_token"; exit 1 }
$env:GH_TOKEN = (Get-Content "E:\work space\.gh_token" -Raw).Trim()

$gitExe = ""
foreach ($c in @("C:\Program Files\HanaAgent\resources\git\mingw64\bin\git.exe",
                 "C:\Program Files\Git\cmd\git.exe")) { if (Test-Path $c) { $gitExe = $c; break } }
if (-not $gitExe) { $gc = Get-Command git -ErrorAction SilentlyContinue; if ($gc) { $gitExe = $gc.Source } }
if (-not $gitExe) { Write-Host "ERROR: git not found"; exit 1 }

$remote = "https://giuneipauliv-glitch:$env:GH_TOKEN@github.com/giuneipauliv-glitch/safety-job-hunter.git"
& $gitExe config user.name "job-radar" | Out-Null
& $gitExe config user.email "job-radar@localhost" | Out-Null
& $gitExe add -A
& $gitExe commit -m "update: sources + data $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
& $gitExe remote remove origin 2>$null | Out-Null
& $gitExe remote add origin $remote 2>$null | Out-Null
& $gitExe push origin main --force 2>&1 | Select-Object -Last 3
$code = $LASTEXITCODE
& $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"
if ($code -eq 0) { Write-Host "PUSH OK. site: https://giuneipauliv-glitch.github.io/safety-job-hunter/" }
else { Write-Host "PUSH FAILED (exit $code)" }
exit $code
