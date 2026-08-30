@echo off
cd /d "%~dp0"
set "PYTHON_EXE=%~dp0\.venv\Scripts\pythonw.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0\.venv\Scripts\python.exe"
start "" "%PYTHON_EXE%" app.py
exit /b 0
