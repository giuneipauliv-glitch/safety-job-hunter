# Finish deploy: cleanup test files -> enable Pages -> trigger Actions -> cleanup token
# Usage: powershell -ExecutionPolicy Bypass -File finish.ps1
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") { $py = $cmd.Source }
if (-not $py) { foreach ($c in @("E:\work space\.tools\py312\python.exe", "$env:USERPROFILE\.tools\py312\python.exe")) { if (Test-Path $c) { $py = $c; break } } }
if (-not $py) { Write-Host "ERROR: python not found"; exit 1 }
if (-not (Test-Path "E:\work space\.gh_token")) { Write-Host "ERROR: token file missing"; exit 1 }
$env:GH_TOKEN = (Get-Content "E:\work space\.gh_token" -Raw).Trim()

Write-Host "=== STEP 1/3: cleanup test files ==="
& $py tools\deploy.py cleanup
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: cleanup (continue anyway)" }

Write-Host "=== STEP 2/3: enable Pages ==="
& $py tools\deploy.py pages
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: pages"; exit $LASTEXITCODE }

Write-Host "=== STEP 3/3: trigger Actions ==="
& $py tools\deploy.py dispatch
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: dispatch"; exit $LASTEXITCODE }

Remove-Item "E:\work space\.gh_token" -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "ALL DONE."
Write-Host "  site: https://giuneipauliv-glitch.github.io/safety-job-hunter/"
Write-Host "  actions: https://github.com/giuneipauliv-glitch/safety-job-hunter/actions"
