@echo off
echo.
echo  ========================================
echo   Project Greenlight - Setup
echo  ========================================
echo.

echo [1/4] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo       ERROR: Python not found in PATH
    echo       Install from https://python.org
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo       ERROR: Node.js not found in PATH
    echo       Install from https://nodejs.org
    pause
    exit /b 1
)
node --version
echo.

echo [3/4] Setting up Python environment...
if not exist "venv" (
    echo       Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo       Installing packages...
pip install -r requirements.txt
echo.

echo [4/4] Setting up frontend...
cd web
echo       Installing npm packages...
call npm install
cd ..
echo.

if not exist ".env" (
    copy .env.example .env
    echo.
    echo  *** Add your API keys to .env ***
    echo.
)

if not exist "projects" mkdir projects

echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo  Next: Run greenlight.bat
echo.
pause
