@echo off
setlocal
set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo ERROR: No se encontro el entorno virtual .venv\Scripts\python.exe
  echo Usa setup.bat para crear el entorno primero.
  exit /b 1
)
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r "%~dp0\requirements.txt"
