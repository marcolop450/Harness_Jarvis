@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     Instalador de Harness Jarvis CLI (Windows)
echo ===================================================
echo.

:: 1. Verificar si Python esta instalado y en el PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PATH=%LOCALAPPDATA%\Python\bin;!PATH!"
    if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" set "PATH=%LOCALAPPDATA%\Microsoft\WindowsApps;!PATH!"
)

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
    echo Si tienes una sesion de 'jarvis' abierta en otra ventana de consola,
    echo por favor cierrala e intentalo nuevamente.
    if "%CI%"=="" if not "%1"=="--no-pause" pause
    exit /b %errorlevel%
)

echo.
echo [OK] Paquete instalado correctamente.
echo.

:: 3. Configurar la carpeta Scripts en el PATH de usuario si no esta presente
echo [INFO] Verificando registro en PATH del usuario...
python -c "import sysconfig, winreg; s = sysconfig.get_path('scripts'); k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE); v = ''; (v, _) = winreg.QueryValueEx(k, 'Path'); (winreg.SetValueEx(k, 'Path', 0, winreg.REG_EXPAND_SZ, (v.rstrip(';') + ';' + s).strip(';')), print('[OK] Ruta de scripts anadida permanentemente al PATH del usuario.')) if s.lower() not in v.lower() else print('[OK] La ruta de scripts ya se encuentra en el PATH.')"

:: 4. Actualizar la variable PATH en la sesion activa actual
for /f "delims=" %%I in ('python -c "import sysconfig; print(sysconfig.get_path('scripts'))"') do (
    set "PATH=%%I;!PATH!"
)

echo.
:: 5. Verificar disponibilidad del comando jarvis
where jarvis >nul 2>nul
if %errorlevel% equ 0 (
    echo ===================================================
    echo  Instalacion completada con exito!
    echo ===================================================
    echo El comando 'jarvis' quedo configurado permanentemente en tu sistema.
    echo Puedes ejecutar Jarvis desde cualquier terminal escribiendo:
    echo.
    echo    jarvis
    echo.
) else (
    echo [ADVERTENCIA] No se pudo verificar 'jarvis' en el PATH inmediato.
    echo Puedes ejecutarlo directamente desde la carpeta del proyecto con:
    echo.
    echo    jarvis
    echo    python -m main
    echo.
)

if "%CI%"=="" if not "%1"=="--no-pause" pause
exit /b 0
