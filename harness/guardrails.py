"""Mecanismos de seguridad y validación (Guardrails) para el Agente Harness.

Implementa:
- Bloqueo total de lectura y modificación de archivos .env y archivos confidenciales.
- Validación de rutas para restringir todas las operaciones dentro del cwd.
- Confirmación interactiva obligatoria [s/n] antes de editar/crear archivos o correr comandos.
"""

from __future__ import annotations
import fnmatch
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

    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
        if fnmatch.fnmatch(path_str, f"*/{pattern}") or fnmatch.fnmatch(path_str, pattern):
            return True

    # Bloqueo explícito de cualquier archivo que empiece por .env
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


def confirm_action(
    action_description: str,
    details: str = "",
    input_fn: Callable[[str], str] | None = None,
) -> bool:
    """Solicita confirmación interactiva obligatoria [s/n] al usuario.

    Retorna True si el usuario acepta ('s', 'si', 'y', 'yes').
    Retorna False si el usuario rechaza.
    """
    prompter = input_fn or input

    prompt_msg = f"\n⚠️  [CONFIRMACIÓN REQUERIDA] ⚠️\nAcción: {action_description}\n"
    if details:
        prompt_msg += f"Detalles: {details}\n"
    prompt_msg += "¿Desea autorizar esta operación? [s/n]: "

    try:
        answer = prompter(prompt_msg).strip().lower()
    except (KeyboardInterrupt, EOFError):
        return False

    return answer in ("s", "si", "y", "yes")
