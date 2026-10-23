# Spec Delta

## MODIFIED Requirements

### Requirement: Script automatizado de instalación en un solo paso para Windows
El sistema SHALL proveer un script de instalación automatizado `install.bat` que verifique la presencia de Python, instale el paquete en modo editable, registre la carpeta de scripts en el PATH de usuario si no está presente y actualice la sesión activa.

#### Scenario: Instalación exitosa en Windows
- **GIVEN** un sistema Windows con Python 3 y pip presentes en el PATH
- **WHEN** el usuario ejecuta `install.bat` desde CMD o mediante doble clic
- **THEN** el script instala el paquete en modo editable, detecta la ruta de ejecutables de Python, la registra de forma permanente en el PATH de usuario si no estaba presente y actualiza la sesión actual permitiendo ejecutar `jarvis` inmediatamente.

#### Scenario: Detección y manejo de ausencia de Python
- **GIVEN** un sistema donde `python` no está configurado en las variables de entorno PATH
- **WHEN** el usuario ejecuta `install.bat`
- **THEN** el script emite un mensaje de error explícito indicando la necesidad de instalar Python y aborta la ejecución con un código de salida distinto de cero.
