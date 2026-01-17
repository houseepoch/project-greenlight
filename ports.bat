@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================
echo   Port Manager - Project Greenlight
echo  ========================================
echo.

:: Check what's running on port 8000 (backend)
echo  Checking port 8000 (Backend)...
set "pid8000="
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    set "pid8000=%%a"
)

if defined pid8000 (
    echo    Found process: PID !pid8000!
    for /f "tokens=1" %%n in ('tasklist /fi "PID eq !pid8000!" /fo csv /nh 2^>nul') do (
        echo    Process name: %%~n
    )
) else (
    echo    Port 8000 is free
)

:: Check what's running on port 3000 (frontend)
echo.
echo  Checking port 3000 (Frontend)...
set "pid3000="
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3000" ^| findstr "LISTENING"') do (
    set "pid3000=%%a"
)

if defined pid3000 (
    echo    Found process: PID !pid3000!
    for /f "tokens=1" %%n in ('tasklist /fi "PID eq !pid3000!" /fo csv /nh 2^>nul') do (
        echo    Process name: %%~n
    )
) else (
    echo    Port 3000 is free
)

echo.
echo  ========================================
echo.

:: If nothing is running, exit
if not defined pid8000 if not defined pid3000 (
    echo  Both ports are free. Nothing to do.
    echo.
    pause
    exit /b 0
)

:: Ask user what to do
echo  Options:
echo    [1] Kill all (clear both ports)
echo    [2] Kill port 8000 only (backend)
echo    [3] Kill port 3000 only (frontend)
echo    [4] Cancel
echo.
set /p choice="  Enter choice (1-4): "

if "%choice%"=="1" goto :kill_all
if "%choice%"=="2" goto :kill_8000
if "%choice%"=="3" goto :kill_3000
if "%choice%"=="4" goto :cancel
goto :cancel

:kill_all
echo.
echo  Killing all processes on ports 8000 and 3000...
if defined pid8000 (
    taskkill /f /pid !pid8000! >nul 2>&1
    echo    Killed PID !pid8000! (port 8000)
)
if defined pid3000 (
    taskkill /f /pid !pid3000! >nul 2>&1
    echo    Killed PID !pid3000! (port 3000)
)
echo  Done!
goto :end

:kill_8000
echo.
if defined pid8000 (
    taskkill /f /pid !pid8000! >nul 2>&1
    echo  Killed PID !pid8000! (port 8000)
) else (
    echo  Port 8000 was already free
)
goto :end

:kill_3000
echo.
if defined pid3000 (
    taskkill /f /pid !pid3000! >nul 2>&1
    echo  Killed PID !pid3000! (port 3000)
) else (
    echo  Port 3000 was already free
)
goto :end

:cancel
echo.
echo  Cancelled.
goto :end

:end
echo.
pause
