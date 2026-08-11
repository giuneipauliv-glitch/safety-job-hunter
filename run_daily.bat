@echo off
rem Daily job launcher (used by Windows Task Scheduler)
rem minimized window so it never blocks the screen
if not "%1"=="silent" (
  start "" /min cmd /c "%~f0" silent
  exit
)
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_daily.ps1" >> "%~dp0logs\daily.log" 2>&1
