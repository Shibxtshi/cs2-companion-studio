@echo off
setlocal
cd /d "%~dp0"
echo CS2 Companion Studio - Guided installation (Windows PowerShell)
echo Run only from a trusted downloaded archive.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1"
if errorlevel 1 echo.
if errorlevel 1 echo Installation stopped. See error above.
echo.
pause
