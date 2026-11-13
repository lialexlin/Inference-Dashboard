@echo off
rem Double-click this file to launch the dashboard (Windows twin of launch.command).
rem Starts a local web server on a free port, opens your browser, and stops
rem when you close this window or press Ctrl+C.
cd /d "%~dp0"
set PORT=
for /f %%p in ('uv run python -c "import socket; s=socket.socket(); s.bind((\"127.0.0.1\", 0)); print(s.getsockname()[1])"') do set PORT=%%p
if not defined PORT (
  echo   [ERROR] Could not start uv. Install it from https://docs.astral.sh/uv/ and try again.
  pause
  exit /b 1
)
echo.
echo   Inference Stack Dashboard: http://localhost:%PORT%
echo   Close this window or press Ctrl+C to stop.
echo.
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul & start "" http://localhost:%PORT%"
uv run python -m http.server %PORT% --bind 127.0.0.1
