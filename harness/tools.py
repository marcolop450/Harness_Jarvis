"""Definición y ejecución de las 6 herramientas operativas del Agente Harness.

Catálogo estricto:
1. read_file (AUTO)
2. write_file (CONFIRM)
3. edit_file (CONFIRM)
4. list_dir (AUTO)
5. run_command (CONFIRM)
6. search_code (AUTO)

Todas las salidas están estrictamente truncadas a un máximo de 4000 caracteres.
"""

from __future__ import annotations
import enum
import os
import re
import sqlite3
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from harness.guardrails import SecurityViolationError, confirm_action, validate_safe_path

MAX_TOOL_OUTPUT_CHARS: int = 4000


class RiskLevel(str, enum.Enum):
    """Clasificación de riesgo de las herramientas."""
    AUTO = "AUTO"       # Lectura: ejecución inmediata si pasa guardrails
    CONFIRM = "CONFIRM" # Escritura o ejecución: requiere confirmación [s/n]


TOOL_RISK_MAP: dict[str, RiskLevel] = {
    "read_file": RiskLevel.AUTO,
    "list_dir": RiskLevel.AUTO,
    "search_code": RiskLevel.AUTO,
    "write_file": RiskLevel.CONFIRM,
    "edit_file": RiskLevel.CONFIRM,
    "run_command": RiskLevel.CONFIRM,
    "mcp_fetch": RiskLevel.AUTO,
    "mcp_git_info": RiskLevel.AUTO,
    "mcp_sqlite_query": RiskLevel.AUTO,
}


def truncate_output(text: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    """Trunca el texto si supera max_chars y anexa un pie informativo explicativo."""
    if len(text) <= max_chars:
        return text
    notice = f"\n\n[... Salida truncada: Se superó el límite de {max_chars} caracteres. Acota tu consulta ...]"
    return text[:max_chars] + notice


def tool_read_file(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    base_dir: Path | None = None,
) -> str:
    """Lee el contenido de un archivo en texto plano con soporte de rango de líneas."""
    safe_path = validate_safe_path(path, base_dir)
    if not safe_path.exists():
        return f"Error: El archivo '{path}' no existe."
    if not safe_path.is_file():
        return f"Error: '{path}' no es un archivo regular."

    try:
        content = safe_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"Error al leer '{path}': {exc}"

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)

    if start_line is not None or end_line is not None:
        s = max(1, start_line or 1)
        e = min(total_lines, end_line or total_lines)
        if s > e:
            return f"Error: start_line ({s}) no puede ser mayor que end_line ({e})."
        selected = lines[s - 1 : e]
        numbered = [f"{s + idx}: {line}" for idx, line in enumerate(selected)]
        output = "".join(numbered)
    else:
        output = "".join(lines)

    return truncate_output(output)


def tool_write_file(
    path: str,
    content: str,
    base_dir: Path | None = None,
    confirm_fn: Callable[[str, str], bool] | None = None,
) -> str:
    """Crea o sobrescribe un archivo dentro del espacio de trabajo tras confirmación."""
    safe_path = validate_safe_path(path, base_dir)

    confirmer = confirm_fn or (lambda desc, det: confirm_action(desc, det))
    if not confirmer("Crear o sobrescribir archivo", f"Ruta: {path}"):
        return f"Acción cancelada: El usuario denegó la escritura en '{path}'."

    try:
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"Archivo '{path}' escrito exitosamente ({len(content)} caracteres)."
    except Exception as exc:
        return f"Error al escribir en '{path}': {exc}"


def tool_edit_file(
    path: str,
    target: str,
    replacement: str,
    base_dir: Path | None = None,
    confirm_fn: Callable[[str, str], bool] | None = None,
) -> str:
    """Edita un archivo existente reemplazando una cadena exacta por otra."""
    safe_path = validate_safe_path(path, base_dir)
    if not safe_path.exists():
        return f"Error: El archivo '{path}' no existe."
    if not safe_path.is_file():
        return f"Error: '{path}' no es un archivo regular."

    try:
        content = safe_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"Error al leer '{path}': {exc}"

    if target not in content:
        return (
            f"Error al editar '{path}': No se encontró la cadena 'target'. "
            f"Verifica que el texto y los espacios coincidan exactamente."
        )

    confirmer = confirm_fn or (lambda desc, det: confirm_action(desc, det))
    if not confirmer("Editar archivo", f"Ruta: {path}\nReemplazo de '{target[:50]}...'"):
        return f"Acción cancelada: El usuario denegó la edición en '{path}'."

    new_content = content.replace(target, replacement)
    try:
        safe_path.write_text(new_content, encoding="utf-8")
        return f"Archivo '{path}' editado exitosamente."
    except Exception as exc:
        return f"Error al guardar cambios en '{path}': {exc}"


