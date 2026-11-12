"""Controlador de comandos y lógica interactiva de la CLI para Harness Jarvis."""

from __future__ import annotations

import datetime
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, Set, Tuple

from harness.session_state import SessionRuntime, get_session_runtime

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory


# Catálogo descriptivo de comandos de barra oblicua para autocompletado interactivo
SLASH_COMMANDS_REGISTRY: dict[str, str] = {
    "/model": "Listar, cambiar o agregar modelos en el catálogo",
    "/plan": "Alternar modo Arquitecto (solo lectura) / Actuador",
    "/steps": "Ajustar límite de pasos de razonamiento por consulta",
    "/approval": "Conmutar política de confirmación (confirm / auto)",
    "/doctor": "Diagnóstico de salud de endpoint LLM y procesos MCP",
    "/tokens": "Estimar consumo de tokens y ventana de contexto",
    "/diff": "Visualizar diferencias de archivos tocados en la sesión",
    "/tree": "Imprimir árbol visual filtrado del espacio de trabajo",
    "/export": "Exportar conversación activa a archivo Markdown",
    "/compact": "Compactar memoria con resumen estructurado",
    "/mcp": "Inspeccionar estado o reconectar servidores MCP",
    "/key": "Configurar clave de API para un proveedor",
    "/endpoint": "Configurar endpoint personalizado para un proveedor",
    "/clear": "Limpiar pantalla manteniendo la sesión",
    "/reset": "Reiniciar historial de conversación en este espacio",
    "/sessions": "Listar sesiones guardadas anteriormente",
    "/resume": "Reanudar una sesión previa mediante su ID",
    "/guide": "Mostrar guía interactiva de usuario",
    "exit": "Terminar y salir de la sesión interactiva",
    "quit": "Terminar y salir de la sesión interactiva",
}

SLASH_SUBCOMMANDS_REGISTRY: dict[str, dict[str, str]] = {
    "/model": {
        "add": "Agregar nuevo modelo: /model add <prov> <modelo> [url]",
        "list": "Listar catálogo numerado de modelos registrados",
        "rm": "Eliminar modelo: /model rm <numero_o_nombre>",
    },
    "/approval": {
        "auto": "Aprobación automática de acciones seguras sin confirmación",
        "confirm": "Confirmación interactiva obligatoria [s/n/a]",
    },
    "/mcp": {
        "reconnect": "Reiniciar y reconectar todos los servidores MCP",
    },
    "/endpoint": {
        "openai": "Configurar URL base para OpenAI / Meta",
        "ollama": "Configurar URL base para Ollama local",
        "groq": "Configurar URL base para Groq",
        "gemini": "Configurar URL base para Gemini",
        "openrouter": "Configurar URL base para OpenRouter",
    },
    "/key": {
        "openai": "Configurar clave de API para OpenAI / Meta",
        "gemini": "Configurar clave de API para Gemini",
        "groq": "Configurar clave de API para Groq",
        "openrouter": "Configurar clave de API para OpenRouter",
    },
}


class JarvisCommandCompleter(Completer):
    """Autocompletador para comandos de barra oblicua, subcomandos y archivos locales."""

    def __init__(
        self,
        commands: Optional[dict[str, str]] = None,
        subcommands: Optional[dict[str, dict[str, str]]] = None,
        base_dir: Optional[Path] = None,
    ):
        self.commands = commands or SLASH_COMMANDS_REGISTRY
        self.subcommands = subcommands or SLASH_SUBCOMMANDS_REGISTRY
        self.base_dir = base_dir

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        # 1. Comandos primarios (/plan, /model, /doctor...)
        if " " not in stripped:
            if stripped.startswith("/"):
                for cmd, desc in self.commands.items():
                    if cmd.lower().startswith(stripped.lower()):
                        yield Completion(
                            cmd,
                            start_position=-len(stripped),
                            display=cmd,
                            display_meta=desc,
                        )
            return

        # 2. Subcomandos jerárquicos (/model add, /approval auto...)
        parts = stripped.split()
        if stripped.startswith("/") and len(parts) >= 1:
            cmd = parts[0].lower()
            if cmd in self.subcommands:
                sub_dict = self.subcommands[cmd]
                sub_prefix = parts[1].lower() if len(parts) > 1 and not text.endswith(" ") else ""
                if len(parts) == 1 and text.endswith(" "):
                    for sub, desc in sub_dict.items():
                        yield Completion(sub, start_position=0, display=sub, display_meta=desc)
                    return
                elif len(parts) == 2 and not text.endswith(" "):
                    for sub, desc in sub_dict.items():
                        if sub.lower().startswith(sub_prefix):
                            yield Completion(
                                sub,
                                start_position=-len(sub_prefix),
                                display=sub,
                                display_meta=desc,
                            )
                    return

        # 3. Autocompletado de archivos o carpetas si la última palabra tiene formato de ruta/extensión
        last_word = text.split()[-1] if text.split() else ""
        if last_word and ("." in last_word or "/" in last_word or "\\" in last_word or len(last_word) >= 4):
            cwd = self.base_dir or Path.cwd()
            ignore_names = {".git", "__pycache__", ".venv", ".pytest_cache", ".harness_sessions"}
            try:
                for entry in cwd.iterdir():
                    if entry.name in ignore_names:
                        continue
                    if entry.name.lower().startswith(last_word.lower()):
                        meta = "Carpeta local" if entry.is_dir() else "Archivo local"
                        disp = f"{entry.name}/" if entry.is_dir() else entry.name
                        yield Completion(
                            entry.name,
                            start_position=-len(last_word),
                            display=disp,
                            display_meta=meta,
                        )
            except Exception:
                pass


