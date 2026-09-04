@echo off
title Gemini Flow Web App
color 0A
cd /d "%~dp0"

echo ========================================================
echo               Gemini Flow Web App
echo ========================================================
echo.
echo [1/2] Launching local server on port 5000...
echo [2/2] Opening your browser at http://localhost:5000 ...
echo.
echo * PC / Laptop: http://localhost:5000
echo * Phone (same Wi-Fi): Look at the Network IP below!
echo.
echo (To stop: Press Ctrl+C in this window or double-click stop_webapp.bat)
echo ========================================================
echo.

:: Launch browser after 2 seconds delay
start /b cmd /c "ping 127.0.0.1 -n 3 >nul & start http://localhost:5000"

:: Start the Python web application
python webapp.py --host 0.0.0.0 --port 5000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Web app stopped unexpectedly.
    pause
)