def tool_list_dir(
    path: str = ".",
    max_depth: int = 2,
    base_dir: Path | None = None,
) -> str:
    """Lista de forma estructurada el contenido de un directorio hasta max_depth."""
    safe_path = validate_safe_path(path, base_dir)
    if not safe_path.exists():
        return f"Error: El directorio '{path}' no existe."
    if not safe_path.is_dir():
        return f"Error: '{path}' no es un directorio."

    ignore_dirs = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
    results: list[str] = [f"Directorio: {path}"]

    def walk(current_dir: Path, current_depth: int, prefix: str = ""):
        if current_depth > max_depth:
            return
        try:
            entries = sorted(list(current_dir.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            results.append(f"{prefix}[Acceso denegado]")
            return

        for idx, entry in enumerate(entries):
            if entry.name in ignore_dirs:
                continue
            is_last = idx == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if entry.is_dir():
                results.append(f"{prefix}{connector}{entry.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                walk(entry, current_depth + 1, new_prefix)
            else:
                results.append(f"{prefix}{connector}{entry.name}")

    walk(safe_path, 1)
    return truncate_output("\n".join(results))


def tool_run_command(
    command: str,
    timeout: int = 30,
    cwd: Path | None = None,
    confirm_fn: Callable[[str, str], bool] | None = None,
) -> str:
    """Ejecuta un comando en la consola del sistema operativo tras confirmación interactiva."""
    confirmer = confirm_fn or (lambda desc, det: confirm_action(desc, det))
    if not confirmer("Ejecutar comando de consola", f"Comando: {command}"):
        return f"Acción cancelada: El usuario denegó la ejecución del comando '{command}'."

    working_dir = (cwd or Path.cwd()).resolve()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
            encoding="utf-8",
            errors="replace",
        )
        output_parts: list[str] = []
        if proc.stdout:
            output_parts.append(proc.stdout)
        if proc.stderr:
            output_parts.append(f"[STDERR]:\n{proc.stderr}")
        if proc.returncode != 0:
            output_parts.append(f"[Código de salida: {proc.returncode}]")

        result = "\n".join(output_parts).strip()
        if not result:
            result = "[Comando ejecutado sin salida]"
        return truncate_output(result)
    except subprocess.TimeoutExpired:
        return f"Error: El comando superó el límite de tiempo de {timeout} segundos."
    except Exception as exc:
        return f"Error al ejecutar comando: {exc}"


def tool_search_code(
    pattern: str,
    path: str = ".",
    base_dir: Path | None = None,
) -> str:
    """Busca un patrón o texto dentro de los archivos del proyecto."""
    safe_path = validate_safe_path(path, base_dir)
    if not safe_path.exists():
        return f"Error: La ruta '{path}' no existe."

    ignore_dirs = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
    matches: list[str] = []

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        return f"Error en patrón regex '{pattern}': {exc}"

    files_to_search: list[Path] = []
    if safe_path.is_file():
        files_to_search.append(safe_path)
    else:
        for root, dirs, files in os.walk(safe_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                files_to_search.append(Path(root) / f)

    for file_path in files_to_search:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            if regex.search(line):
                rel_path = file_path.relative_to(safe_path if safe_path.is_dir() else safe_path.parent)
                matches.append(f"{rel_path}:{line_num}: {line.strip()}")
                if len(matches) >= 100:
                    matches.append("... Se alcanzó el límite de 100 coincidencias.")
                    break
        if len(matches) >= 100:
            break

    if not matches:
        return f"No se encontraron coincidencias para '{pattern}' en '{path}'."

    return truncate_output("\n".join(matches))


def tool_mcp_fetch(url: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    """Consulta segura de endpoints HTTP o recursos web bajo el protocolo MCP."""
    if not url.startswith(("http://", "https://")):
        return "Error: Solo se admiten URLs que inicien con http:// o https://."
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Harness-Jarvis-MCP/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            raw_bytes = response.read(max_chars * 2)
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw_bytes.decode(charset, errors="replace")
            res_str = f"[MCP Fetch Status {status} | Tipo: {content_type}]\n\n{body}"
            return truncate_output(res_str, max_chars)
    except urllib.error.HTTPError as http_err:
        return f"[MCP Fetch Error {http_err.code}]: {http_err.reason}"
    except Exception as exc:
        return f"[MCP Fetch Error]: {exc}"


def tool_mcp_git_info(
    subcommand: str = "status",
    max_commits: int = 5,
    base_dir: Path | None = None,
) -> str:
    """Inspector MCP para consultar el estado del repositorio Git del proyecto."""
    cwd = (base_dir or Path.cwd()).resolve()
    valid_subcommands = {
        "status": ["git", "status", "-s"],
        "log": ["git", "log", f"-n{max(1, min(max_commits, 20))}", "--oneline"],
        "diff": ["git", "diff", "--stat"],
        "branch": ["git", "branch", "--show-current"],
    }
    cmd_key = subcommand.strip().lower()
    if cmd_key not in valid_subcommands:
        return (
            f"Error: Subcomando '{subcommand}' no soportado. "
            f"Opciones disponibles: {', '.join(valid_subcommands.keys())}."
        )

    try:
        res = subprocess.run(
            valid_subcommands[cmd_key],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode != 0:
            err_msg = res.stderr.strip() or f"Código de salida: {res.returncode}"
            return f"[MCP Git Error]: {err_msg}"
        out = res.stdout.strip()
        if not out:
            return f"[MCP Git {cmd_key}]: Sin cambios / salida limpia."
        return truncate_output(f"[MCP Git {cmd_key}]:\n{out}")
    except Exception as exc:
        return f"[MCP Git Error]: {exc}"


def tool_mcp_sqlite_query(
    query: str,
    db_path: str = ":memory:",
    base_dir: Path | None = None,
) -> str:
    """Ejecutor MCP de consultas SQL sobre bases de datos SQLite locales o en memoria."""
    clean_query = query.strip()
    if not clean_query:
        return "Error: La consulta SQL no puede estar vacía."

    if db_path != ":memory:":
        safe_path = validate_safe_path(db_path, base_dir)
        db_target = str(safe_path)
    else:
        db_target = ":memory:"

    try:
        conn = sqlite3.connect(db_target)
        try:
            cursor = conn.cursor()
            if clean_query.lower().startswith("select") or clean_query.lower().startswith("pragma"):
                cursor.execute(clean_query)
                rows = cursor.fetchall()
                col_names = [d[0] for d in cursor.description] if cursor.description else []
                header = " | ".join(col_names)
                lines = [header, "-" * max(len(header), 10)]
                for row in rows[:50]:
                    lines.append(" | ".join(str(v) for v in row))
                if len(rows) > 50:
                    lines.append(f"... {len(rows) - 50} filas adicionales omitidas.")
                output = "\n".join(lines) if rows else "Consulta ejecutada: 0 filas encontradas."
            else:
                cursor.executescript(clean_query)
                conn.commit()
                output = "Sentencia ejecutada con éxito."
        finally:
            conn.close()
        return truncate_output(output)
    except SecurityViolationError as sec_err:
        return f"Violación de seguridad: {sec_err}"
    except Exception as exc:
        return f"[MCP SQLite Error]: {exc}"


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    base_dir: Path | None = None,
    confirm_fn: Callable[[str, str], bool] | None = None,
) -> str:
    """Despacha de forma unificada la ejecución de cualquier herramienta con captura de excepciones."""
    if name not in TOOL_RISK_MAP:
        return (
            f"Error: La herramienta '{name}' no existe en el catálogo. "
            f"Herramientas disponibles: {', '.join(TOOL_RISK_MAP.keys())}."
        )

    try:
        args = dict(arguments or {})
        if name == "read_file":
            return tool_read_file(
                path=args.get("path", ""),
                start_line=args.get("start_line"),
                end_line=args.get("end_line"),
                base_dir=base_dir,
            )
        elif name == "write_file":
            return tool_write_file(
                path=args.get("path", ""),
                content=args.get("content", ""),
                base_dir=base_dir,
                confirm_fn=confirm_fn,
            )
        elif name == "edit_file":
            return tool_edit_file(
                path=args.get("path", ""),
                target=args.get("target", ""),
                replacement=args.get("replacement", ""),
                base_dir=base_dir,
                confirm_fn=confirm_fn,
            )
        elif name == "list_dir":
            return tool_list_dir(
                path=args.get("path", "."),
                max_depth=int(args.get("max_depth", 2)),
                base_dir=base_dir,
            )
        elif name == "run_command":
            return tool_run_command(
                command=args.get("command", ""),
                cwd=base_dir,
                confirm_fn=confirm_fn,
            )
        elif name == "search_code":
            return tool_search_code(
                pattern=args.get("pattern", ""),
                path=args.get("path", "."),
                base_dir=base_dir,
            )
        elif name == "mcp_fetch":
            return tool_mcp_fetch(
                url=args.get("url", ""),
            )
        elif name == "mcp_git_info":
            return tool_mcp_git_info(
                subcommand=args.get("subcommand", "status"),
                max_commits=int(args.get("max_commits", 5)),
                base_dir=base_dir,
            )
        elif name == "mcp_sqlite_query":
            return tool_mcp_sqlite_query(
                query=args.get("query", ""),
                db_path=args.get("db_path", ":memory:"),
                base_dir=base_dir,
            )
        else:
            return f"Error: Herramienta '{name}' no implementada."
    except SecurityViolationError as sec_err:
        return f"Violación de seguridad: {sec_err}"
    except Exception as exc:
        return f"Error inesperado al ejecutar '{name}': {exc}"


TOOLS_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee el contenido de un archivo en texto plano con soporte opcional de rango de líneas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa del archivo a leer dentro del espacio de trabajo.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Número de línea inicial a leer (base 1, inclusivo).",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Número de línea final a leer (base 1, inclusivo).",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Crea o sobrescribe un archivo con el contenido especificado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa del archivo a crear o sobreescribir.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Contenido completo a escribir en el archivo.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edita un archivo existente reemplazando una cadena exacta ('target') por otra ('replacement').",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa del archivo a modificar.",
                    },
                    "target": {
                        "type": "string",
                        "description": "Texto exacto que se desea buscar y reemplazar.",
                    },
                    "replacement": {
                        "type": "string",
                        "description": "Nuevo texto de sustitución.",
                    },
                },
                "required": ["path", "target", "replacement"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Lista el contenido y estructura de un directorio dentro del espacio de trabajo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa del directorio a inspeccionar (por defecto '.').",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Profundidad máxima de recursión (por defecto 2).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Ejecuta un comando en la consola del sistema operativo y retorna su salida.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Comando de shell a ejecutar.",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Busca una subcadena o patrón dentro de los archivos del proyecto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Patrón de texto o subcadena a buscar.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directorio relativo donde buscar (por defecto '.').",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_fetch",
            "description": "Cliente MCP para consultar recursos web o APIs externas mediante peticiones HTTP seguras.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL completa (http:// o https://) a consultar.",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_git_info",
            "description": "Herramienta MCP para inspeccionar el estado, ramas, historial de commits o diffs del repositorio Git.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subcommand": {
                        "type": "string",
                        "description": "Subcomando a ejecutar: 'status', 'log', 'diff' o 'branch'.",
                        "enum": ["status", "log", "diff", "branch"],
                    },
                    "max_commits": {
                        "type": "integer",
                        "description": "Número máximo de commits a mostrar al consultar 'log' (por defecto 5).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_sqlite_query",
            "description": "Herramienta MCP para ejecutar consultas SQL sobre bases de datos locales SQLite o base en memoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Sentencia SQL a ejecutar.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Ruta al archivo .db / .sqlite o ':memory:' (por defecto ':memory:').",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def get_tools_definitions() -> list[dict[str, Any]]:
    """Retorna las 6 especificaciones de herramientas compatibles con OpenAI."""
    return list(TOOLS_DEFINITIONS)
