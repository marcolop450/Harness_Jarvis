"""Políticas locales MCP. Las anotaciones remotas nunca conceden permisos."""
from __future__ import annotations

import asyncio
import ipaddress
import subprocess
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any, Callable
from harness.guardrails import SecurityViolationError, confirm_action, is_sensitive_path, validate_safe_path

ALLOWED_TOOLS = {"fetch": {"fetch"}, "git": {
    "git_status", "git_log", "git_diff_unstaged", "git_diff_staged"},
    "filesystem": {"read_text_file", "read_multiple_files", "list_directory", "search_files", "write_file", "edit_file"}}
PROTECTED_PARTS = {".git", ".venv", "node_modules", ".harness_sessions", ".mcp-logs"}


def safe_workspace_path(value: str, workspace: Path) -> Path:
    raw = Path(value)
    raw = raw if raw.is_absolute() else workspace / raw
    # Comprobar tanto el nombre original como el destino resuelto de un enlace.
    for candidate in (raw, raw.resolve()):
        try:
            parts = candidate.relative_to(workspace).parts
        except ValueError:
            raise SecurityViolationError("Ruta fuera del espacio de trabajo.")
        if any(p.lower() in PROTECTED_PARTS or p.lower() == "mcp.json" or is_sensitive_path(Path(p)) for p in parts):
            raise SecurityViolationError("Ruta confidencial o configuración protegida.")
        if any(":" in p for p in parts):
            raise SecurityViolationError("No se permiten flujos alternativos de archivos.")
    return validate_safe_path(value, workspace)


def prepare_git(name: str, args: dict[str, Any], workspace: Path) -> dict[str, Any]:
    repo = Path(args.get("repo_path", str(workspace)))
    repo = (repo if repo.is_absolute() else workspace / repo).resolve()
    if repo != workspace or not (workspace / ".git").exists():
        raise SecurityViolationError("Git solo permite el repositorio del espacio de trabajo activo.")
    args["repo_path"] = str(workspace)
    if name == "git_log":
        args["max_count"] = max(1, min(int(args.get("max_count", 5)), 20))
    if name.startswith("git_diff_"):
        command = ["git", "diff", "--name-only", "-z", "--no-ext-diff", "--no-textconv"]
        if name == "git_diff_staged":
            command.append("--cached")
        changed = subprocess.run(command, cwd=workspace, capture_output=True, timeout=5, check=True)
        for path in changed.stdout.decode("utf-8").split("\0"):
            if path:
                safe_workspace_path(path, workspace)
        args["context_lines"] = max(0, min(int(args.get("context_lines", 3)), 20))
    return args


def prepare_filesystem(name: str, args: dict[str, Any], workspace: Path, confirm_fn) -> dict[str, Any]:
    if name == "read_multiple_files":
        args["paths"] = [str(safe_workspace_path(p, workspace)) for p in args["paths"]]
    else:
        args["path"] = str(safe_workspace_path(args["path"], workspace))
    if name == "search_files":
        exclusions = [f"**/{part}/**" for part in PROTECTED_PARTS]
        exclusions += ["**/.env*", "**/*.key", "**/*.pem", "**/credentials*", "**/mcp.json", "**/.harness_*"]
        args["excludePatterns"] = list(args.get("excludePatterns", [])) + exclusions
    if name in ("write_file", "edit_file"):
        confirmer = confirm_fn or confirm_action
        if not confirmer(f"MCP Filesystem: {name}", f"Ruta: {args['path']}"):
            raise PermissionError("Acción cancelada: el usuario denegó la escritura MCP.")
        # Volver a validar tras la espera de entrada humana.
        safe_workspace_path(args["path"], workspace)
    return args


def public_url_syntax(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Fetch requiere una URL HTTP/HTTPS pública.")
    if parsed.username or parsed.password:
        raise ValueError("No se admiten credenciales en la URL.")
    if parsed.port not in (None, 80, 443):
        raise ValueError("Fetch solo permite los puertos web 80 y 443.")
    return parsed.hostname.encode("idna").decode("ascii")


async def validate_public_url(url: str) -> None:
    """Resolver antes del envío; Fetch valida otra vez cada salto HTTP."""
    host = public_url_syntax(url)
    addresses = await asyncio.get_running_loop().getaddrinfo(host, None)
    if not addresses:
        raise ValueError("No se pudo resolver el destino público.")
    for info in addresses:
        address = ipaddress.ip_address(info[4][0])
        if isinstance(address, ipaddress.IPv6Address):
            address = address.ipv4_mapped or address
            if address in ipaddress.ip_network("64:ff9b::/96"):
                address = ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        if not address.is_global or address.is_multicast:
            raise ValueError("Fetch bloqueó un destino local, privado o reservado.")


def prepare_call(server: str, name: str, arguments: dict[str, Any], workspace: Path,
                 confirm_fn: Callable[[str, str], bool] | None = None) -> dict[str, Any]:
    if name not in ALLOWED_TOOLS.get(server, set()):
        raise ValueError("Herramienta MCP no autorizada por la política local.")
    args = dict(arguments)
    if server == "fetch":
        public_url_syntax(args.get("url", ""))
        args["max_length"] = min(int(args.get("max_length", 3500)), 3500)
    elif server == "git":
        args = prepare_git(name, args, workspace)
    elif server == "filesystem":
        args = prepare_filesystem(name, args, workspace, confirm_fn)
    return args


def filter_result(server: str, name: str, text: str, arguments: dict[str, Any],
                  workspace: Path) -> str:
    if server == "filesystem" and name in ("list_directory", "search_files"):
        lines = []
        for line in text.splitlines():
            entry = line
            if name == "list_directory":
                if not line.startswith(("[FILE] ", "[DIR] ")):
                    continue
                entry = str(Path(arguments["path"]) / line.split(" ", 1)[1])
            elif not Path(entry).is_absolute():
                continue
            try:
                safe_workspace_path(entry, workspace)
            except (ValueError, PermissionError, OSError):
                continue
            lines.append(line)
        return "\n".join(lines) or "Sin resultados visibles permitidos."
    return text
