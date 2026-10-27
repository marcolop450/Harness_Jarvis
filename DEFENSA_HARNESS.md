# Guía de defensa técnica: Harness Jarvis

## Qué implementa el arnés

Jarvis combina un adaptador de modelo, reglas, contexto del workspace, historial y herramientas. El modelo propone acciones; el programa valida, ejecuta y devuelve resultados. El bucle admite hasta 15 iteraciones por turno. Cada iteración puede contener varias llamadas a herramientas; no equivale a un límite de 15 herramientas ni a un timeout global del modelo.

## Módulos y recorrido de una solicitud

| Módulo | Responsabilidad |
| --- | --- |
| `main.py` | REPL, comandos, modo `-p` y ensamblado de herramientas. |
| `harness/llm_provider.py` | API compatible con OpenAI, proveedor, modelo y respuestas normalizadas. |
| `harness/agent_loop.py` | Historial, iteraciones y ejecución de llamadas solicitadas por el modelo. |
| `harness/tools.py` | Siete herramientas nativas, incluida SQLite. |
| `harness/mcp_client.py` | Configuración, procesos stdio, descubrimiento, llamadas y cierre. |
| `harness/mcp_policy.py` | Permisos locales por servidor, rutas y destinos públicos. |
| `harness/guardrails.py` | Secretos, contención y confirmaciones. |
| `harness/model_config.py` | Configuración de modelos y sesiones en JSON. |

```text
Usuario -> CLI -> modelo + historial + catálogo
                    |
                    v
              llamada de herramienta
                    |
           validación y autorización
              /                 \
     herramienta nativa       cliente MCP
                                  |
                         proceso servidor stdio
                                  |
                            resultado MCP
              \                 /
                  historial -> modelo -> respuesta
```

## Por qué estas integraciones sí son MCP

Hay tres procesos externos independientes: Fetch, Git y Filesystem. El SDK Python conecta por stdio, realiza la inicialización (modo legacy compatible), consulta `tools/list` recorriendo sus páginas y envía `tools/call`. Se convierten los esquemas descubiertos al catálogo que entiende el modelo.

Una función Python llamada `mcp_fetch` que usa HTTP directamente no demuestra MCP. Esas implementaciones antiguas se retiraron. SQLite permanece como herramienta nativa y no cuenta entre los tres servidores.

- **Fetch:** obtiene contenido web público y respeta robots.txt. El cliente valida la URL; el servidor fijado valida destinos y redirecciones.
- **Git:** consulta estado, historial y diferencias. El servidor ofrece más capacidades, pero Jarvis no expone commits ni modificaciones. Solo admite el repositorio del workspace.
- **Filesystem:** lee, busca y escribe archivos dentro del workspace. Las escrituras requieren confirmación, y se rechazan secretos, configuración protegida y enlaces externos.

Los nombres incluyen servidor: `mcp_fetch__fetch`, `mcp_git__git_log`, `mcp_filesystem__read_text_file`. Los servidores son externos al proceso del arnés aunque se ejecuten localmente; no necesitan cuentas ni estar alojados en Internet.

## Ciclo de vida, fallos y contexto

El REPL síncrono utiliza un hilo y una tarea asyncio propietaria por servidor. La misma tarea abre y cierra el contexto del SDK; las llamadas llegan por cola. Esto evita cerrar contextos AnyIO desde una tarea distinta.

Conexión y llamadas tienen un límite configurado de hasta 30 segundos. La limpieza de procesos puede añadir unos segundos. Una conexión fallida muestra error y puede reintentarse con `/mcp reconnect`; las herramientas nativas siguen disponibles. No existe un reemplazo HTTP/Git local oculto cuando falla MCP.

Los resultados se incorporan como mensajes `tool`, asociados al identificador de la llamada. Se limita el texto a 4000 caracteres incluyendo el aviso. Se conserva el historial en `.harness_session.json`, y las sesiones recuperables en `.harness_sessions/`. Los archivos históricos no se vuelven a ejecutar al cargarlos.

## Seguridad: qué afirmar y qué no

Las listas locales de herramientas autorizadas prevalecen sobre las anotaciones del servidor. Las validaciones cubren rutas simples y múltiples, enlaces que salen del workspace y archivos confidenciales. La configuración `mcp.json` puede lanzar procesos, por lo que debe revisarla una persona antes de confiar en un repositorio ajeno.

No afirmar que el sistema es infranqueable: no hay sandbox del SO. Un comando de consola autorizado corre con los permisos del usuario. Las validaciones tampoco eliminan todas las carreras frente a modificaciones concurrentes de archivos o DNS.

SQLite usa autorización de solo lectura para las consultas y solicita confirmación antes de mutaciones. ATTACH/DETACH, PRAGMA y carga de extensiones están bloqueados incluso con aprobación.

## Demostración breve

1. Iniciar con Ollama y ejecutar `/mcp`: tres servidores, once herramientas MCP.
2. Pedir una consulta a example.com con Fetch y mostrar `[MCP fetch/fetch] ok`.
3. Pedir los últimos commits con Git; explicar que no se expone la herramienta de commit.
4. Crear un archivo mediante Filesystem, mostrar la confirmación y leer el resultado.
5. Rechazar una escritura y comprobar que el archivo conserva su contenido.
6. Salir y explicar el cierre de los procesos.

`python -m scripts.mcp_demo --model qwen3.5:4b` reproduce la prueba con autorización limitada a un archivo temporal y evidencia de llamadas. Su aprobación automática es exclusiva del guion de prueba, no del uso normal.

## Estado y pendientes reconocidos

- Implementado y verificado: tres servidores MCP reales, configuración portable, políticas, trazas, CLI, historial y cierre.
- Función de subagente disponible en código, pero sin enlace desde la CLI: no afirmar que el agente ya delega tareas.
- Compactación previa no reparada: una falla de API puede reemplazar el historial por texto de error.
- 1500 tokens por llamada es un límite de salida, no una garantía contra cuotas ni respuestas truncadas. En la demo, Filesystem ejecutó escritura y lectura, pero el modelo emitió una respuesta final sin texto; se verificaron los tool_calls y el contenido del archivo.

## SDD y evidencia

El cambio `integrate-real-mcp-servers` se especificó y validó con OpenSpec antes de programar. Las tareas se implementaron secuencialmente y se marcaron al comprobar su comportamiento. Los resultados reproducibles están en `docs/VERIFICACION_MCP.md`. Los commits conservan autor y committer configurados, sin coautoría añadida.
