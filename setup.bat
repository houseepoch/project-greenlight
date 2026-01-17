@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================
echo   Project Greenlight - First Time Setup
echo  ========================================
echo.

:: Create temp directory for downloads
if not exist "temp_setup" mkdir temp_setup

:: Check for Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo       Python not found. Installing automatically...
    echo.
    echo       Downloading Python 3.12 installer...

    :: Download Python installer using PowerShell
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'temp_setup\python_installer.exe'}" 2>nul

    if not exist "temp_setup\python_installer.exe" (
        echo       ERROR: Failed to download Python installer.
        echo       Please install Python 3.10+ manually from https://python.org
        echo       Make sure to check "Add Python to PATH" during installation!
        pause
        exit /b 1
    )

    echo       Running Python installer (this may take a few minutes)...
    echo       IMPORTANT: The installer will add Python to your PATH automatically.
    echo.

    :: Silent install with PATH option
    temp_setup\python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

    if errorlevel 1 (
        echo       Automatic install failed. Launching manual installer...
        echo       IMPORTANT: Check "Add Python to PATH" at the bottom of the installer!
        start /wait temp_setup\python_installer.exe
    )

    :: Refresh PATH
    echo       Refreshing system PATH...
    call refreshenv >nul 2>&1

    :: Also try to add to current session PATH
    for /f "tokens=*" %%a in ('powershell -Command "[Environment]::GetEnvironmentVariable('Path', 'User')"') do set "PATH=%%a;%PATH%"

    :: Verify installation
    python --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo       Python installed but PATH not updated in this session.
        echo       Please CLOSE this window and run setup.bat again.
        echo.
        pause
        exit /b 1
    )
    echo       Python installed successfully!
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo       Found Python %PYVER%

:: Check for Node.js
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo       Node.js not found. Installing automatically...
    echo.
    echo       Downloading Node.js 20 LTS installer...

    :: Download Node.js installer using PowerShell
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile 'temp_setup\node_installer.msi'}" 2>nul

    if not exist "temp_setup\node_installer.msi" (
        echo       ERROR: Failed to download Node.js installer.
        echo       Please install Node.js 18+ manually from https://nodejs.org
        pause
        exit /b 1
    )

    echo       Running Node.js installer (this may take a few minutes)...
    echo.

    :: Silent install
    msiexec /i "temp_setup\node_installer.msi" /qn /norestart

    if errorlevel 1 (
        echo       Automatic install failed. Launching manual installer...
        start /wait msiexec /i "temp_setup\node_installer.msi"
    )

    :: Refresh PATH
    echo       Refreshing system PATH...
    call refreshenv >nul 2>&1

    :: Also try to add to current session PATH
    for /f "tokens=*" %%a in ('powershell -Command "[Environment]::GetEnvironmentVariable('Path', 'Machine')"') do set "PATH=%%a;%PATH%"

    :: Verify installation
    node --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo       Node.js installed but PATH not updated in this session.
        echo       Please CLOSE this window and run setup.bat again.
        echo.
        pause
        exit /b 1
    )
    echo       Node.js installed successfully!
)
for /f %%i in ('node --version') do set NODEVER=%%i
echo       Found Node.js %NODEVER%

:: Clean up temp downloads
if exist "temp_setup" (
    echo       Cleaning up installers...
    rmdir /s /q temp_setup 2>nul
)

:: Create Python virtual environment
echo [3/5] Setting up Python environment...
if not exist "venv" (
    echo       Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo       Activating virtual environment...
call venv\Scripts\activate.bat

echo       Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo       Python setup complete!

:: Install Node.js dependencies
echo [4/5] Setting up Node.js environment...
cd web
if not exist "node_modules" (
    echo       Installing Node.js dependencies (this may take a minute)...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
) else (
    echo       Node modules already installed.
)
cd ..
echo       Node.js setup complete!

:: Check for .env file
echo [5/5] Checking configuration...
if not exist ".env" (
    echo.
    echo  WARNING: No .env file found!
    echo  Copying .env.example to .env...
    copy .env.example .env >nul
    echo.
    echo  ========================================
    echo   ACTION REQUIRED: Add your API keys
    echo  ========================================
    echo.
    echo  Open .env in a text editor and add:
    echo.
    echo    XAI_API_KEY=xai-your-key-here
    echo    REPLICATE_API_TOKEN=r8_your-token-here
    echo.
    echo  Get keys from:
    echo    - xAI: https://x.ai
    echo    - Replicate: https://replicate.com
    echo.
) else (
    echo       Configuration file exists.
)

:: Create projects directory
if not exist "projects" mkdir projects

echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo  Next steps:
echo    1. Add your API keys to .env (if not done)
echo    2. Double-click "greenlight.bat" to start
echo.

pause
