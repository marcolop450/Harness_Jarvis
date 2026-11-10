"""Mecanismos de seguridad y validación (Guardrails) para el Agente Harness.

Implementa:
- Bloqueo total de lectura y modificación de archivos .env y archivos confidenciales.
- Validación de rutas para restringir todas las operaciones dentro del cwd.
- Gobernanza de seguridad en 3 niveles de riesgo (Smart HITL):
  - Nivel 0 (Lectura / Auto): auto-aprobado.
  - Nivel 1 (Escritura en Workspace): interactivo con memoria de aprobación [a] para toda la sesión.
  - Nivel 2 (Comandos y Red): whitelist segura sin operadores shell; confirmación obligatoria para el resto.
"""

from __future__ import annotations
import fnmatch
import sys
from pathlib import Path
from typing import Callable

# Patrones de archivos confidenciales cuyo acceso está terminantemente prohibido
SENSITIVE_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.env",
    "id_rsa*",
    "*.pem",
    "*.key",
    "credentials",
    "credentials.*",
    ".git/config",
    ".harness_session.json",
    ".harness_models.json",
    "mcp.json",
)

# Niveles de riesgo Smart HITL
RISK_LEVEL_AUTO = 0       # Nivel 0: Solo lectura y comandos en whitelist segura
RISK_LEVEL_WORKSPACE = 1  # Nivel 1: Escritura y modificación en workspace
RISK_LEVEL_DANGEROUS = 2  # Nivel 2: Comandos fuera de whitelist y red externa

# Whitelist de comandos seguros (sin confirmación si no tienen encadenamiento)
SAFE_COMMAND_PREFIXES: tuple[str, ...] = (
    "pytest",
    "python -m unittest",
    "git status",
    "git diff",
    "git log",
    "git branch",
    "ruff",
    "black --check",
    "mypy",
)

# Operadores de shell estrictamente prohibidos en la whitelist
SHELL_CHAINING_CHARS: tuple[str, ...] = (
    ";",
    "&&",
    "||",
    "|",
    "`",
    "$(",
    ">",
    "<",
    "\n",
)


class SecurityViolationError(PermissionError):
    """Excepción específica para violaciones de guardrails de seguridad."""
    pass


class ActionCancelledError(Exception):
    """Excepción cuando el usuario rechaza una operación interactiva [s/n]."""
    pass


def is_sensitive_path(path: Path) -> bool:
    """Determina si una ruta corresponde a un archivo protegido o confidencial."""
    filename = path.name.lower()
    path_str = path.as_posix().lower()
    if any(part.lower() in (".git", ".harness_sessions", ".mcp-logs") for part in path.parts):
        return True

    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
        if fnmatch.fnmatch(path_str, f"*/{pattern}") or fnmatch.fnmatch(path_str, pattern):
            return True

    if filename.startswith(".env"):
        return True

    return False


def validate_safe_path(path_str: str, base_dir: Path | None = None) -> Path:
    """Valida que la ruta no escape de cwd (anti-path traversal) y no sea confidencial.

    Retorna la ruta absoluta resuelta si es segura.
    Lanza SecurityViolationError si se detecta una violación de seguridad.
    """
    base = (base_dir or Path.cwd()).resolve()

    raw_path = Path(path_str)
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    else:
        resolved = (base / raw_path).resolve()

    # Validación de contención dentro del directorio base
    try:
        resolved.relative_to(base)
    except ValueError:
        raise SecurityViolationError(
            f"Violación de seguridad (Path Traversal): La ruta '{path_str}' "
            f"está fuera del directorio de trabajo autorizado ({base})."
        )

    # Validación de archivo confidencial
    if is_sensitive_path(resolved):
        raise SecurityViolationError(
            f"Acceso bloqueado: El archivo '{resolved.name}' es confidencial "
            f"y su acceso está estrictamente prohibido por la Constitución del Harness."
        )

    return resolved


def is_safe_command(command: str) -> bool:
    """Verifica si un comando pertenece a la whitelist segura y no tiene operadores shell."""
    cmd = command.strip()
    if not cmd:
        return False
    if any(char in cmd for char in SHELL_CHAINING_CHARS):
        return False
    return any(cmd == prefix or cmd.startswith(prefix + " ") for prefix in SAFE_COMMAND_PREFIXES)


def classify_risk(tool_name: str, args: dict) -> tuple[int, str]:
    """Clasifica la herramienta y argumentos en uno de los 3 niveles de riesgo.

    Retorna: (risk_level, target_identifier)
    """
    if tool_name in (
        "read_file",
        "list_dir",
        "search_code",
        "git_status",
        "git_log",
        "git_diff_unstaged",
        "git_diff_staged",
        "mcp_git__git_status",
        "mcp_git__git_log",
        "mcp_git__git_diff_unstaged",
        "mcp_git__git_diff_staged",
    ):
        target = args.get("path", "") if "path" in args else ""
        return RISK_LEVEL_AUTO, target

    if tool_name == "sqlite_query":
        query = args.get("query", "").strip().upper()
        if query.startswith(("SELECT", "PRAGMA TABLE_INFO", "EXPLAIN")):
            return RISK_LEVEL_AUTO, args.get("db_path", "database")
        return RISK_LEVEL_WORKSPACE, args.get("db_path", "database")

    if tool_name in ("write_file", "edit_file"):
        target = args.get("path", "")
        return RISK_LEVEL_WORKSPACE, target

    if tool_name == "run_command":
        cmd = args.get("command", "")
        if is_safe_command(cmd):
            return RISK_LEVEL_AUTO, cmd
        return RISK_LEVEL_DANGEROUS, cmd

    if tool_name in ("fetch", "mcp_fetch__fetch"):
        return RISK_LEVEL_DANGEROUS, args.get("url", "")

    return RISK_LEVEL_DANGEROUS, str(args)


