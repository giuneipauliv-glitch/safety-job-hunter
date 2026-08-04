@echo off
rem 本地运行（cmd 双击亦可），推荐用 run_local.ps1
chcp 65001 >nul
cd /d "%~dp0"
python run.py --backend chrome_dump --pages 2
if errorlevel 2 echo [警告] 被反爬拦截或网络异常，请稍后重试
pause