def create_prompt_session(output: Any = None) -> PromptSession:
    """Crea una sesión interactiva de prompt_toolkit con autocompletador e historial.

    Maneja transparentemente entornos sin búfer de consola de Windows mediante DummyOutput.
    """
    if output is not None:
        return PromptSession(
            completer=JarvisCommandCompleter(),
            history=InMemoryHistory(),
            output=output,
        )
    try:
        return PromptSession(
            completer=JarvisCommandCompleter(),
            history=InMemoryHistory(),
        )
    except Exception:
        from prompt_toolkit.output import DummyOutput
        return PromptSession(
            completer=JarvisCommandCompleter(),
            history=InMemoryHistory(),
            output=DummyOutput(),
        )



def handle_control_command(
    command_line: str,
    runtime: Optional[SessionRuntime] = None,
) -> Tuple[bool, str]:
    """Procesa comandos de control de ciclo agéntico y gobernanza (/plan, /steps, /approval).

    Retorna: (handled, mensaje_resultado).
    """
    rt = runtime or get_session_runtime()
    parts = command_line.strip().split()
    if not parts:
        return False, ""

    cmd = parts[0].lower()

    if cmd == "/plan":
        new_mode = rt.toggle_plan_mode()
        desc = (
            "Arquitecto (Solo Lectura y Diseño - Bloquea modificaciones en disco)"
            if new_mode == "PLAN"
            else "Actuador (Modo estándar con permisos de lectura y escritura)"
        )
        msg = f"\n[+] Modo de razonamiento conmutado a: {new_mode}\n    {desc}"
        return True, msg

    if cmd == "/steps":
        if len(parts) == 1:
            return True, f"\n[Pasos]: Límite actual de pasos por consulta: {rt.max_steps}"
        try:
            val = int(parts[1])
            if rt.set_max_steps(val):
                return True, f"\n[+] Límite de pasos actualizado a: {rt.max_steps} pasos por consulta."
            return True, f"\n[Error]: El valor de pasos debe ser un número entero entre 1 y 50."
        except ValueError:
            return True, f"\n[Error]: '{parts[1]}' no es un número válido. Uso: /steps <1-50>"

    if cmd == "/approval":
        if len(parts) == 1:
            new_pol = rt.toggle_approval_policy()
            desc = (
                "Automática (Ejecuta acciones seguras sin preguntar)"
                if new_pol == "AUTO"
                else "Confirmación interactiva (Pregunta obligatoriamente [s/n] antes de modificar archivos o ejecutar comandos)"
            )
            return True, f"\n[+] Política de aprobación conmutada a: {new_pol}\n    {desc}"
        target_pol = parts[1].strip().upper()
        if rt.set_approval_policy(target_pol):
            return True, f"\n[+] Política de aprobación establecida en: {rt.approval_policy}"
        return True, f"\n[Error]: Política no válida: '{parts[1]}'. Opciones permitidas: confirm, auto"

    return False, ""


