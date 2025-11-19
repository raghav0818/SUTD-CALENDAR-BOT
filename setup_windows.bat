@echo off
echo ==================================================
echo   SUTD Calendar Bot - Dependency Installer
echo ==================================================
echo.

:: 1. Fix Directory: Switch to the folder where this script is located
cd /d "%~dp0"

:: 2. Install
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

:: 3. Check for errors
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed! 
    echo Please ensure you have Python installed and added to PATH.
    echo.
    pause
    exit /b
)

echo.
echo [SUCCESS] All dependencies installed!
echo You can now run the bot by double-clicking 'run_bot.bat' or running the python command.
echo.
pause