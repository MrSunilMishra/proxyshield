@echo off
REM ==============================================================================
REM ProxyShield - Windows Automated 1-Click Bootstrap & Launch Script
REM
REM Author: Quarkova
REM Organization: Quarkova
REM Website: https://quarkova.com
REM License: MIT
REM ==============================================================================

cd /d "%~dp0"

echo [ProxyShield Bootstrap] Checking environment...

where uv >nul 2>&1
if not errorlevel 1 goto UV_READY

if exist "%USERPROFILE%\.cargo\bin\uv.exe" goto USE_CARGO
if exist "%USERPROFILE%\.local\bin\uv.exe" goto USE_LOCAL

echo [!] Installing standalone uv package manager...
powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"

:USE_CARGO
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
goto UV_READY

:USE_LOCAL
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
goto UV_READY

:UV_READY
if not exist ".venv" goto CREATE_VENV
goto CHECK_INSTALL

:CREATE_VENV
echo [*] Creating isolated virtual environment (.venv)...
uv venv .venv

:CHECK_INSTALL
if not exist ".venv\.installed" goto DO_INSTALL
goto LAUNCH

:DO_INSTALL
echo [*] Installing ProxyShield dependencies...
uv pip install -e .[dev]
echo installed > ".venv\.installed"

:LAUNCH
echo [OK] Launching ProxyShield (pxs)...
echo.
.\.venv\Scripts\python.exe -m proxyshield.cli %*
