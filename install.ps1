# ===================================================
#     Instalador de Harness Jarvis CLI (PowerShell)
# ===================================================
[CmdletBinding()]
param(
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Instalador de Harness Jarvis CLI (Windows)    " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar si Python esta instalado
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] No se encontro Python en el PATH del sistema." -ForegroundColor Red
    Write-Host "Por favor instala Python 3.10 o superior desde https://www.python.org/" -ForegroundColor Yellow
    Write-Host "Asegurate de marcar la casilla 'Add python.exe to PATH' durante la instalacion." -ForegroundColor Yellow
    if (-not $NoPause -and -not $env:CI) {
        Read-Host "Presiona Enter para salir..."
    }
    exit 1
}

$pyVersion = & python --version
Write-Host "[OK] Python detectado: $pyVersion" -ForegroundColor Green
Write-Host ""

# 2. Instalar el paquete en modo editable con pip
Write-Host "[INFO] Instalando dependencias y registrando el comando 'jarvis'..." -ForegroundColor Cyan
try {
    & python -m pip install -e .
    if ($LASTEXITCODE -ne 0) {
        throw "pip install salio con codigo de error $LASTEXITCODE"
    }
}
catch {
    Write-Host ""
    Write-Host "[ERROR] Hubo un problema al ejecutar 'python -m pip install -e .': $_" -ForegroundColor Red
    if (-not $NoPause -and -not $env:CI) {
        Read-Host "Presiona Enter para salir..."
    }
    exit 1
}

Write-Host ""
Write-Host "[OK] Paquete instalado correctamente." -ForegroundColor Green
Write-Host ""

# 3. Verificar si el comando jarvis esta en el PATH
$jarvisCmd = Get-Command jarvis -ErrorAction SilentlyContinue
if ($jarvisCmd) {
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host "  Instalacion completada con exito!" -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host "Puedes ejecutar Jarvis desde cualquier terminal escribiendo:"
    Write-Host ""
    Write-Host "   jarvis" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[ADVERTENCIA] El comando 'jarvis' se instalo pero la carpeta 'Scripts'" -ForegroundColor Yellow
    Write-Host "de Python no parece estar en tu variable PATH de esta sesion." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Puedes reiniciar tu terminal o ejecutarlo temporalmente con:"
    Write-Host ""
    Write-Host "   python -m main" -ForegroundColor Cyan
    Write-Host ""
}

if (-not $NoPause -and -not $env:CI) {
    Read-Host "Presiona Enter para finalizar..."
}
