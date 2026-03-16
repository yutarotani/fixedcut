#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$AppName = "fixedcut",
    [int]$Port = 8000,
    [string]$PythonMajor = "3"
)

# Usage:
#   1) Open PowerShell as Administrator
#   2) Set-ExecutionPolicy -Scope Process Bypass
#   3) .\setup_windows_production.ps1
#
# What this script does (Windows production):
# 1) Detects Python
# 2) Creates a virtual environment (.venv-win)
# 3) Installs app dependencies + waitress
# 4) Creates/updates a Windows service
# 5) Starts the service

function Write-Step {
    param([string]$Text)
    Write-Host $Text -ForegroundColor Cyan
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-PythonCommand {
    param([string]$Major)

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py -$Major"
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }

    throw "Python is not found. Install Python 3.x first, then rerun this script."
}

if (-not (Test-IsAdmin)) {
    throw "Run this script in an elevated PowerShell (Administrator)."
}

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv-win"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$RunnerBat = Join-Path $ProjectDir "run_fixedcut_service.bat"

Set-Location $ProjectDir

$pythonCmd = Get-PythonCommand -Major $PythonMajor

Write-Step "[1/6] Creating virtual environment..."
if (-not (Test-Path $PythonExe)) {
    & cmd /c "$pythonCmd -m venv `"$VenvDir`""
}

Write-Step "[2/6] Upgrading pip/setuptools/wheel..."
& $PythonExe -m pip install --upgrade pip setuptools wheel

Write-Step "[3/6] Installing Python dependencies..."
& $PythonExe -m pip install -r (Join-Path $ProjectDir "requirements.txt")
& $PythonExe -m pip install waitress

Write-Step "[4/6] Creating service runner script..."
$runnerContent = @"
@echo off
cd /d "%~dp0"
"%~dp0.venv-win\Scripts\python.exe" -m waitress --listen=0.0.0.0:$Port server:app
"@
Set-Content -Path $RunnerBat -Value $runnerContent -Encoding ASCII

Write-Step "[5/6] Creating/updating Windows service..."
$serviceExists = Get-Service -Name $AppName -ErrorAction SilentlyContinue
if ($serviceExists) {
    sc.exe stop $AppName | Out-Null
    sc.exe delete $AppName | Out-Null
    Start-Sleep -Seconds 2
}

$binPath = "cmd.exe /c `"`"$RunnerBat`"`""
sc.exe create $AppName binPath= "$binPath" start= auto DisplayName= "$AppName Flask App (Waitress)" | Out-Null
sc.exe failure $AppName reset= 86400 actions= restart/5000/restart/5000/restart/5000 | Out-Null

Write-Step "[6/6] Starting service..."
sc.exe start $AppName | Out-Null

Write-Host "Done. Service status:" -ForegroundColor Green
Get-Service -Name $AppName | Format-Table -AutoSize

Write-Host "`nRecent Windows Event Logs (System, Service Control Manager):" -ForegroundColor Green
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Service Control Manager'; StartTime=(Get-Date).AddMinutes(-10)} -MaxEvents 20 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message |
    Format-List