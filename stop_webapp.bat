@echo off
title Stop Gemini Flow Web App
color 0C
cd /d "%~dp0"

echo ========================================================
echo          Stopping Gemini Flow Web Server
echo ========================================================
echo.
echo Searching for active process on port 5000...

set FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo Stopping process PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)

echo.
if "%FOUND%"=="1" (
    echo [SUCCESS] Gemini Flow server has been stopped.
) else (
    echo [INFO] No server was running on port 5000.
)
echo.
echo Window closing in 3 seconds...
ping 127.0.0.1 -n 4 >nul
