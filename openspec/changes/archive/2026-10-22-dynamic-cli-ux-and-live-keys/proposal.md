# Proposal: Experiencia de Terminal Limpia, Gestión de Modelos y Memoria de Chat por Carpeta

## Why
La terminal interactiva actual incluye modelos de prueba quemados en código que confunden al usuario, carece de comandos para limpiar la pantalla o purgar la sesión, y no guarda el historial de conversación del proyecto entre ejecuciones. Inspirados en la elegancia de herramientas modernas como OpenCode, transformaremos la CLI en un entorno de desarrollo limpio, visual y dinámico, donde el usuario define y administra sus propios modelos, puede limpiar pantalla (`/clear`) y reiniciar sesión (`/reset`), y la conversación se preserva en un punto de memoria local por carpeta.

## What Changes
- **Cero modelos de prueba quemados**: Se elimina la lista preconfigurada estática. El catálogo de modelos es 100% administrado por el usuario mediante `/model add <proveedor> <modelo>` y `/model rm <id_o_nombre>`.
- **Selector numerado interactivo**: `/model` lista limpiamente los modelos propios registrados por el usuario con números de acceso rápido (`/model 1`).
- **Activación de claves en vivo**: `/key <proveedor> <clave>` inyecta la clave en `os.environ` inmediatamente sin reiniciar el proceso.
- **Punto de memoria de chat por carpeta**: El historial de mensajes se guarda localmente en el espacio de trabajo activo (`.harness_session.json`), permitiendo reanudar el trabajo en esa carpeta.
- **Comandos de limpieza**: `/clear` limpia la pantalla de la terminal y redibuja la interfaz limpia; `/reset` vacía la memoria de conversación de la carpeta.
- **Prompt dinámico contextual**: Muestra la carpeta de trabajo actual y el modelo activo (ejemplo: `[Pruebas | ⚡ groq:llama-3.3-70b-versatile] jarvis> `).

## Capabilities

### Modified Capabilities
- `cli-entrypoint`: Soporte para comandos de control de interfaz (`/clear`), prompt dinámico contextual y selector interactivo de modelos.
- `workspace-context`: Catálogo limpio de modelos definido por el usuario (sin modelos de prueba), comandos de adición/eliminación de modelos, y persistencia/reinicio del historial de chat por carpeta.

## Impact
- Actualizaciones en `main.py` y `harness/model_config.py`.
- No requiere dependencias pesadas; usa la biblioteca estándar de Python con manejo limpio de terminal multiplataforma.
- Fuera de alcance: Múltiples hilos de chat paralelos por carpeta o sincronización en la nube.
