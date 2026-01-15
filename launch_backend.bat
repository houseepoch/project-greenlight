@echo off
echo Starting Project Greenlight Backend...

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python -m greenlight server --port 8000 --reload
