@echo off
setlocal enableextensions
cd /d "%~dp0"
title SeeChat - Studio LAN Messenger Server
color 0B

echo =======================================================
echo     SeeChat - PYTHON LAN MESSENGER LAUNCHER
echo =======================================================
echo.

:: Detect Python executable (python, py, or python3)
set "PY_CMD="
where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>&1 && set "PY_CMD=py"
)
if not defined PY_CMD (
    where python3 >nul 2>&1 && set "PY_CMD=python3"
)

if not defined PY_CMD (
    echo [ERROR] Python was not detected in PATH!
    echo.
    echo Please install Python and check "Add Python to PATH":
    echo 👉 https://www.python.org/downloads/
    echo =======================================================
    pause
    exit /b
)

echo [INFO] Using Python command: %PY_CMD%
echo [INFO] Opening Desk Ping in browser...
start http://127.0.0.1:8080

echo.
echo [INFO] Starting Desk Ping Server on Port 8080...
echo.
%PY_CMD% server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with error code %errorlevel%.
)

pause
