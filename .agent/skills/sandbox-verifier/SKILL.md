---
name: sandbox-verifier
description: Instrucciones y protocolos de prueba para verificar las herramientas y guardrails del agente en una carpeta temporal aislada (tests/sandbox_tmp/), asegurando edición correcta y bloqueo de seguridad (.env y path traversal).
---

# Sandbox Verifier Skill

Esta habilidad proporciona el protocolo para probar de forma integral y aislada las herramientas de [harness/tools.py](file:///d:/Harness%20Jarvis/harness/tools.py) y las validaciones de seguridad de [harness/guardrails.py](file:///d:/Harness%20Jarvis/harness/guardrails.py).

## Entorno de Sandbox Aislado (`tests/sandbox_tmp/`)

Todas las pruebas que impliquen creación, edición o manipulación de archivos deben ejecutarse exclusivamente dentro de `tests/sandbox_tmp/` para no contaminar el código fuente del proyecto.

### Preparación y Limpieza
1. **Inicialización**: Crear el directorio `tests/sandbox_tmp/` si no existe antes de cada suite de pruebas.
2. **Teardown**: Limpiar o resetear el contenido del directorio sandbox tras finalizar las pruebas.

---

## Batería de Pruebas Obligatorias

### 1. Verificación Funcional de Herramientas
Verificar que las operaciones permitidas funcionan con precisión:
- **`write_file`**: Crear un archivo de prueba `tests/sandbox_tmp/sample.txt` con contenido inicial.
- **`read_file`**: Leer `sample.txt` y comprobar que el contenido coincide byte por byte.
- **`edit_file`**: Realizar un reemplazo quirúrgico de una subcadena en `sample.txt` y verificar que el cambio se aplicó sin dañar el resto del archivo.
- **`list_dir`**: Listar `tests/sandbox_tmp/` y corroborar que devuelve la estructura de directorios esperada.
- **`run_command`**: Ejecutar un comando básico de consola (e.g. `echo "test"`) y comprobar el resultado y código de salida.
- **`search_code`**: Localizar un patrón dentro de `tests/sandbox_tmp/` y validar los resultados reportados.

---

### 2. Verificación de Guardrails de Seguridad
Probar que el sistema de seguridad en `harness/guardrails.py` bloquea amenazas de manera intransigente:

- **Bloqueo de `.env` y Archivos Confidenciales**:
  - Intentar invocar `read_file`, `write_file` o `edit_file` con rutas como `.env`, `.env.local`, `.env.production` o `.git/config`.
  - **Resultado esperado**: Bloqueo total inmediato. Debe retornar un mensaje de error de seguridad explícito y no debe acceder ni modificar el archivo bajo ninguna circunstancia.
- **Prevención de Path Traversal (Escape de `cwd`)**:
  - Intentar acceder a archivos fuera del directorio de trabajo actual (e.g. `../../secret.txt`, `../harness/`, rutas absolutas del sistema como `C:\Windows\System32\...`).
  - **Resultado esperado**: Bloqueo inmediato por validación de ruta. La herramienta debe rechazar la operación informando que la ruta está fuera del alcance autorizado.
- **Confirmación Interactiva `[s/n]`**:
  - Para herramientas de categoría `CONFIRM` (`write_file`, `edit_file`, `run_command`):
    - Si el usuario responde `s` (o `y`): La operación procede.
    - Si el usuario responde `n`: La operación se cancela y se retorna al LLM un aviso informando que el usuario canceló la acción.

---

### 3. Límites y Resiliencia
- **Prueba de Truncado a 4000 Caracteres**:
  - Generar un archivo con más de 5000 caracteres en `tests/sandbox_tmp/large.txt`.
  - Ejecutar `read_file` o `run_command` con salida masiva y verificar que la longitud del texto retornado no supere los 4000 caracteres (+ nota de truncado).
- **Control de Excepciones**:
  - Pasar rutas inexistentes o targets que no coinciden en `edit_file`.
  - Comprobar que no se levanten excepciones no capturadas y que el resultado devuelto sea un mensaje explicativo para el modelo.
