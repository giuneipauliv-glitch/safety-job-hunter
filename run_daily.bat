@echo off
rem Daily job launcher (used by Windows Task Scheduler)
rem runs the PowerShell daily update script with bypass policy
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_daily.ps1" >> "%~dp0logs\daily.log" 2>&1
