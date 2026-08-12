@echo off
setlocal
set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo ERROR: No se encontro el entorno virtual .venv\Scripts\python.exe
  exit /b 1
)
"%PYTHON%" "%~dp0\main.py"
