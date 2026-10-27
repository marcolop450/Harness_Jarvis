# Harness Jarvis

Agente de terminal en Python con herramientas nativas y **tres servidores MCP reales**: Fetch, Git y Filesystem. Funciona con Ollama o proveedores compatibles con la API de OpenAI.

## Inicio en este equipo (Windows)

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -X utf8 main.py --provider ollama --model qwen3.5:4b
```

Dentro de Jarvis:

```text
/mcp
/model add ollama qwen3.5:4b
Usa mcp_git__git_log para resumir los últimos tres commits de este repositorio.
```

`/model add` recuerda la selección. Después basta ejecutar `main.py` sin parámetros. Ollama debe estar funcionando y tener el modelo descargado. Las claves de nube se configuran con `/key <proveedor> <clave>`; no hacen falta para Ollama ni para estos servidores MCP.

## Instalación reproducible

Requisitos: Python >=3.10, Git, Node.js/npm para instalar dependencias y un modelo con soporte de herramientas. En Python 3.10, instalar también `tomli` para ejecutar la suite de pruebas.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
npm.cmd ci --no-audit --no-fund
.\.venv\Scripts\python.exe -m pip check
```

En Linux/macOS usar `.venv/bin/python` y `npm ci`. El paquete npm `node` instala **Node 24.15.0 dentro de node_modules**: no cambia el Node global ni el PATH. npm puede advertir sobre el Node global anterior durante la instalación; el servidor se ejecuta con el Node local fijado.

| Componente | Versión fijada |
| --- | --- |
| SDK Python MCP | 2.3.0 |
| Fetch | 2026.10.24 |
| Git | 2026.10.19 |
| Filesystem | 2.0.1 |
| Node local | 24.15.0 |

`package-lock.json` fija las dependencias npm. Python declara las versiones de SDK y servidores en `pyproject.toml`; sus dependencias transitivas se resuelven con pip. `requirements.txt` apunta al mismo proyecto. No hay descargas al iniciar Jarvis.

Los instaladores antiguos `install.bat`/`install.ps1` registran el paquete Python globalmente; para instalar también Filesystem y mantener aislamiento, usar los comandos anteriores. El comando `jarvis` queda disponible dentro del entorno virtual.

## Configuración MCP por proyecto

Jarvis carga únicamente `mcp.json` de la carpeta de trabajo. Sin ese archivo funciona con herramientas nativas. Para otra carpeta, copiar allí la configuración y ejecutar el Python del entorno de Jarvis o su comando instalado.

- `${python}`: intérprete que ejecuta Jarvis.
- `${workspace}`: carpeta actual autorizada.
- `${project}`: ubicación de la instalación de Jarvis.
- `${node}`: ejecutable Node local del proyecto, portable entre Windows y Unix.
- `allowed_tools`: subconjunto de herramientas habilitadas; nunca amplía la política del cliente.
- `timeout_seconds`: límite de conexión y llamada, 30 segundos por defecto y máximo.
- `enabled: false`: desactiva un servidor antes de iniciar la sesión.

**mcp.json es configuración ejecutable de confianza:** sus comandos arrancan procesos. Revísalo antes de usarlo en un repositorio ajeno. Las herramientas de archivos de Jarvis no pueden editarlo. Reinicia Jarvis tras cambiar la configuración; `/mcp reconnect` reintenta las conexiones fallidas con la configuración cargada.

Las conexiones se abren de forma perezosa al consultar `/mcp` o enviar el primer turno al modelo. Se conservan durante la sesión y se cierran al salir. En `-p` se cierran al terminar la solicitud. Un servidor fallido no impide usar los demás ni las herramientas nativas.

## Herramientas y permisos

| Servidor | Herramientas expuestas | Política |
| --- | --- | --- |
| Fetch | `mcp_fetch__fetch` | HTTP/HTTPS público en puertos 80/443; bloqueo local y validación en servidor de cada redirección y robots.txt. |
| Git | `mcp_git__git_status`, `git_log`, `git_diff_unstaged`, `git_diff_staged` (todas con prefijo `mcp_git__`) | Solo el repositorio activo y solo lectura. Si un diff incluye secretos o configuración protegida, se rechaza completo. |
| Filesystem | `read_text_file`, `read_multiple_files`, `list_directory`, `search_files`, `write_file`, `edit_file` (con prefijo `mcp_filesystem__`) | Rutas dentro del workspace, bloqueo de secretos y confirmación antes de escribir. |