def handle_observability_command(
    command_line: str,
    history: Optional[list[dict[str, Any]]] = None,
    cwd: Optional[Path] = None,
) -> Tuple[bool, str]:
    """Procesa comandos de observabilidad y exportación (/tokens, /export)."""
    base_dir = cwd or Path.cwd()
    parts = command_line.strip().split()
    if not parts:
        return False, ""

    cmd = parts[0].lower()

    if cmd == "/tokens":
        active_history = history or []
        char_count = sum(len(str(m.get("content") or "")) for m in active_history)
        est_tokens = max(0, char_count // 4)
        msg_count = len(active_history)

        output = (
            "\n+--------------------------------------------------------+\n"
            "| [OBSERVABILIDAD DE TOKENS Y CONTEXTO]                  |\n"
            "+--------------------------------------------------------+\n"
            f"| Mensajes en contexto activo : {str(msg_count).ljust(25)}|\n"
            f"| Caracteres acumulados       : {str(char_count).ljust(25)}|\n"
            f"| Tokens estimados (~4 car/t) : {str(est_tokens).ljust(25)}|\n"
            "+--------------------------------------------------------+"
        )
        return True, output

    if cmd == "/export":
        active_history = history or []
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        if len(parts) > 1:
            raw_filename = parts[1].strip()
            if not raw_filename.endswith(".md"):
                raw_filename += ".md"
            target_path = base_dir / raw_filename
        else:
            target_path = base_dir / f"sesion_jarvis_{timestamp}.md"

        lines = [
            f"# Historial de Sesión de Jarvis CLI",
            f"- **Fecha de exportación**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Directorio de trabajo**: `{base_dir}`",
            f"- **Total de mensajes**: {len(active_history)}",
            "",
            "---",
            "",
        ]

        for idx, msg in enumerate(active_history, 1):
            role = msg.get("role", "unknown")
            content = str(msg.get("content") or "")

            if role == "system":
                lines.append(f"### ⚙️ Contexto del Sistema (Mensaje #{idx})\n")
                lines.append(f"```text\n{content}\n```\n")
            elif role == "user":
                lines.append(f"### 👤 Usuario (Mensaje #{idx})\n")
                lines.append(f"{content}\n")
            elif role == "assistant":
                lines.append(f"### 🤖 Jarvis (Mensaje #{idx})\n")
                lines.append(f"{content}\n")
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                lines.append(f"### 🔧 Resultado de Herramienta [{tool_call_id}] (Mensaje #{idx})\n")
                lines.append(f"```text\n{content}\n```\n")
            else:
                lines.append(f"### [{role.upper()}] (Mensaje #{idx})\n")
                lines.append(f"{content}\n")

        full_content = "\n".join(lines)
        try:
            target_path.write_text(full_content, encoding="utf-8")
            return True, f"\n[+] Sesión exportada exitosamente a:\n    {target_path.resolve()}"
        except Exception as exc:
            return True, f"\n[Error]: No se pudo exportar la sesión: {exc}"

    return False, ""


def build_directory_tree(
    root_dir: Path,
    max_depth: int = 3,
    ignore_dirs: Optional[Set[str]] = None,
) -> str:
    """Genera una representación visual en árbol del directorio con límite de profundidad."""
    ignores = ignore_dirs or {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".harness_sessions",
        ".gemini",
    }
    lines: list[str] = [f"📁 {root_dir.name or str(root_dir)}/"]

    def _walk(current: Path, prefix: str, depth: int):
        if depth > max_depth:
            lines.append(f"{prefix}└── ... (límite de profundidad alcanzado)")
            return

        try:
            entries = sorted(
                [e for e in current.iterdir() if e.name not in ignores],
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
        except Exception as exc:
            lines.append(f"{prefix}└── [Error: {exc}]")
            return

        total = len(entries)
        if total == 0:
            if depth > 1:
                lines.append(f"{prefix}└── (carpeta vacía)")
            elif depth == 1:
                lines.append("  └── (directorio vacío)")
            return

        for idx, entry in enumerate(entries):
            is_last = idx == total - 1
            connector = "└── " if is_last else "├── "
            extension_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                _walk(entry, prefix + extension_prefix, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    _walk(root_dir, "", 1)
    return "\n".join(lines)


def handle_diagnostics_command(
    command_line: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    cwd: Optional[Path] = None,
    runtime: Optional[SessionRuntime] = None,
    mcp_manager: Any = None,
) -> Tuple[bool, str]:
    """Procesa comandos de diagnóstico y exploración (/doctor, /tree, /diff)."""
    base_dir = cwd or Path.cwd()
    rt = runtime or get_session_runtime()
    parts = command_line.strip().split()
    if not parts:
        return False, ""

    cmd = parts[0].lower()

    if cmd == "/tree":
        depth = 3
        if len(parts) > 1:
            try:
                depth = max(1, min(10, int(parts[1])))
            except ValueError:
                pass
        tree_view = build_directory_tree(base_dir, max_depth=depth)
        output = (
            f"\n+--------------------------------------------------------+\n"
            f"| [ÁRBOL DE DIRECTORIO: {base_dir.name}] (profundidad: {depth})\n"
            f"+--------------------------------------------------------+\n"
            f"{tree_view}\n"
            f"+--------------------------------------------------------+"
        )
        return True, output

    if cmd == "/diff":
        diffs = rt.get_diffs(cwd=base_dir)
        if not diffs:
            return True, "\n[Diff]: No se han registrado modificaciones de archivos en la sesión activa."

        output_lines = [
            "\n+--------------------------------------------------------+",
            f"| [DIFERENCIAS REGISTRADAS EN LA SESIÓN] ({len(diffs)} archivo(s))",
            "+--------------------------------------------------------+",
        ]
        for d in diffs:
            output_lines.append(d)
            output_lines.append("----------------------------------------------------------")
        return True, "\n".join(output_lines)

    if cmd == "/doctor":
        report_lines = [
            "\n+--------------------------------------------------------+",
            "| [DIAGNÓSTICO DEL SISTEMA - HARNESS DOCTOR]              |",
            "+--------------------------------------------------------+",
            f"| Espacio de trabajo : {str(base_dir).ljust(35)}|",
            f"| Modo de ejecución  : {rt.mode.ljust(35)}|",
            f"| Política aprobación: {rt.approval_policy.ljust(35)}|",
            f"| Límite de pasos    : {str(rt.max_steps).ljust(35)}|",
            "+--------------------------------------------------------+",
        ]

        if not provider or not model:
            report_lines.append("| LLM Proveedor/Modelo: [NO CONFIGURADO]                 |")
            report_lines.append("|  -> Usa /model add <prov> <mod> para registrar uno     |")
        else:
            report_lines.append(f"| LLM Proveedor      : {provider.upper().ljust(35)}|")
            report_lines.append(f"| LLM Modelo         : {model.ljust(35)}|")

            # Chequeo de endpoints
            from harness.model_config import get_provider_endpoints, has_valid_key_for_provider
            from harness.llm_provider import SUPPORTED_PROVIDERS

            cfg_file = base_dir / ".harness_models.json"
            endpoints = get_provider_endpoints(cfg_file if cfg_file.exists() else None)
            endpoint = endpoints.get(provider.lower())
            if not endpoint and provider.lower() in SUPPORTED_PROVIDERS:
                endpoint = SUPPORTED_PROVIDERS[provider.lower()].get("base_url", "")

            if endpoint and any(local_k in provider.lower() for local_k in ("ollama", "lmstudio", "local", "custom")):
                report_lines.append(f"| Endpoint URL       : {endpoint[:35].ljust(35)}|")
                t0 = time.perf_counter()
                try:
                    ping_url = endpoint.rstrip("/")
                    if ping_url.endswith("/v1"):
                        ping_url += "/models"
                    req = urllib.request.Request(ping_url, headers={"User-Agent": "Jarvis-Doctor"})
                    with urllib.request.urlopen(req, timeout=2.0) as resp:
                        lat_ms = (time.perf_counter() - t0) * 1000
                        report_lines.append(f"| Estado de Conexión : [OK] Conectado ({lat_ms:.1f} ms)".ljust(57) + "|")
                except Exception as exc:
                    lat_ms = (time.perf_counter() - t0) * 1000
                    report_lines.append(f"| Estado de Conexión : [FAIL] No responde ({lat_ms:.1f} ms)".ljust(57) + "|")
                    report_lines.append(f"| Detalle del fallo  : {str(exc)[:35].ljust(35)}|")
            else:
                has_k = has_valid_key_for_provider(provider)
                k_status = "[OK] Clave detectada" if has_k else "[AVISO] Sin clave configurada"
                report_lines.append(f"| Estado Credenciales: {k_status.ljust(35)}|")

        report_lines.append("+--------------------------------------------------------+")
        report_lines.append("| SERVIDORES MCP:                                        |")
        if mcp_manager is None:
            report_lines.append("|  - Sin gestor de MCP inicializado                      |")
        else:
            rep = mcp_manager.report()
            for line in rep.splitlines()[:6]:
                report_lines.append(f"|  {line[:52]}".ljust(57) + "|")
        report_lines.append("+--------------------------------------------------------+")

        return True, "\n".join(report_lines)

    return False, ""
