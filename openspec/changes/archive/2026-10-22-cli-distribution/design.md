# Design

## Context
Actualmente la aplicación se ejecuta de forma manual mediante `python main.py` desde el directorio raíz del repositorio. Para permitir una experiencia CLI estándar (análoga a herramientas como Claude Code) en cualquier equipo con Windows, se requiere empaquetar el proyecto bajo los estándares modernos de Python (PEP 518/621) y proveer scripts de instalación automatizados para CMD y PowerShell.

## Goals / Non-Goals

**Goals:**
- Definir `pyproject.toml` con metadata estándar (PEP 621) y punto de entrada de consola `jarvis = "main:main"`.
- Proporcionar `install.bat` (y soporte PowerShell) para instalación en un solo clic/comando.
- Detectar si la carpeta `Scripts` de Python está en el PATH de Windows y guiar al usuario.
- Incluir pruebas unitarias en `tests/test_distribution.py` validando la metadata y la invocabilidad del punto de entrada usando la biblioteca estándar (`tomllib` e `importlib`).

**Non-Goals:**
- Generar binarios independientes `.exe` compilados mediante PyInstaller o Nuitka.
- Publicar el paquete en PyPI o repositorios externos.
- Modificar la arquitectura o lógica de los módulos en `harness/`.

## Decisions

### 1. `pyproject.toml` (PEP 518/621) con backend `setuptools`
- **Decisión**: Utilizar `pyproject.toml` declarativo estándar con `setuptools.build_meta` como build-backend.
- **Alternativas consideradas**:
  - `setup.py` tradicional: Obsoleto en los estándares modernos de empaquetado de Python.
  - `poetry` / `hatch` / `flit`: Requerirían que el usuario instale herramientas de terceros previas a la instalación. `setuptools` y `pip` vienen preinstalados con Python en Windows.

### 2. Punto de entrada de consola: `jarvis = "main:main"`
- **Decisión**: Configurar `[project.scripts] jarvis = "main:main"`.
- **Alternativas consideradas**:
  - Registrar múltiples alias (`harness-jarvis`, `jarvis-agent`): Se opta por `jarvis` por brevedad y ergonomía de uso en la terminal.

### 3. Script automatizado `install.bat`
- **Decisión**: Proveer un script por lotes que:
  1. Verifique si `python` está presente en el PATH.
  2. Ejecute `python -m pip install -e .`.
  3. Verifique con `where jarvis` si el ejecutable está disponible en el PATH.
  4. Informe al usuario el resultado y los pasos para comenzar.
- **Alternativas consideradas**:
  - Instrucciones manuales en README: Propenso a errores en usuarios que no conocen la sintaxis de `pip install -e .`.

### 4. Pruebas unitarias de distribución con `tomllib`
- **Decisión**: Implementar `tests/test_distribution.py` usando `tomllib` (nativo en Python 3.11+) para parsear `pyproject.toml` y asegurar que `jarvis` apunta a `main:main`, verificando que la función `main` exista y sea invocable.

## Risks / Trade-offs

- **[Riesgo] La carpeta `Scripts` de Python no está en el PATH del usuario en Windows**  
  → *Mitigación*: `install.bat` ejecuta `where jarvis`. Si no se encuentra, emite una advertencia clara indicando la ruta exacta de `Scripts` para agregar al PATH o la alternativa inmediata `python -m main`.
- **[Riesgo] Permisos de escritura al instalar en un Python global del sistema**  
  → *Mitigación*: El comando `python -m pip install -e .` se ejecuta en el contexto del usuario o entorno virtual activo.
