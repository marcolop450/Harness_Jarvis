# Spec Delta

## Purpose
Proporciona el empaquetado estandarizado de Python y scripts automatizados de instalación para permitir la ejecución global del agente CLI mediante el comando `jarvis` en cualquier PC con Windows.

## ADDED Requirements

### Requirement: Empaquetado estándar e instalación como script de consola
El sistema SHALL definir los metadatos de empaquetado del proyecto en `pyproject.toml` registrando el script de consola `jarvis` vinculado al punto de entrada `main:main`.

#### Scenario: Instalación editable y registro del comando global
- **GIVEN** un entorno de sistema operativo con Python 3.10+ y pip instalado
- **WHEN** se ejecuta `pip install -e .` en la raíz del repositorio
- **THEN** el ejecutable `jarvis` queda disponible en el PATH del sistema apuntando a `main:main`.

#### Scenario: Invocación de la CLI desde cualquier directorio
- **GIVEN** el paquete `jarvis` instalado en el entorno
- **WHEN** el usuario escribe el comando `jarvis` desde cualquier directorio en CMD o PowerShell
- **THEN** se inicializa la interfaz de terminal interactiva del agente.

### Requirement: Script automatizado de instalación en un solo paso para Windows
El sistema SHALL proveer un script de instalación automatizado `install.bat` que verifique la presencia de Python, instale el paquete en modo editable y reporte el estado de la instalación.

#### Scenario: Instalación exitosa en Windows
- **GIVEN** un sistema Windows con Python 3 y pip presentes en el PATH
- **WHEN** el usuario ejecuta `install.bat` desde CMD o mediante doble clic
- **THEN** el script ejecuta la instalación editable, verifica la salida y confirma que `jarvis` está listo para usarse.

#### Scenario: Detección y manejo de ausencia de Python
- **GIVEN** un sistema donde `python` no está configurado en las variables de entorno PATH
- **WHEN** el usuario ejecuta `install.bat`
- **THEN** el script emite un mensaje de error explícito indicando la necesidad de instalar Python y aborta la ejecución con un código de salida distinto de cero.

### Requirement: Verificación automatizada de empaquetado y punto de entrada
El sistema SHALL incluir pruebas unitarias automatizadas que validen la sintaxis de configuración del empaquetado y la importabilidad del punto de entrada.

#### Scenario: Validación de configuración de scripts de consola
- **GIVEN** la suite de pruebas unitarias
- **WHEN** se ejecuta la prueba de configuración de distribución
- **THEN** se valida que `pyproject.toml` declare la clave `project.scripts` con `jarvis = "main:main"` y que `main.py:main` sea invocable.
