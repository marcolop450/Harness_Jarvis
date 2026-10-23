"""Mecanismos de seguridad y validación (Guardrails) para el Agente Harness.

Implementa:
- Bloqueo total de lectura y modificación de archivos .env y archivos confidenciales.
- Validación de rutas para restringir todas las operaciones dentro del cwd.
- Confirmación interactiva obligatoria [s/n] antes de editar/crear archivos o correr comandos.
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


_turn_approved_targets: set[str] = set()


def clear_turn_approvals() -> None:
    """Limpia la memoria de autorizaciones en lote registradas durante el turno activo."""
    _turn_approved_targets.clear()


def confirm_action(
    action_description: str,
    details: str = "",
    input_fn: Callable[[str], str] | None = None,
    target: str | None = None,
) -> bool:
    """Solicita confirmación interactiva [s/n/a] al usuario.

    Soporta:
    - 's' / 'si' / 'y': autoriza la operación actual.
    - 'n' / 'no': rechaza la operación.
    - 'a' / 'all': autoriza la operación actual y recuerda la aprobación para el
      mismo objetivo durante el resto del turno activo.
    """
    resolved_target = target
    if not resolved_target and details:
        if details.startswith("Ruta: "):
            resolved_target = details[6:].strip()
        elif details.startswith("Comando: "):
            resolved_target = details[9:].strip()
        else:
            resolved_target = details.strip()

    if resolved_target and resolved_target in _turn_approved_targets:
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
        return False

    if not answer:
        return False

    if answer in ("a", "all", "auto", "aa"):
        if resolved_target:
            _turn_approved_targets.add(resolved_target)
        return True

    valid_affirmatives = (
        "s", "si", "sí", "ss", "sii", "y", "yes", "ye", "ok", "true", "1"
    )
    return answer in valid_affirmatives or answer.startswith("s") or answer.startswith("y")
