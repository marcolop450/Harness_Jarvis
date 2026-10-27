"""La CLI comparte despacho y cierra el gestor incluso al fallar."""
import io
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch
import main
from harness.llm_provider import NormalizedResponse, NormalizedToolCall


class MCPCLITests(unittest.TestCase):
    def manager(self):
        manager = MagicMock()
        manager.workspace = Path.cwd()
        manager.confirm_fn = None
        manager.config_error = ""
        manager.connections = {}
        manager.definitions.return_value = [{"type": "function", "function": {
            "name": "mcp_fetch__fetch", "parameters": {"type": "object"}}}]
        manager.execute.return_value = "contenido remoto"
        manager.__enter__.return_value = manager
        return manager

    def test_status_and_reconnect_without_model(self):
        manager = self.manager()
        manager.report.return_value = "fetch: conectado"
        manager.reconnect.return_value = "fetch: conectado"
        with patch("sys.stdout", io.StringIO()) as out:
            for command in ("/mcp", "/mcp reconnect"):
                self.assertTrue(main.handle_slash_command(command, None, None, Path.cwd(), mcp_manager=manager)[2])
        self.assertIn("fetch: conectado", out.getvalue())
        manager.reconnect.assert_called_once()

    def test_turn_sends_real_tool_result_into_history(self):
        manager = self.manager()
        calls = []
        def caller(**kwargs):
            calls.append(list(kwargs["messages"]))
            if len(calls) == 1:
                self.assertIn("mcp_fetch__fetch", str(kwargs["tools"]))
                return NormalizedResponse(tool_calls=[NormalizedToolCall("id1", "mcp_fetch__fetch", {"url": "https://example.com"})])
            self.assertEqual(kwargs["messages"][-1]["content"], "contenido remoto")
            return NormalizedResponse(content="listo")
        reply, history = main.run_turn(manager, prompt="consulta", llm_caller=caller)
        self.assertIn("listo", reply)
        manager.execute.assert_called_once()
        self.assertEqual(history[-2]["role"], "tool")

    def test_direct_mode_closes_manager_on_failure(self):
        manager = self.manager()
        with patch("main.MCPManager", return_value=manager), patch("main.run_turn", side_effect=RuntimeError("fallo")), \
             patch("main.load_model_memory", return_value={}), patch("main.build_workspace_system_prompt", return_value="sys"), \
             patch("sys.stderr", io.StringIO()):
            self.assertEqual(main.main(["--provider", "ollama", "-p", "hola"]), 1)
        manager.__exit__.assert_called_once()

    def test_repl_closes_after_exit_and_interrupt(self):
        for input_value in ("exit", KeyboardInterrupt):
            manager = self.manager()
            with patch("main.MCPManager", return_value=manager), patch("main.load_model_memory", return_value={}), \
                 patch("main.load_session_history", return_value=[]), patch("builtins.input", side_effect=[input_value]), \
                 patch("sys.stdout", io.StringIO()):
                self.assertEqual(main.run_repl(), 0)
            manager.__exit__.assert_called_once()

    def test_trace_excludes_arguments(self):
        with patch("sys.stdout", io.StringIO()) as output:
            main.print_mcp_event("fetch", "fetch", "ok")
        self.assertEqual(output.getvalue().strip(), "[MCP fetch/fetch] ok")


if __name__ == "__main__":
    unittest.main()
