@echo off
echo.
echo  Stopping Greenlight...
echo.

taskkill /fi "WINDOWTITLE eq Greenlight-API*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Greenlight-UI*" /f >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo  Done.
echo.
pause
