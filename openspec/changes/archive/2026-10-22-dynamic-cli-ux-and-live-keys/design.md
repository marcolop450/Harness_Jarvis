# Design: Experiencia de Terminal Limpia, Gestión de Modelos y Memoria de Chat por Carpeta

## Context
Véase `proposal.md`. Actualmente, la terminal CLI contiene modelos de prueba sugeridos en código que generan confusión si el usuario no los tiene o no los desea. Asimismo, la sesión en memoria se pierde al salir y no existe un comando `/clear` para refrescar la consola ni un comando `/reset` para reiniciar la conversación del espacio de trabajo.

## Goals / Non-Goals

**Goals:**
- Eliminar modelos ficticios o de prueba de la configuración base (`DEFAULT_MODEL_REGISTRY`). El catálogo arranca limpio y se administra exclusivamente mediante `/model add <prov> <modelo>` y `/model rm <id_o_nombre>`.
- Inyectar claves de API inmediatamente en `os.environ` al ejecutar `/key` para disponibilidad en caliente sin reiniciar.
- Mantener persistencia del historial de conversación por carpeta de trabajo en `.harness_session.json` para dar continuidad al trabajo, con comando `/reset` para vaciarlo.
- Implementar `/clear` para limpiar la pantalla de la terminal de forma nativa (`os.system('cls' if os.name == 'nt' else 'clear')`) y volver a renderizar el encabezado limpio.
- Prompt contextual dinámico: `[<carpeta> | ⚡ <proveedor>:<modelo>] jarvis> `.

**Non-Goals:**
- No implementar persistencia de múltiples hilos/conversaciones paralelas ni bases de datos complejas.
- No depender de librerías TUI pesadas (como textual o curses); mantener compatibilidad nativa con Windows PowerShell y cmd.

## Decisions

### 1. Gestión de modelos limpia y gobernada por el usuario
- **Decisión**: Eliminar la lista estática `DEFAULT_MODEL_REGISTRY` con modelos predeterminados de prueba. Si no hay modelos registrados en `.harness_models.json`, el catálogo reporta vacío y la terminal orienta al usuario para agregar su primer modelo (`/model add <prov> <modelo>`).
- **Alternativas**: Mantener gemini/groq como sugerencias fijas. *Descarte*: El usuario solicitó explícitamente no tener modelos de prueba quemados.

### 2. Memoria de conversación persistente por carpeta (`.harness_session.json`)
- **Decisión**: Implementar funciones `load_session_history(workspace_dir)` y `save_session_history(workspace_dir, messages)` en `harness/model_config.py` o módulo de soporte, guardando el array de mensajes en `.harness_session.json`. Al iniciar el agente en una carpeta, se carga el historial previo si existe. El comando `/reset` vacía este archivo y el historial en memoria.
- **Seguridad**: `.harness_session.json` se restringe dentro del workspace y se agrega a los patrones protegidos para evitar que las herramientas del agente lo sobreescriban accidentalmente.

### 3. Limpieza de pantalla y visualización OpenCode
- **Decisión**: El comando `/clear` ejecuta la limpieza estándar del sistema operativo y vuelve a imprimir el banner estilizado. El prompt dinámico se computa en cada iteración del bucle en `main.py`.

### 4. Inyección en caliente de variables de entorno
- **Decisión**: Al invocar `save_api_key_to_env(provider, key)`, se ejecuta `os.environ[var_name] = key.strip()` además de persistirlo en `.env`.

## Risks / Trade-offs

- **[Tamaño excesivo del historial guardado en `.harness_session.json`]** → Conversaciones muy largas podrían consumir excesivo contexto de tokens.
  *Mitigación*: Truncar o mantener los últimos N intercambios relevantes en memoria si excede un límite prudente, o permitir al usuario ejecutar `/reset`.
- **[Concurrencia en archivos locales]** → Dos terminales abiertas en la misma carpeta podrían sobrescribir `.harness_session.json`.
  *Mitigación*: Operaciones de lectura al inicio y escritura atómica tras cada turno.
