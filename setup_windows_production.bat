@echo off
setlocal enabledelayedexpansion

REM Usage:
REM   1) Open Command Prompt as Administrator
REM   2) Run: setup_windows_production.bat
REM
REM What this script does (Windows production):
REM 1) Detects Python
REM 2) Creates a virtual environment (.venv-win)
REM 3) Installs app dependencies + waitress
REM 4) Creates/updates a Windows service
REM 5) Starts the service

cd /d "%~dp0"

set "APP_NAME=fixedcut"
set "PORT=8000"
set "VENV_DIR=.venv-win"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "RUNNER_BAT=run_fixedcut_service.bat"
set "PYTHON_CMD="

echo [0/6] Checking administrator privileges...
net session >nul 2>nul
if errorlevel 1 (
  echo Please run this script as Administrator.
  exit /b 1
)

call :detect_python
if not defined PYTHON_CMD (
  echo Python is not detected. Install Python 3.x and run this script again.
  exit /b 1
)

echo [1/6] Creating virtual environment...
if not exist "%PYTHON_EXE%" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 exit /b 1
)

echo [2/6] Upgrading pip/setuptools/wheel...
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

echo [3/6] Installing Python dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
"%PYTHON_EXE%" -m pip install waitress
if errorlevel 1 exit /b 1

echo [4/6] Creating service runner script...
(
  echo @echo off
  echo cd /d "%%~dp0"
  echo "%%~dp0.venv-win\Scripts\python.exe" -m waitress --listen=0.0.0.0:%PORT% server:app
) > "%RUNNER_BAT%"

echo [5/6] Creating/updating Windows service...
sc query "%APP_NAME%" >nul 2>nul
if not errorlevel 1 (
  sc stop "%APP_NAME%" >nul 2>nul
  sc delete "%APP_NAME%" >nul 2>nul
  timeout /t 2 /nobreak >nul
)

set "SERVICE_CMD=cmd.exe /c \"\"%CD%\%RUNNER_BAT%\"\""
sc create "%APP_NAME%" binPath= "%SERVICE_CMD%" start= auto DisplayName= "fixedcut Flask App (Waitress)" >nul
if errorlevel 1 (
  echo Failed to create service.
  exit /b 1
)

sc failure "%APP_NAME%" reset= 86400 actions= restart/5000/restart/5000/restart/5000 >nul

echo [6/6] Starting service...
sc start "%APP_NAME%" >nul
if errorlevel 1 (
  echo Failed to start service. Check Event Viewer for details.
  exit /b 1
)

echo Done. Service status:
sc query "%APP_NAME%"

echo.
echo Recent Windows Event Logs (System, Service Control Manager):
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Service Control Manager'; StartTime=(Get-Date).AddMinutes(-10)} -MaxEvents 20 | Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-List"

exit /b 0

:detect_python
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
  goto :eof
)

where python >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=python"
)
goto :eof