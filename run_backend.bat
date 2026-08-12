@echo off
setlocal
set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo ERROR: No se encontro el entorno virtual .venv\Scripts\python.exe
  exit /b 1
)
"%PYTHON%" -m pip install -r backend\requirements.txt
"%PYTHON%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
