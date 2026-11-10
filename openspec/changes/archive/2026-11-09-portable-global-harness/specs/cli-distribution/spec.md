# Spec Delta: cli-distribution

## MODIFIED Requirements

### Requirement: Empaquetado estándar e instalación como script de consola
El sistema SHALL definir los metadatos de empaquetado del proyecto en `pyproject.toml` registrando el script de consola `jarvis` vinculado al punto de entrada `main:main`, incluyendo plantillas no-código en `package_data` para garantizar funcionalidad al instalar vía Git o pip remoto.

#### Scenario: Instalación editable y registro del comando global
- **GIVEN** un entorno de sistema operativo con Python 3.10+ y pip instalado
- **WHEN** se ejecuta `pip install -e .` en la raíz del repositorio
- **THEN** el ejecutable `jarvis` queda disponible en el PATH del sistema apuntando a `main:main`.

#### Scenario: Instalación directa desde repositorio remoto Git
- **GIVEN** un entorno de sistema operativo con Python 3.10+ y git instalado
- **WHEN** se ejecuta `pip install git+https://github.com/usuario/harness-jarvis.git`
- **THEN** el paquete se instala en `site-packages` incluyendo sus plantillas de configuración y el comando `jarvis` queda operativo en cualquier carpeta.

#### Scenario: Invocación de la CLI desde cualquier directorio
- **GIVEN** el paquete `jarvis` instalado en el entorno
- **WHEN** el usuario escribe el comando `jarvis` desde cualquier directorio en CMD o PowerShell
- **THEN** se inicializa la interfaz de terminal interactiva del agente.
