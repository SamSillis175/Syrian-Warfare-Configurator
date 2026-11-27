@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys, tkinter; sys.exit(sys.version_info < (3,10))" >nul 2>nul
    if not errorlevel 1 (
        py -3 "%~dp0Configurator.py"
        if errorlevel 1 pause
        exit /b
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys, tkinter; sys.exit(sys.version_info < (3,10))" >nul 2>nul
    if not errorlevel 1 (
        python "%~dp0Configurator.py"
        if errorlevel 1 pause
        exit /b
    )
)
echo Python 3.10 or newer with Tkinter is required.
echo Install Python from https://www.python.org/downloads/ and run this file again.
pause
exit /b 1
