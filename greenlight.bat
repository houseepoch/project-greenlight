@echo off
setlocal

echo.
echo  ========================================
echo   Project Greenlight
echo  ========================================
echo.

:: Check if setup has been run
if not exist "venv" (
    echo  First time? Run setup.bat first!
    echo.
    pause
    exit /b 1
)

:: Check for .env
if not exist ".env" (
    echo  ERROR: No .env file found!
    echo  Run setup.bat or copy .env.example to .env
    echo  and add your API keys.
    echo.
    pause
    exit /b 1
)

:: Clear any existing processes on ports 8000 and 3000
echo  [0/2] Clearing ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo        Killing process on port 8000 (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING" 2^>nul') do (
    echo        Killing process on port 3000 (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start backend API server
echo  [1/2] Starting Backend API (port 8000)...
start "Greenlight API" /min cmd /c "cd /d %~dp0 && call venv\Scripts\activate.bat && python -m greenlight 2>&1"

:: Wait for backend to initialize
echo        Waiting for backend to start...
timeout /t 3 /nobreak >nul

:: Check if backend started (try to connect)
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo        Backend starting... (may take a moment)
    timeout /t 2 /nobreak >nul
)

:: Start frontend
echo  [2/2] Starting Frontend (port 3000)...
start "Greenlight UI" /min cmd /c "cd /d %~dp0\web && npm run dev 2>&1"

:: Wait for frontend
echo        Waiting for frontend to start...
timeout /t 5 /nobreak >nul

:: Open browser
echo.
echo  Opening browser...
start http://localhost:3000

echo.
echo  ========================================
echo   Greenlight is running!
echo  ========================================
echo.
echo  Backend API: http://localhost:8000
echo  Frontend UI: http://localhost:3000
echo.
echo  To stop: Close this window or run stop.bat
echo.
echo  Press any key to keep this window open...
echo  (Servers will continue running in background)
echo.
pause >nul
