@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\apply-settings.ps1"
if errorlevel 1 echo Settings were not confirmed. See error above.
echo.
pause