Son **11 herramientas MCP** descubiertas por protocolo y **7 nativas**: `read_file`, `write_file`, `edit_file`, `list_dir`, `run_command`, `search_code`, `sqlite_query`.

SQLite ya no se presenta como MCP. Las consultas no mutan archivos; las escrituras requieren aprobación. Se bloquean ATTACH/DETACH, PRAGMA y carga de extensiones. Los antiguos nombres `mcp_fetch`, `mcp_git_info` y `mcp_sqlite_query` no se ejecutan; los historiales existentes siguen siendo legibles y no se reproducen automáticamente.

Cada llamada MCP muestra `[MCP servidor/herramienta] ok` o `error`, sin imprimir sus argumentos. Los resultados llegan al modelo con un máximo de 4000 caracteres, incluyendo el aviso de truncado. Las descripciones descubiertas son datos del servidor, no instrucciones de confianza del proyecto.

## Comandos

| Comando | Función |
| --- | --- |
| `/mcp` | Estado, errores y herramientas disponibles; funciona sin modelo configurado. |
| `/mcp reconnect` | Reconectar servidores fallidos. |
| `/model`, `/model add <proveedor> <modelo>` | Consultar y registrar modelos. |
| `/key <proveedor> <clave>` | Configurar credencial del proveedor LLM en `.env`. |
| `/sessions`, `/resume <id>` | Listar y recuperar sesiones. |
| `/compact` | Resumir el contexto con el modelo activo. |
| `/cwd`, `/guide`, `/clear`, `/reset`, `exit` | Carpeta, ayuda, pantalla, conversación y salida. |

Ejemplo directo:

```powershell
.\.venv\Scripts\python.exe -X utf8 main.py --provider ollama --model qwen3.5:4b -p "Usa mcp_fetch__fetch para consultar https://example.com y resume su contenido."
```

## Pruebas y demostración

```powershell
# Unitarias y regresión: sin red ni modelos reales
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p "test_*.py" -v

# Servidores reales: requiere dependencias instaladas e Internet
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p "integration_mcp.py" -v

# Modelo real: requiere Ollama y qwen3.5:4b descargado
.\.venv\Scripts\python.exe -X utf8 -m scripts.mcp_demo --model qwen3.5:4b
```

La demo comprueba tool_calls y eventos reales, autoriza exclusivamente su archivo temporal y guarda `.mcp-demo/resultado-ollama.json` (ignorado por Git). No basta una respuesta textual del modelo para pasar. Ver `docs/VERIFICACION_MCP.md` para resultados y `DEFENSA_HARNESS.md` para explicar la arquitectura.

## Límites conocidos

- Los guardrails no constituyen un sandbox del sistema operativo: `run_command` aprobado tiene los permisos del usuario. Los servidores y la configuración deben ser confiables.
- La resolución DNS y las validaciones de rutas no aíslan cambios concurrentes maliciosos de DNS o del sistema de archivos.
- Fetch puede rechazar páginas por robots.txt, TLS o conectividad; no se evita esa restricción.
- Git requiere iniciar en la raíz de un repositorio con `.git`.
- `run_subagent` existe pero aún no está conectado a la CLI; no se implementó delegación en este cambio.
- La compactación conserva su comportamiento previo, incluido el problema conocido si falla la generación del resumen.
- El límite previo de 1500 tokens por llamada puede producir una respuesta final vacía con modelos que consumen ese presupuesto razonando, incluso después de ejecutar herramientas correctamente. La traza y el archivo resultante permiten distinguirlo de una herramienta no ejecutada.

## Desarrollo SDD

Se usa OpenSpec `spec-driven`: propuesta -> especificaciones Dado/Cuando/Entonces -> diseño -> tareas -> implementación y pruebas por tarea -> sincronización -> archivo. No modificar código sin tarea activa. Conservar la identidad Git configurada y no añadir atribuciones automáticas de coautoría.
