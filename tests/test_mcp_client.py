"""Contratos del cliente MCP sin red ni procesos externos."""
import asyncio
from pathlib import Path
import json
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

from harness.mcp_client import Connection, MCPManager, ServerConfig, bounded_text, discover_tools, load_config
from harness.mcp_policy import prepare_call, validate_public_url


def tool(name="fetch"):
    return NS(name=name, description="Prueba", input_schema={"type": "object", "properties": {}})


class FakeClient:
    def __init__(self, delay=0, fail=False):
        self.delay, self.fail, self.closed = delay, fail, False
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        self.closed = True
    async def list_tools(self, **kwargs):
        return NS(tools=[tool()], next_cursor=None)
    async def call_tool(self, *args, **kwargs):
        await asyncio.sleep(self.delay)
        if self.fail:
            raise ConnectionError("Servidor desconectado")
        return NS(content=[NS(type="text", text="respuesta")], structured_content=None, is_error=False)


class MCPClientTests(unittest.TestCase):
    def test_config_portable_and_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.assertEqual(load_config(base), [])
            (base / "mcp.json").write_text(json.dumps({"mcpServers": {"fetch": {
                "command": "${python}", "args": ["-m", "mcp_server_fetch"], "allowed_tools": ["fetch"]}}}))
            config = load_config(base)[0]
            self.assertTrue(Path(config.command).is_absolute())
            self.assertEqual(config.timeout, 30)

    def test_invalid_config_does_not_start(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "mcp.json").write_text('{broken')
            with MCPManager(Path(folder)) as manager, patch.object(Connection, "start") as start:
                self.assertIn("configuración", manager.report())
                start.assert_not_called()

    def test_config_rejects_private_override(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "mcp.json").write_text(json.dumps({"mcpServers": {"fetch": {
                "command": "python", "args": ["--allow-private-ips"], "allowed_tools": ["fetch"]}}}))
            with self.assertRaises(ValueError):
                load_config(Path(folder))

    def test_pagination_allowlist_and_duplicate(self):
        config = ServerConfig("fetch", "unused", [], frozenset({"fetch"}))
        client = NS(list_tools=AsyncMock(side_effect=[NS(tools=[tool("forbidden")], next_cursor="2"),
                                                     NS(tools=[tool()], next_cursor=None)]))
        result = asyncio.run(discover_tools(client, config))
        self.assertEqual(list(result), ["mcp_fetch__fetch"])
        self.assertEqual(client.list_tools.call_args.kwargs, {"cursor": "2"})
        client.list_tools = AsyncMock(return_value=NS(tools=[tool()], next_cursor="same"))
        with self.assertRaises(ValueError):
            asyncio.run(discover_tools(client, config))

    def test_public_url_policy_and_dns(self):
        for url in ("file:///etc/passwd", "ftp://example.com", "https://user:pass@example.com", "https://example.com:8080"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                prepare_call("fetch", "fetch", {"url": url}, Path.cwd())
        async def check(address):
            loop = asyncio.get_running_loop()
            with patch.object(loop, "getaddrinfo", AsyncMock(return_value=[(0, 0, 0, "", (address, 0))])):
                await validate_public_url("https://example.com")
        for address in ("127.0.0.1", "10.1.2.3", "::1", "169.254.169.254", "::ffff:127.0.0.1", "64:ff9b::7f00:1"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                asyncio.run(check(address))
        asyncio.run(check("93.184.215.14"))

    def test_server_guard_blocks_redirect_before_send(self):
        # Ejercita la política del paquete fijado usando transporte HTTP simulado:
        # primera URL pública -> Location privado -> hook rechaza antes del envío.
        import httpx
        from mcp_server_fetch.server import _refuse_private_destination
        seen = []
        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})
        async def run():
            async def resolve(host):
                return ["127.0.0.1" if host == "127.0.0.1" else "93.184.215.14"]
            with patch("mcp_server_fetch.server._resolve_host", resolve):
                async with httpx.AsyncClient(transport=httpx.MockTransport(handler),
                        event_hooks={"request": [_refuse_private_destination]}) as client:
                    await client.get("https://example.com", follow_redirects=True)
        with self.assertRaises(Exception):
            asyncio.run(run())
        self.assertEqual(seen, ["https://example.com"])

    def test_connection_lifecycle_timeout_and_disconnect(self):
        for delay, fail in ((0, False), (0.2, False), (0, True)):
            fake = FakeClient(delay, fail)
            config = ServerConfig("fetch", "unused", [], frozenset({"fetch"}), 0.05)
            with patch("harness.mcp_client.validate_public_url", AsyncMock()):
                conn = Connection(config, Path.cwd(), lambda: fake).start()
                self.assertEqual(conn.status, "conectado")
                try:
                    if delay or fail:
                        with self.assertRaises(Exception):
                            conn.call("fetch", {"url": "https://example.com"})
                    else:
                        self.assertFalse(conn.call("fetch", {"url": "https://example.com"}).is_error)
                finally:
                    conn.close()
                self.assertFalse(conn.thread.is_alive())
                self.assertTrue(fake.closed)

    def test_start_failure_and_reconnect(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = MCPManager(Path(folder))
            manager.started = True
            config = ServerConfig("fetch", "unused", [], frozenset({"fetch"}))
            failed = NS(status="error", config=config, close=lambda: None)
            manager.connections["fetch"] = failed
            replacement = NS(status="conectado", error="", catalog={"mcp_fetch__fetch": {}}, close=lambda: None)
            with patch("harness.mcp_client.Connection") as factory:
                factory.return_value.start.return_value = replacement
                self.assertIn("conectado", manager.reconnect())
                self.assertEqual(factory.call_count, 1)
                manager.reconnect()
                self.assertEqual(factory.call_count, 1)

    def test_truncation_and_unknown_tool(self):
        self.assertEqual(len(bounded_text("x" * 5000)), 4000)
        self.assertIn("truncada", bounded_text("x" * 5000))
        with tempfile.TemporaryDirectory() as folder, MCPManager(Path(folder)) as manager:
            self.assertIn("no disponible", manager.execute("mcp_fetch__fetch", {}))


if __name__ == "__main__":
    unittest.main()
