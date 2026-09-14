@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON_CMD if exist "%CODEX_PYTHON%" set "PYTHON_CMD=%CODEX_PYTHON%"
if not defined PYTHON_CMD (
    echo Python could not be found.
    pause
    exit /b 1
)
"%PYTHON_CMD%" -c "import pygame" >nul 2>nul
if errorlevel 1 "%PYTHON_CMD%" -m pip install -r requirements.txt
"%PYTHON_CMD%" robot_nightlight.py
if errorlevel 1 echo The nightlight stopped because of the error shown above.
pause
