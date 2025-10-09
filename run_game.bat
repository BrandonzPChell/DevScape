@echo off
REM run_game.bat — A ceremonial gate to launch DevScape on Windows

REM --- Python Version Check ---
python -c "import sys; assert sys.version_info >= (3, 11)" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Python 3.11 or higher is required to run DevScape.
    ECHO Please install Python 3.11+ and ensure it's in your PATH.
    ECHO Download from: https://www.python.org/downloads/
    ECHO.
    PAUSE
    EXIT /b 1
)

REM --- Virtual Environment Setup and Activation ---
IF NOT EXIST .venv (
    ECHO Creating virtual environment...
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Failed to create virtual environment.
        PAUSE
        EXIT /b 1
    )
)

REM Activate the virtual environment
CALL .venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to activate virtual environment.
    PAUSE
    EXIT /b 1
)

REM --- Install/Update Dependencies ---
ECHO Checking for Python dependencies...
pip install -r game/requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to install Python dependencies.
    PAUSE
    EXIT /b 1
)

REM --- Launch the shrine ---
ECHO Launching DevScape...
python run_game.py

REM Keep the window open so the steward may see any omens
PAUSE
