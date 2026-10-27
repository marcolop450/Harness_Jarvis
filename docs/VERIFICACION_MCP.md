# Verificación y Aceptación: Servidores MCP Reales en Harness Jarvis

Este documento registra los resultados reproducibles y las evidencias de validación de la integración de tres servidores MCP externos independientes en Harness Jarvis, conforme al plan de cambio `integrate-real-mcp-servers` bajo metodología SDD con OpenSpec.

---

## 1. Arquitectura de Integración MCP

Jarvis implementa un cliente MCP nativo en Python (`harness/mcp_client.py`) que gestiona procesos independientes comunicados a través de `stdio`. La inicialización de herramientas, filtrado de catálogos y políticas de seguridad son gobernadas estrictamente por el arnés (`harness/mcp_policy.py`).

| Servidor | Paquete / Versión | Transporte | Herramientas Expuestas | Políticas y Guardrails |
|---|---|---|---|---|
| **Fetch** | `mcp-server-fetch==2026.10.24` | stdio (`python -m mcp_server_fetch`) | `mcp_fetch__fetch` | Validación sintáctica previa (solo HTTP/HTTPS, puertos 80/443), bloqueo estricto de destinos privados/locales y protección contra redirecciones privadas en el servidor. |
| **Git** | `mcp-server-git==2026.10.19` | stdio (`python -m mcp_server_git`) | `mcp_git__git_status`, `mcp_git__git_log`, `mcp_git__git_diff_unstaged`, `mcp_git__git_diff_staged` | Repositorio circunscrito exclusivamente al espacio de trabajo activo (`cwd`), modo solo lectura (sin mutaciones ni commits), bloqueo de diffs sobre archivos sensibles (`.env`, certificados). |
| **Filesystem** | `@modelcontextprotocol/server-filesystem@2.0.1` | stdio (`node .../index.js`) | `mcp_filesystem__read_text_file`, `read_multiple_files`, `list_directory`, `search_files`, `write_file`, `edit_file` | Rutas confinadas al workspace, bloqueo de secretos y archivos protegidos (`.git`, `mcp.json`, `.venv`), confirmación humana interactiva `[s/n]` obligatoria antes de cualquier escritura. |

---

## 2. Resultados de Pruebas Unitarias y de Regresión

Se ejecutó la suite completa de pruebas unitarias de Jarvis, abarcando el adaptador multimodelo, el bucle ReAct, guardrails, comandos de la CLI, cliente MCP y la migración de SQLite a herramienta nativa:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

**Resultado:**
- **107 pruebas ejecutadas** en 0.633 segundos.
- **107 pruebas pasadas exitosamente (OK)**, 0 fallos, 0 errores.
- Se verificó la ausencia de nombres obsoletos (`mcp_fetch`, `mcp_git_info`, `mcp_sqlite_query`), el truncado estricto a 4000 caracteres con pie explicativo, la confirmación humana para escrituras en SQLite y Filesystem, y la persistencia de sesiones.

---

## 3. Pruebas de Integración con Servidores Reales

Se ejecutó la suite de pruebas de integración directa (`tests/integration_mcp.py`) contra los tres servidores reales levantados por `stdio` en la máquina local:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p "integration_mcp.py" -v
```

**Resultado:**
```text
test_01_three_servers_connected (integration_mcp.RealMCPTests.test_01_three_servers_connected) ... ok
test_02_fetch (integration_mcp.RealMCPTests.test_02_fetch) ... ok
test_03_git_status_log_and_diff (integration_mcp.RealMCPTests.test_03_git_status_log_and_diff) ... ok
test_04_filesystem_and_rejection (integration_mcp.RealMCPTests.test_04_filesystem_and_rejection) ... ok
test_05_missing_process_and_handshake_timeout (integration_mcp.RealMCPTests.test_05_missing_process_and_handshake_timeout) ... ok

----------------------------------------------------------------------
Ran 5 tests in 8.452s

OK
```

**Comportamientos verificados:**
1. Los 3 servidores se conectan e inicializan correctamente vía stdio, exponiendo un total de 11 herramientas descubiertas sin colisión de nombres.
2. `mcp_fetch__fetch` descarga contenido de `https://example.com` y registra el evento con éxito.
3. `mcp_git__*` ejecuta consultas de estado, historial y diferencias del repositorio activo.
4. `mcp_filesystem__write_file` respeta la autorización: escribe cuando es aprobada y se cancela sin tocar archivos cuando es denegada; se bloquean accesos a `.env` y rutas externas.
5. Servidores inexistentes o con retardo excesivo entran en timeout de 30s sin congelar el arnés y liberan los hilos correspondientes.

---

## 4. Demostración en Vivo con Modelo Local (Ollama)

Se ejecutó el script de verificación automatizado con Ollama (`scripts/mcp_demo.py`) utilizando el modelo local `qwen3.5:4b`. La evidencia completa quedó persistida en `.mcp-demo/resultado-ollama.json`.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.mcp_demo --model qwen3.5:4b
```

### Resumen de la Ejecución

1. **Estado Inicial:**
   - `fetch`: conectado (`mcp_fetch__fetch`)
   - `git`: conectado (`mcp_git__git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_log`)
   - `filesystem`: conectado (`read_text_file`, `read_multiple_files`, `write_file`, `edit_file`, `list_directory`, `search_files`)

2. **Turno 1 - Fetch:**
   - Solicitud: Consultar y resumir `https://example.com`.
   - Herramienta llamada: `mcp_fetch__fetch`
   - Respuesta del modelo: *"El sitio web example.com es solo un dominio de ejemplo diseñado para utilizarse en ejemplos de documentación..."*
   - Estado: `ok`

3. **Turno 2 - Git:**
   - Solicitud: Consultar los 3 últimos commits del repositorio.
   - Herramienta llamada: `mcp_git__git_log`
   - Respuesta del modelo: Resume con precisión los tres commits recientes de integración MCP (`5cbbb9b`, `54282b3`, `5549691`).
   - Estado: `ok`

4. **Turno 3 - Filesystem:**
   - Solicitud: Crear `demo-saludo.txt` con el texto exacto `Hola MCP` y posteriormente leerlo.
   - Confirmación: Se solicitó y autorizó exclusivamente la escritura sobre el archivo temporal.
   - Herramientas llamadas: `mcp_filesystem__write_file` y `mcp_filesystem__read_text_file`.
   - Comprobación en disco: El archivo fue creado con `Hola MCP` y validado.
   - Estado: `ok`

5. **Cierre de Sesión:**
   - Cierre ordenado de los tres procesos y verificación de hilos: `hilos_cerrados: true`.

---

## 5. Instrucciones de Reproducción Rápida

```powershell
# 1. Asegurar entorno virtual y dependencias
.\.venv\Scripts\Activate.ps1
npm list

# 2. Ejecutar suite de pruebas unitarias (sin red)
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v

# 3. Ejecutar pruebas con servidores MCP reales (requiere conexión)
python -X utf8 -m unittest discover -s tests -p "integration_mcp.py" -v

# 4. Demostración interactiva con Ollama
python -X utf8 -m scripts.mcp_demo --model qwen3.5:4b

# 5. Inspección desde la CLI de Jarvis
python -X utf8 main.py
# Dentro de Jarvis:
/mcp
/mcp reconnect
```
