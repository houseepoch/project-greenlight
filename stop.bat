@echo off
echo.
echo  Stopping Project Greenlight...
echo.

:: Kill Python processes (backend)
echo  [1/2] Stopping Backend...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Greenlight API*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Greenlight API*" >nul 2>&1

:: Kill Node processes (frontend)
echo  [2/2] Stopping Frontend...
taskkill /f /im node.exe /fi "WINDOWTITLE eq Greenlight UI*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Greenlight UI*" >nul 2>&1

:: Also try to kill by port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo  Greenlight stopped.
echo.
pause
