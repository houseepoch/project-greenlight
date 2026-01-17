@echo off
echo.
echo  ========================================
echo   Project Greenlight
echo  ========================================
echo.

if not exist "venv" (
    echo  Run setup.bat first!
    pause
    exit /b 1
)

if not exist ".env" (
    echo  No .env file. Run setup.bat first!
    pause
    exit /b 1
)

echo  Starting backend...
start "Greenlight-API" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python -m greenlight server"

timeout /t 3 /nobreak >nul

echo  Starting frontend...
start "Greenlight-UI" cmd /k "cd /d %~dp0web && npm run dev"

timeout /t 5 /nobreak >nul

echo  Opening browser...
start http://localhost:3000

echo.
echo  ========================================
echo   Running!
echo  ========================================
echo.
echo  Backend: http://localhost:8000
echo  Frontend: http://localhost:3000
echo.
echo  To stop: Close the terminal windows
echo           or run stop.bat
echo.
pause
