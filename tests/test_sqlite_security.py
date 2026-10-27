"""Comprobar efectos reales de permisos SQL, no solo prefijos del texto."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from harness.tools import execute_tool, get_tools_definitions, tool_sqlite_query, truncate_output


class SQLiteSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.db = self.base / "data.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute("CREATE TABLE items (id INTEGER)")
            conn.execute("INSERT INTO items VALUES (7)")
        conn.close()

    def test_read_does_not_confirm_or_create(self):
        def never(*args):
            self.fail("Una lectura no debe solicitar aprobación")
        result = tool_sqlite_query("SELECT * FROM items", str(self.db), self.base, never)
        self.assertIn("7", result)
        result = tool_sqlite_query("SELECT 1", "missing.db", self.base, never)
        self.assertIn("Error", result)
        self.assertFalse((self.base / "missing.db").exists())

    def test_rejected_write_and_cte_do_not_mutate(self):
        for query in ("DELETE FROM items", "WITH ids AS (SELECT 7) DELETE FROM items WHERE id IN ids"):
            self.assertIn("cancelada", tool_sqlite_query(query, str(self.db), self.base, lambda *_: False))
        self.assertIn("7", tool_sqlite_query("SELECT * FROM items", str(self.db), self.base))
        self.assertIn("cancelada", tool_sqlite_query("CREATE TABLE x(id)", "new.db", self.base, lambda *_: False))
        self.assertFalse((self.base / "new.db").exists())

    def test_approved_write_works(self):
        self.assertIn("éxito", tool_sqlite_query("INSERT INTO items VALUES (8)", str(self.db), self.base, lambda *_: True))
        self.assertIn("8", tool_sqlite_query("SELECT * FROM items", str(self.db), self.base))

    def test_external_sql_and_extensions_always_denied(self):
        for query in ("ATTACH DATABASE 'escape.db' AS other", "PRAGMA writable_schema=1", "SELECT load_extension('x')"):
            result = tool_sqlite_query(query, str(self.db), self.base, lambda *_: True)
            self.assertIn("bloqueada", result)
        self.assertFalse((self.base / "escape.db").exists())

    def test_native_tools_protect_mcp_config_and_histories(self):
        for path in ("mcp.json", ".harness_sessions/x.json", ".git/config"):
            result = execute_tool("write_file", {"path": path, "content": "x"}, self.base, lambda *_: True)
            self.assertIn("Violación de seguridad", result)

    def test_legacy_mcp_names_unavailable_and_limit_is_strict(self):
        self.assertFalse(any(t["function"]["name"].startswith("mcp_") for t in get_tools_definitions()))
        self.assertIn("no existe", execute_tool("mcp_fetch", {"url": "https://example.com"}))
        self.assertEqual(len(truncate_output("X" * 8000)), 4000)
        self.assertLessEqual(len(execute_tool("X" * 8000, {})), 4000)


if __name__ == "__main__":
    unittest.main()
