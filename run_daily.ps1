# Daily full update: cloud-safe sources (headless) + Zhaopin (headful, logged-in) + push
# 用法：powershell -ExecutionPolicy Bypass -File run_daily.ps1
# 建议配合 Windows 计划任务，每天 11:15 运行（智联登录态有效期内无需人工）
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

# locate python / git
$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") { $py = $cmd.Source }
if (-not $py) { foreach ($c in @("E:\work space\.tools\py312\python.exe", "$env:USERPROFILE\.tools\py312\python.exe")) { if (Test-Path $c) { $py = $c; break } } }
if (-not $py) { Write-Host "ERROR: python not found"; exit 1 }

$gitExe = ""
foreach ($c in @("C:\Program Files\HanaAgent\resources\git\mingw64\bin\git.exe",
                 "C:\Program Files\Git\cmd\git.exe")) { if (Test-Path $c) { $gitExe = $c; break } }
if (-not $gitExe) { $gc = Get-Command git -ErrorAction SilentlyContinue; if ($gc) { $gitExe = $gc.Source } }

Write-Host "=== STEP 1/3: 无头抓取（国聘/应届生网）==="
& $py run.py --backend chrome_dump --sources iguopin,yjs
$code = $LASTEXITCODE

Write-Host "=== STEP 2/3: 有头抓取智联（弹出 Chrome 属正常，跑完自动关）==="
& $py run.py --backend playwright_headful --sources zhaopin
$code2 = $LASTEXITCODE

Write-Host "=== STEP 3/3: 推送数据到 GitHub ==="
if ($gitExe -and (Test-Path "E:\work space\.gh_token")) {
    $env:GH_TOKEN = (Get-Content "E:\work space\.gh_token" -Raw).Trim()
    $remote = "https://giuneipauliv-glitch:$env:GH_TOKEN@github.com/giuneipauliv-glitch/safety-job-hunter.git"
    & $gitExe remote remove origin 2>$null | Out-Null
    & $gitExe remote add origin $remote 2>$null | Out-Null
    & $gitExe add data docs
    & $gitExe commit -m "daily data $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
    & $gitExe push origin main --force 2>&1 | Select-Object -Last 2
    & $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"
    Write-Host "数据已推送"
} else {
    Write-Host "未找到令牌文件（E:\work space\.gh_token），跳过推送。网页数据需手动更新。"
}

Write-Host ""
Write-Host "DONE. site: https://giuneipauliv-glitch.github.io/safety-job-hunter/"
