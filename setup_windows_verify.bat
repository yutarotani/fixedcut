@echo off
setlocal enabledelayedexpansion

REM Usage:
REM   Double-click or run from cmd: setup_windows_verify.bat
REM
REM What this script does (Windows verification):
REM 1) Installs Python (if missing)
REM 2) Adds Python paths to user PATH environment variable
REM 3) Creates a local virtual environment
REM 4) Installs app dependencies (without gunicorn)
REM 5) Starts the Flask app

cd /d "%~dp0"

set "VENV_DIR=.venv-win"
set "PYTHON_CMD="

call :detect_python
if not defined PYTHON_CMD (
  echo Python is not detected. Trying to install Python 3.11 with winget...
  where winget >nul 2>nul
  if errorlevel 1 (
    echo winget is not available. Please install Python 3.11 manually and re-run this script.
    exit /b 1
  )

  winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo Python installation failed.
    exit /b 1
  )

  echo Updating user PATH environment variable for Python...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$p1 = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311'; $p2 = Join-Path $p1 'Scripts'; $current = [Environment]::GetEnvironmentVariable('Path','User'); if ([string]::IsNullOrWhiteSpace($current)) { $current = '' }; $parts = @($current -split ';' | Where-Object { $_ -and $_.Trim() -ne '' }); foreach ($p in @($p1, $p2)) { if (-not ($parts -contains $p)) { $parts += $p } }; $newPath = ($parts -join ';'); [Environment]::SetEnvironmentVariable('Path', $newPath, 'User'); Write-Host 'User PATH updated.'"
  if errorlevel 1 (
    echo Failed to update user PATH. You may need to add Python paths manually.
  )

  set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

  call :detect_python
  if not defined PYTHON_CMD (
    echo Python was installed but is still not detected in this session.
    echo Open a new terminal and run this script again.
    exit /b 1
  )
)

echo [1/5] Creating virtual environment...
call %PYTHON_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 exit /b 1

echo [2/5] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

echo [3/5] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [4/5] Setting user environment variables for verification...
setx FIXEDCUT_ENV "windows-verify" >nul
setx PYTHONUTF8 "1" >nul

echo [5/5] Starting app (without gunicorn)...
python -c "from fixedcut_app import app; app.run(host='127.0.0.1', port=5000, debug=True)"

endlocal

goto :eof

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
