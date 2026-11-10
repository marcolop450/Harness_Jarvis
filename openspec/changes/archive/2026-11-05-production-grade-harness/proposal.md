# Proposal: Evolución del Arnés Jarvis a Grado de Producción

## Why
El arnés actual requiere dar el salto definitivo hacia un entorno de ejecución de grado de producción (estilo Claude Code): eliminando dependencias externas frágiles (Node.js/npm para filesystem), unificando el despacho de herramientas bajo una gobernanza estricta de seguridad en 3 niveles de riesgo, incorporando resiliencia ante saturación de cuota (Exponential Backoff en HTTP 429), auto-reparando JSONs defectuosos de modelos pequeños, y optimizando el uso de la ventana de contexto mediante truncado Head+Tail (1000+3000), Observation Masking e inyección proactiva de entorno.

## What Changes
- **Limpieza de Runtime MCP:** Eliminación del servidor Node.js `@modelcontextprotocol/server-filesystem` y de `package.json`/`package-lock.json`. Operaciones de disco gobernadas 100% por `tools.py` nativo en Python. Arranque tolerante a fallos (*graceful degradation*) para los servidores MCP stdio (`fetch` y `git`).
- **Gobernanza de Seguridad en 3 Niveles (Smart HITL):** Nivel 0 (Lectura/Auto), Nivel 1 (Escritura en Workspace con memoria de aprobación `[a]` para toda la sesión activa), y Nivel 2 (Comandos con whitelist segura libre de command injection y confirmación estricta para el resto).
- **Resiliencia e Inferencia Multi-API:** Aumento de `max_tokens` a 4096, Exponential Backoff automático ante errores HTTP 429 con indicador de espera, y sanitizador/reparador de JSON para `tool_calls` que devuelve errores estructurados sin abortar.
- **Herramientas con Truncado Head+Tail:** Reemplazo del truncado ciego por `smart_truncate` (1000 caracteres de cabecera y 3000 de cola con aviso explícito), numeración de líneas en `read_file` y validación diagnóstica en `edit_file`.
- **Inteligencia del Kernel y Contexto:** Inyección proactiva de contexto en System Prompt (SO, cwd, árbol raíz, estado Git, JARVIS.md/AGENT.md), bucle de auto-reparación (Self-Healing) y Observation Masking sobre copia efímera del historial para ahorrar RAM cognitiva.

## Capabilities

### Modified Capabilities
- `mcp-integration`: Eliminación del servidor Node filesystem y soporte de arranque tolerante a fallos.
- `security-guardrails`: Clasificación en 3 niveles de riesgo, memoria de sesión `[a]`, whitelist segura y bloqueo de command injection.
- `multi-api-provider`: Soporte de max_tokens=4096, Exponential Backoff ante Error 429 y auto-reparación de JSON.
- `harness-tools`: Truncado inteligente Head+Tail, soporte de numeración/rangos en lectura y diagnóstico en edición.
- `agent-loop`: Inyección proactiva de contexto, Observation Masking en copia efímera y bucle de auto-reparación.

## Impact
- Módulos afectados: `harness/guardrails.py`, `harness/mcp_client.py`, `harness/llm_provider.py`, `harness/tools.py`, `harness/agent_loop.py`, `main.py`, `mcp.json`.
- Eliminación de archivos Node.js (`package.json`, `package-lock.json`, `node_modules`).
- Sin impacto negativo en compatibilidad ni adición de dependencias de frameworks pesados.
