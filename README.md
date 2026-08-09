# Data Analyzer Pro

## Ejecución desde cualquier ordenador con Windows

### 1. Crear el entorno virtual e instalar dependencias
Ejecuta en PowerShell desde la carpeta raíz del repositorio:

```powershell
.\setup.bat
```

### 2. Iniciar la aplicación
Puedes hacerlo de tres formas:

```powershell
.\run.bat
```

O con doble clic en:

```text
launch.vbs
```

### Qué hace cada archivo
- `setup.bat` crea `.venv` y instala las dependencias del proyecto.
- `install_deps.bat` actualiza `pip` y vuelve a instalar `requirements.txt`.
- `run.bat` arranca `PROYECTO 2 UCR\main.py` usando el Python del `.venv`.

### Nota
Si el proyecto se copia a otro ordenador, basta copiar la carpeta completa y ejecutar `setup.bat` primero.
