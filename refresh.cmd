@echo off
rem Double-click this file to refresh the data (Windows twin of refresh.command).
rem Takes about five minutes.
cd /d "%~dp0"
echo.
echo   Refreshing data, this takes about five minutes...
echo.
doppler run -- uv run python -m jobs.refresh
echo.
if errorlevel 1 (echo   [ERROR] Refresh failed, see the messages above.) else (echo   Done. You can close this window.)
pause
