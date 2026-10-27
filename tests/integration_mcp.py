"""Pruebas REALES opt-in: python -m unittest discover -s tests -p integration_mcp.py -v.

Requieren instalación local de los tres servidores y red para example.com.
No se incluyen en test_*.py ni necesitan un modelo LLM.
"""
from pathlib import Path
import sys
import tempfile
import unittest

from harness.mcp_client import Connection, MCPManager, PROJECT_ROOT, ServerConfig


class RealMCPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = []
        cls.manager = MCPManager(PROJECT_ROOT, confirm_fn=lambda *_: True,
                                 on_event=lambda *event: cls.events.append(event))
        cls.manager.start()

    @classmethod
    def tearDownClass(cls):
        cls.manager.close()
        assert all(not conn.thread.is_alive() for conn in cls.manager.connections.values())

    def test_01_three_servers_connected(self):
        self.assertEqual(set(self.manager.connections), {"fetch", "git", "filesystem"})
        self.assertTrue(all(c.status == "conectado" for c in self.manager.connections.values()), self.manager.report())
        self.assertEqual(len(self.manager.definitions()), 11)

    def test_02_fetch(self):
        result = self.manager.execute("mcp_fetch__fetch", {"url": "https://example.com", "max_length": 1000})
        self.assertIn("Example Domain", result)
        self.assertIn(("fetch", "fetch", "ok"), self.events)

    def test_03_git_status_log_and_diff(self):
        for name in ("git_status", "git_log", "git_diff_unstaged", "git_diff_staged"):
            result = self.manager.execute("mcp_git__" + name, {"repo_path": str(PROJECT_ROOT)})
            self.assertNotIn("[Error MCP", result, name)
        self.assertIn(("git", "git_log", "ok"), self.events)

    def test_04_filesystem_and_rejection(self):
        demo = PROJECT_ROOT / ".mcp-demo"
        demo.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=demo) as folder:
            file = Path(folder) / "mcp.txt"
            self.manager.confirm_fn = lambda *_: True
            result = self.manager.execute("mcp_filesystem__write_file", {"path": str(file), "content": "real MCP"})
            self.assertNotIn("[Error MCP", result)
            result = self.manager.execute("mcp_filesystem__read_multiple_files", {"paths": [str(file)]})
            self.assertIn("real MCP", result)
            result = self.manager.execute("mcp_filesystem__edit_file", {"path": str(file),
                "edits": [{"oldText": "real MCP", "newText": "editado por MCP"}]})
            self.assertNotIn("[Error MCP", result)
            self.assertEqual(file.read_text(), "editado por MCP")
            self.manager.confirm_fn = lambda *_: False
            result = self.manager.execute("mcp_filesystem__write_file", {"path": str(file), "content": "NO"})
            self.assertIn("cancelada", result)
            self.assertEqual(file.read_text(), "editado por MCP")
            result = self.manager.execute("mcp_filesystem__read_multiple_files", {"paths": [str(file), str(PROJECT_ROOT / '.env')]})
            self.assertIn("[Error MCP", result)
            for name, args in (("list_directory", {"path": folder}), ("search_files", {"path": folder, "pattern": "*.txt"})):
                self.assertIn("mcp.txt", self.manager.execute("mcp_filesystem__" + name, args))

    def test_05_missing_process_and_handshake_timeout(self):
        for command, args in (("jarvis-nonexistent-server-123", []),
                              (sys.executable, ["-c", "import time; time.sleep(60)"])):
            config = ServerConfig("fetch", command, args, frozenset({"fetch"}), 0.3)
            conn = Connection(config, PROJECT_ROOT).start()
            conn.close()
            self.assertEqual(conn.status, "error")
            self.assertFalse(conn.thread.is_alive())


if __name__ == "__main__":
    unittest.main()
