@echo off
echo Starting Project Greenlight...
echo.

:: Start backend API server
echo [1/2] Starting Backend API (port 8000)...
start "Greenlight API" cmd /k "cd /d %~dp0 && python -m greenlight.api.main"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting Frontend (port 3000)...
start "Greenlight UI" cmd /k "cd /d %~dp0\web && npm run dev"

echo.
echo Both servers starting...
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:3000
echo.
echo Press any key to open the UI in your browser...
pause >nul
start http://localhost:3000
