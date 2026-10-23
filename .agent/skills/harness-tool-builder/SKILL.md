---
name: harness-tool-builder
description: Instrucciones para definir y registrar las 6 herramientas del agente en harness/tools.py con JSON Schema estricto, clasificación de riesgo (AUTO vs CONFIRM), manejo resiliente de errores y truncado a 4000 caracteres.
---

# Harness Tool Builder Skill

Esta habilidad guía la creación, tipado, validación y ejecución de las herramientas en [harness/tools.py](file:///d:/Harness%20Jarvis/harness/tools.py).

## Catálogo Obligatorio de las 6 Herramientas

El sistema debe proveer exactamente estas 6 herramientas estructuradas:

1. **`read_file`**: Lectura del contenido de archivos con soporte opcional para rangos de líneas o paginación.
2. **`write_file`**: Creación o sobreescritura completa de archivos.
3. **`edit_file`**: Edición precisa de archivos mediante coincidencia exacta de texto (`target`) y sustitución (`replacement`).
4. **`list_dir`**: Exploración estructurada de directorios e inspección del árbol de archivos.
5. **`run_command`**: Ejecución de comandos del sistema operativo (PowerShell / Shell) con timeout preventivo.
6. **`search_code`**: Búsqueda textual o regex dentro de archivos del repositorio.

---

## 1. Esquema JSON Schema Estricto

Cada herramienta debe contar con:
- `name`: Identificador único en minúsculas y snake_case.
- `description`: Explicación concisa y clara de la función y parámetros para el modelo.
- `parameters`: Objeto JSON Schema con `type: "object"`, diccionario `properties` con tipos (`string`, `integer`, etc.), descripciones y lista obligatoria `required`.

Ejemplo de contrato:
```json
{
  "type": "function",
  "function": {
    "name": "edit_file",
    "description": "Edita un archivo existente reemplazando una cadena exacta por otra.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "Ruta relativa del archivo a editar." },
        "target": { "type": "string", "description": "Texto exacto que se desea reemplazar." },
        "replacement": { "type": "string", "description": "Nuevo texto de sustitución." }
      },
      "required": ["path", "target", "replacement"]
    }
  }
}
```

---

## 2. Clasificación de Riesgo (`RiskLevel`)

Cada herramienta debe estar categorizada con un nivel de riesgo:

| Nivel de Riesgo | Herramientas | Política de Ejecución |
| :--- | :--- | :--- |
| **`AUTO`** | `read_file`, `list_dir`, `search_code` | Ejecución inmediata sin interrumpir el flujo del agente, siempre que cumpla las reglas de seguridad de `guardrails.py`. |
| **`CONFIRM`** | `write_file`, `edit_file`, `run_command` | Requiere confirmación interactiva obligatoria del usuario `[s/n]` gestionada a través de `guardrails.py` antes de cualquier efecto secundario. |

---

## 3. Resiliencia y Captura de Errores

**Regla crítica**: Ninguna herramienta debe arrojar excepciones no controladas hacia `agent_loop.py`. Si ocurre un fallo:
- Capturar la excepción (e.g., `FileNotFoundError`, `PermissionError`, `TimeoutError`, parámetros faltantes).
- Devolver un string informativo claro al modelo indicando qué falló y cómo remediarlo.
- **Ejemplo**: `"Error al ejecutar edit_file: No se encontró la cadena 'target' en el archivo 'main.py'. Asegúrate de que el texto coincida exactamente."`

---

## 4. Truncado Estricto de Salidas (Límite: 4000 caracteres)

Para evitar saturar la ventana de contexto y desperdiciar tokens:
- Toda salida generada por una herramienta debe pasar por una función de truncado con un límite estricto de **4000 caracteres**.
- Si la salida excede 4000 caracteres:
  - Cortar el texto en el carácter 4000 (o en el límite de línea anterior más cercano).
  - Anexar un pie informativo explicativo:
    ```text
    \n[... Salida truncada: Se superó el límite de 4000 caracteres. Refina tu búsqueda o usa rangos de líneas ...]
    ```
