@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     Instalador de Harness Jarvis CLI (Windows)
echo ===================================================
echo.

:: 1. Verificar si Python esta instalado y en el PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python en el PATH del sistema.
    echo Por favor instala Python 3.10 o superior desde https://www.python.org/
    echo Asegurate de marcar la casilla "Add python.exe to PATH" durante la instalacion.
    if "%CI%"=="" if not "%1"=="--no-pause" pause
    exit /b 1
)

echo [OK] Python detectado:
python --version
echo.

:: 2. Instalar el paquete en modo editable con pip
echo [INFO] Instalando dependencias y registrando el comando 'jarvis'...
python -m pip install -e .
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar 'python -m pip install -e .'.
    if "%CI%"=="" if not "%1"=="--no-pause" pause
    exit /b %errorlevel%
)

echo.
echo [OK] Paquete instalado correctamente.
echo.

:: 3. Verificar si el comando jarvis esta en el PATH
where jarvis >nul 2>nul
if %errorlevel% equ 0 (
    echo ===================================================
    echo  Instalacion completada con exito!
    echo ===================================================
    echo Puedes ejecutar Jarvis desde cualquier terminal escribiendo:
    echo.
    echo    jarvis
    echo.
) else (
    echo [ADVERTENCIA] El comando 'jarvis' se instalo pero la carpeta 'Scripts'
    echo de Python no parece estar en tu variable PATH actual.
    echo.
    echo Puedes agregarlo a tus variables de entorno o ejecutarlo temporalmente con:
    echo.
    echo    python -m main
    echo.
)

if "%CI%"=="" if not "%1"=="--no-pause" pause
exit /b 0
