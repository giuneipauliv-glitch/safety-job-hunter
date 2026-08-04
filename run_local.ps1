# 本地手动/计划任务运行脚本（Windows PowerShell）
# 用法：powershell -ExecutionPolicy Bypass -File run_local.ps1
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Set-Location $PSScriptRoot

# 选择 Python：优先系统 Python（排除 Windows 商店占位符），否则用项目便携版
$py = ""
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -and $cmd.Source -notlike "*WindowsApps*") {
    $py = $cmd.Source
}
if (-not $py) {
    $candidates = @(
        "E:\work space\.tools\py312\python.exe",
        "$env:USERPROFILE\.tools\py312\python.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $py = $c; break } }
}
if (-not $py) { Write-Host "未找到 Python，请安装或配置便携版路径"; exit 1 }

Write-Host "使用 Python: $py"
& $py run.py --backend chrome_dump --pages 2
$code = $LASTEXITCODE
if ($code -eq 2) {
    Write-Host "[警告] 本次抓取被智联反爬拦截（或网络异常），数据未更新。家庭宽带重试通常可成功。"
} elseif ($code -ne 0) {
    Write-Host "[错误] 运行失败，退出码 $code"
} else {
    Write-Host "[完成] 抓取并更新成功，可在 GitHub Pages 查看最新数据。"
}
exit $code
