@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=C:\Users\user\hsi-orderbook"
set "LOG_DIR=%PROJECT_DIR%\logs"
set "PYTHON=python.exe"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "LOG_FILE=%LOG_DIR%\%%c%%a%%b_collector.log"

cd /d "%PROJECT_DIR%"
"%PYTHON%" main.py >> "%LOG_FILE%" 2>&1
