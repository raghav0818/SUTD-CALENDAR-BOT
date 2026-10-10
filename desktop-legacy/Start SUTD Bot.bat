@echo off
REM ============================================================
REM  SUTD Calendar Bot - just double-click this file.
REM  No code editor needed. Sets itself up the first time.
REM ============================================================
title SUTD Calendar Bot
cd /d "%~dp0"

REM --- Find Python (the py launcher first, then a plain python) ---
set PY=
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1 && set "PY=python"
)

if not defined PY (
  echo.
  echo   Python is not installed on this computer.
  echo.
  echo   I'm opening the download page for you now.
  echo   Install it, then TICK "Add python.exe to PATH" on the first screen,
  echo   then double-click this file again.
  echo.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)

REM --- First run: build a private .venv so we never touch system Python ---
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   First-time setup. This takes a minute, only happens once.
  echo.
  %PY% -m venv .venv
  if errorlevel 1 goto setupfailed
  ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
  if errorlevel 1 goto setupfailed
  echo   Setup done.
  echo.
)

".venv\Scripts\python.exe" sutd_calendar_bot.py
if errorlevel 1 (
  echo.
  echo   The bot stopped with an error. Details are in sutd_bot.log
  echo   If this keeps happening, delete the ".venv" folder and run this again.
  echo.
  pause
)
exit /b 0

:setupfailed
echo.
echo   Setup failed - most likely no internet connection.
echo   Connect to wifi and double-click this file again.
echo.
pause
exit /b 1