_turn_approved_targets: set[str] = set()
_session_approved_targets: set[str] = set()


def clear_turn_approvals() -> None:
    """Limpia la memoria de autorizaciones en lote registradas durante el turno activo."""
    _turn_approved_targets.clear()


def clear_session_approvals() -> None:
    """Limpia la memoria de autorizaciones persistentes de la sesión activa."""
    _session_approved_targets.clear()


def get_session_approved_targets() -> set[str]:
    """Retorna el conjunto de objetivos autorizados para toda la sesión."""
    return _session_approved_targets


def confirm_action(
    action_description: str,
    details: str = "",
    input_fn: Callable[[str], str] | None = None,
    target: str | None = None,
    session_approved_targets: set[str] | None = None,
    policy: str | None = None,
) -> bool:
    """Solicita confirmación interactiva [s/n/a] al usuario.

    Soporta:
    - Política 'AUTO': aprueba automáticamente sin bloquear la terminal.
    - 's' / 'si' / 'y': autoriza la operación actual.
    - 'n' / 'no': rechaza la operación.
    - 'a' / 'all': autoriza la operación actual y recuerda la aprobación para el
      mismo objetivo durante toda la sesión activa.
    """
    from harness.session_state import get_session_runtime

    effective_policy = (policy or get_session_runtime().approval_policy).strip().upper()
    if effective_policy == "AUTO":
        return True
    resolved_target = target
    if not resolved_target and details:
        if details.startswith("Ruta: "):
            resolved_target = details[6:].splitlines()[0].strip()
        elif details.startswith("Comando: "):
            resolved_target = details[9:].splitlines()[0].strip()
        else:
            resolved_target = details.splitlines()[0].strip()

    # Comandos seguros en whitelist: auto-aprobados directamente
    if action_description in ("Ejecutar comando", "Ejecutar comando de consola"):
        cmd_candidate = resolved_target or ""
        if is_safe_command(cmd_candidate):
            return True

    # Verificar si ya fue aprobado en este turno o en la sesión activa
    if resolved_target:
        if resolved_target in _turn_approved_targets:
            return True
        if session_approved_targets is not None and resolved_target in session_approved_targets:
            return True
        if resolved_target in _session_approved_targets:
            return True

    prompter = input_fn or input

    # Volcado explícito e inmediato en pantalla previo a la espera de entrada
    print("\n+--------------------------------------------------------+", flush=True)
    print(f"| [CONFIRMACION REQUERIDA]", flush=True)
    print(f"| Accion: {action_description}", flush=True)
    if details:
        print(f"| Detalles: {details}", flush=True)
    print("+--------------------------------------------------------+", flush=True)
    sys.stdout.flush()

    try:
        prompt_text = "¿Desea autorizar esta operacion? [s/n/a (autorizar todo para este objetivo)]: "
        answer = prompter(prompt_text).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n[x] Operación cancelada por el usuario.", flush=True)
        return False

    if not answer:
        print("[x] Operación cancelada: No se ingresó confirmación ('s'). No se realizaron cambios.", flush=True)
        return False

    if answer in ("a", "all", "auto", "aa"):
        if resolved_target:
            _turn_approved_targets.add(resolved_target)
            if session_approved_targets is not None:
                session_approved_targets.add(resolved_target)
            else:
                # Si no se pasó explícitamente conjunto de sesión, recordar en turno
                pass
        print(f"[✓] Operación autorizada y memorizada para '{resolved_target or 'este objetivo'}'.", flush=True)
        return True

    valid_affirmatives = (
        "s", "si", "sí", "ss", "sii", "y", "yes", "ye", "ok", "true", "1"
    )
    if answer in valid_affirmatives or answer.startswith("s") or answer.startswith("y"):
        print("[✓] Operación autorizada. Ejecutando...", flush=True)
        return True

    print("[x] Operación cancelada por el usuario. No se realizaron cambios.", flush=True)
    return False


def authorize_and_dispatch(
    tool_name: str,
    args: dict,
    session_approved_targets: set[str] | None = None,
    input_fn: Callable[[str], str] | None = None,
    base_dir: Path | None = None,
) -> bool:
    """Valida guardrails y gestiona HITL para cualquier herramienta nativa o MCP."""
    if tool_name in ("read_file", "write_file", "edit_file", "list_dir"):
        path_str = args.get("path", "")
        if path_str:
            validate_safe_path(path_str, base_dir=base_dir)

    risk_level, target = classify_risk(tool_name, args)
    if risk_level == RISK_LEVEL_AUTO:
        return True

    action_desc = f"Ejecutar herramienta '{tool_name}'"
    if tool_name in ("write_file", "edit_file"):
        action_desc = "Modificar archivo" if tool_name == "edit_file" else "Crear archivo"
        details = f"Ruta: {target}"
    elif tool_name == "run_command":
        action_desc = "Ejecutar comando"
        details = f"Comando: {target}"
    else:
        details = f"Objetivo: {target}"

    authorized = confirm_action(
        action_desc,
        details=details,
        input_fn=input_fn,
        target=target,
        session_approved_targets=session_approved_targets,
    )
    if not authorized:
        raise ActionCancelledError(f"Operacion cancelada por el usuario para '{tool_name}'.")
    return True
