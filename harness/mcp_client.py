"""Puente síncrono hacia MCP por stdio, sin descargas ni fallback local.

Cada conexión posee un hilo y una tarea asyncio. Esa MISMA tarea abre y cierra
los contextos AnyIO del SDK; las llamadas llegan mediante una cola. No cerrar
un contexto MCP desde run_coroutine_threadsafe en otra tarea.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import Future
from contextlib import AsyncExitStack
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
from typing import Any, Callable

from jsonschema import Draft202012Validator
from mcp import Client, StdioServerParameters, stdio_client

from harness.mcp_policy import ALLOWED_TOOLS, filter_result, prepare_call, validate_public_url

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
OUTPUT_LIMIT = 4000


def bounded_text(text: str) -> str:
    suffix = "\n[Salida truncada]"
    return text if len(text) <= OUTPUT_LIMIT else text[:OUTPUT_LIMIT-len(suffix)] + suffix


def clean_error(error: BaseException) -> str:
    # ExceptionGroup del transporte: mostrar la causa útil, no un traceback.
    children = getattr(error, "exceptions", ())
    if children:
        return clean_error(children[0])
    if isinstance(error, (TimeoutError, asyncio.CancelledError)):
        return "Tiempo límite agotado o conexión interrumpida."
    return (str(error).splitlines() or [type(error).__name__])[0][:300]


@dataclass(frozen=True)
class ServerConfig:
    name: str
    command: str
    args: list[str]
    allowed_tools: frozenset[str]
    timeout: float = 30.0


def load_config(workspace: Path, project: Path = PROJECT_ROOT) -> list[ServerConfig]:
    path = workspace / "mcp.json"
    if not path.exists():
        return []
    if path.is_symlink() or path.resolve().parent != workspace.resolve():
        raise ValueError("mcp.json debe pertenecer al espacio de trabajo.")
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data["mcpServers"]
    if not isinstance(servers, dict):
        raise ValueError("mcpServers debe ser un objeto.")
    node = project / "node_modules/node/bin" / ("node.exe" if os.name == "nt" else "node")
    substitutions = {"${python}": sys.executable, "${workspace}": str(workspace),
                     "${project}": str(project), "${node}": str(node)}

    def expand(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Comandos y argumentos MCP deben ser texto.")
        for key, replacement in substitutions.items():
            value = value.replace(key, replacement)
        if "${" in value:
            raise ValueError("Variable desconocida en mcp.json.")
        return value

    result = []
    for name, entry in servers.items():
        if name not in ("fetch", "git", "filesystem") or not isinstance(entry, dict):
            raise ValueError("Servidor MCP desconocido o configuración inválida.")
        if entry.get("enabled", True) is False:
            continue
        args = entry.get("args", [])
        allowed = entry["allowed_tools"]
        if not isinstance(args, list) or not isinstance(allowed, list) or not all(isinstance(n, str) for n in allowed):
            raise ValueError("args y allowed_tools deben ser listas.")
        timeout = float(entry.get("timeout_seconds", 30))
        if not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ValueError("timeout_seconds debe estar entre 0 y 30.")
        expanded = [expand(arg) for arg in args]
        if name == "fetch" and any(a.startswith(("--allow-private-ips", "--proxy-url", "--ignore-robots-txt")) for a in expanded):
            raise ValueError("No se permite desactivar la política de Fetch.")
        command = expand(entry["command"])
        if not command:
            raise ValueError("El comando MCP está vacío.")
        result.append(ServerConfig(name, command, expanded, frozenset(allowed), timeout))
    return result


async def discover_tools(client: Client, config: ServerConfig) -> dict[str, dict[str, Any]]:
    catalog = {}
    cursor = None
    seen = set()
    for _ in range(100):
        page = await client.list_tools(cursor=cursor)
        for tool in page.tools:
            if tool.name not in config.allowed_tools or tool.name not in ALLOWED_TOOLS.get(config.name, set()):
                continue
            name = f"mcp_{config.name}__{tool.name}"
            if not NAME_PATTERN.fullmatch(name) or len(name) > 64 or name in catalog:
                raise ValueError("Nombre MCP duplicado o incompatible con el modelo.")
            schema = tool.input_schema
            Draft202012Validator.check_schema(schema)
            if schema.get("type") != "object":
                raise ValueError("La herramienta MCP requiere un esquema de objeto.")
            catalog[name] = {"type": "function", "function": {
                "name": name, "description": f"[MCP {config.name}] {tool.description or tool.name}"[:1000],
                "parameters": schema}}
        cursor = page.next_cursor
        if cursor is None:
            return catalog
        if cursor in seen:
            raise ValueError("Paginación MCP repetida.")
        seen.add(cursor)
    raise ValueError("Demasiadas páginas de herramientas MCP.")


class Connection:
    """Una sesión remota con propietario único y cierre acotado."""
    def __init__(self, config: ServerConfig, workspace: Path, client_factory=None):
        self.config, self.workspace = config, workspace
        self.client_factory = client_factory
        self.catalog: dict[str, dict[str, Any]] = {}
        self.status, self.error = "pendiente", ""
        self.ready: Future = Future()
        self.loop = None
        self.queue = None
        self.task = None
        self.thread = threading.Thread(target=self._run, name=f"jarvis-mcp-{config.name}", daemon=True)

    def start(self):
        self.thread.start()
        try:
            self.ready.result(timeout=self.config.timeout + 10)
        except Exception as exc:
            self.status, self.error = "error", clean_error(exc)
            self.close()
        return self

    def _run(self):
        asyncio.run(self._serve())

    async def _serve(self):
        self.loop = asyncio.get_running_loop()
        self.task = asyncio.current_task()
        self.queue = asyncio.Queue()
        watchdog = self.loop.call_later(self.config.timeout, self.task.cancel)
        current = None
        try:
            async with AsyncExitStack() as stack:
                if self.client_factory:
                    client = await stack.enter_async_context(self.client_factory())
                else:
                    params = StdioServerParameters(command=self.config.command, args=self.config.args,
                        cwd=str(self.workspace), env={"PYTHONUTF8": "1"})
                    # Logs del servidor no se mezclan con stdout JSON-RPC ni con la CLI.
                    log = stack.enter_context(open(os.devnull, "w", encoding="utf-8"))
                    client = await stack.enter_async_context(Client(stdio_client(params, errlog=log),
                        mode="legacy", read_timeout_seconds=self.config.timeout, cache=None))
                self.catalog = await discover_tools(client, self.config)
                watchdog.cancel()
                self.status = "conectado"
                self.ready.set_result(True)
                while True:
                    request = await self.queue.get()
                    if request is None:
                        break
                    name, args, current = request
                    try:
                        result = await asyncio.wait_for(self._call(client, name, args), self.config.timeout)
                        current.set_result(result)
                        current = None
                    except Exception as exc:
                        current.set_exception(exc)
                        current = None
                        raise  # Una sesión rota no se reutiliza silenciosamente.
        except BaseException as exc:
            self.status, self.error = "error", clean_error(exc)
            if current is not None and not current.done():
                current.set_exception(RuntimeError(self.error))
        finally:
            watchdog.cancel()
            self.catalog = {}
            if not self.ready.done():
                self.ready.set_result(False)
            while not self.queue.empty():
                request = self.queue.get_nowait()
                if request is not None and not request[2].done():
                    request[2].set_exception(RuntimeError(self.error or "Conexión cerrada."))
            if self.status != "error":
                self.status = "cerrado"

    async def _call(self, client, name, args):
        if self.config.name == "fetch":
            await validate_public_url(args["url"])
        return await client.call_tool(name, arguments=args)

    def call(self, name, args):
        if self.status != "conectado" or not self.thread.is_alive():
            raise RuntimeError(self.error or "Servidor desconectado.")
        future: Future = Future()
        self.loop.call_soon_threadsafe(self.queue.put_nowait, (name, args, future))
        try:
            return future.result(timeout=self.config.timeout + 2)
        except BaseException:
            self.status = "error"
            self.close()
            raise

    def close(self):
        if not self.thread.is_alive():
            return
        try:
            if self.loop is not None and self.queue is not None:
                self.loop.call_soon_threadsafe(self.queue.put_nowait, None)
            self.thread.join(timeout=1)
            if self.thread.is_alive():
                if self.loop is not None and self.task is not None:
                    self.loop.call_soon_threadsafe(self.task.cancel)
                self.thread.join(timeout=10)
        except RuntimeError:
            pass  # El loop acaba de cerrarse.


class MCPManager:
    def __init__(self, workspace: Path | None = None, *, confirm_fn=None,
                 on_event: Callable[[str, str, str], None] | None = None):
        self.workspace = (workspace or Path.cwd()).resolve()
        self.confirm_fn, self.on_event = confirm_fn, on_event
        self.connections: dict[str, Connection] = {}
        self.config_error = ""
        self.started = False

    def start(self):
        if self.started:
            return
        self.started = True
        try:
            configs = load_config(self.workspace)
        except Exception as exc:
            self.config_error = clean_error(exc)
            return
        try:
            for config in configs:
                connection = Connection(config, self.workspace)
                self.connections[config.name] = connection
                connection.start()
        except BaseException:
            self.close()
            raise

    def definitions(self):
        self.start()
        return [definition for conn in self.connections.values() if conn.status == "conectado"
                for definition in conn.catalog.values()]

    def execute(self, full_name: str, arguments: dict[str, Any]) -> str:
        self.start()
        server, name = "desconocido", full_name
        state = "error"
        try:
            prefix, name = full_name.split("__", 1)
            server = prefix.removeprefix("mcp_")
            conn = self.connections.get(server)
            if conn is None or full_name not in conn.catalog:
                raise ValueError("Herramienta MCP no disponible; consulta /mcp.")
            schema = conn.catalog[full_name]["function"]["parameters"]
            Draft202012Validator(schema).validate(arguments)
            args = prepare_call(server, name, arguments, self.workspace, self.confirm_fn)
            result = conn.call(name, args)
            text = "\n".join(block.text for block in result.content if getattr(block, "type", None) == "text")
            if not text and result.structured_content is not None:
                text = json.dumps(result.structured_content, ensure_ascii=False)
            text = filter_result(server, name, text, args, self.workspace)
            state = "error" if result.is_error else "ok"
            return bounded_text(("[Error MCP] " if result.is_error else "") + text)
        except Exception as exc:
            return bounded_text(f"[Error MCP {server}]: {clean_error(exc)}")
        finally:
            if self.on_event:
                self.on_event(server, name, state)

    def report(self):
        self.start()
        if self.config_error:
            return f"[MCP configuración]: {self.config_error}"
        if not self.connections:
            return "[MCP]: Sin servidores configurados en mcp.json."
        lines = []
        for name, conn in self.connections.items():
            lines.append(f"{name}: {conn.status}" + (f" — {conn.error}" if conn.error else ""))
            lines.extend(f"  {tool}" for tool in conn.catalog)
        return "\n".join(lines)

    def reconnect(self):
        if self.config_error:
            self.close()
            self.connections.clear()
            self.config_error = ""
            self.started = False
        self.start()
        for name, old in list(self.connections.items()):
            if old.status != "conectado":
                old.close()
                self.connections[name] = Connection(old.config, self.workspace).start()
        return self.report()

    def close(self):
        for conn in self.connections.values():
            conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
