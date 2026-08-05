# Daily full update: all sources headless (no popup windows), auto push
# 全源无头抓取：智联(登录态)/国聘/应届生网，不弹任何窗口，后台静默运行
# 用法：powershell -ExecutionPolicy Bypass -File run_daily.ps1
# 配合 Windows 计划任务每天 11:15 运行（智联登录态过期时需重跑 login_zhaopin.py）
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") { $py = $cmd.Source }
if (-not $py) { foreach ($c in @("E:\work space\.tools\py312\python.exe", "$env:USERPROFILE\.tools\py312\python.exe")) { if (Test-Path $c) { $py = $c; break } } }
if (-not $py) { Write-Host "ERROR: python not found"; exit 1 }

Write-Host "=== STEP 1/2: 无头全量抓取（智联/国聘/应届生网，不弹窗）==="
& $py run.py --backend chrome_dump
$code = $LASTEXITCODE
if ($code -eq 2) {
    Write-Host "[警告] 智联可能被拦（登录态过期？），可运行 login_zhaopin.py 重新登录后重试"
}

Write-Host "=== STEP 2/2: 推送数据到 GitHub ==="
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
    & $gitExe remote set-url origin "https://github.com/giuneipauliv-glitch/safety-job-hunter.git"
    Write-Host "数据已推送"
} else {
    Write-Host "未找到令牌或 git，跳过推送"
}

Write-Host ""
Write-Host "DONE. site: https://giuneipauliv-glitch.github.io/safety-job-hunter/"
