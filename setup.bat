@echo off
setlocal
set PYTHON=%~dp0.venv\Scripts\python.exe
if exist "%PYTHON%" (
  echo Entorno virtual ya existe.
  exit /b 0
)
python -m venv "%~dp0.venv"
if errorlevel 1 (
  echo ERROR: No se pudo crear el entorno virtual.
  exit /b 1
)
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r "%~dp0\requirements.txt"
if errorlevel 1 (
  echo ERROR: No se pudieron instalar las dependencias.
  exit /b 1
)
echo Entorno virtual creado y dependencias instaladas.
