import tempfile
import unittest
from pathlib import Path
from harness.tools import (
    RiskLevel,
    TOOL_RISK_MAP,
    execute_tool,
    get_tools_definitions,
    tool_edit_file,
    tool_list_dir,
    tool_mcp_fetch,
    tool_mcp_git_info,
    tool_mcp_sqlite_query,
    tool_read_file,
    tool_run_command,
    tool_search_code,
    tool_write_file,
    truncate_output,
)


class TestToolsDefinitions(unittest.TestCase):
    def test_tools_catalog_includes_core_and_mcp(self):
        tools = get_tools_definitions()
        self.assertEqual(len(tools), 9)
        names = {t["function"]["name"] for t in tools}
        expected = {
            "read_file",
            "write_file",
            "edit_file",
            "list_dir",
            "run_command",
            "search_code",
            "mcp_fetch",
            "mcp_git_info",
            "mcp_sqlite_query",
        }
        self.assertEqual(names, expected)

    def test_tools_schema_structure(self):
        tools = get_tools_definitions()
        for t in tools:
            self.assertEqual(t["type"], "function")
            fn = t["function"]
            self.assertIn("name", fn)
            self.assertIn("description", fn)
            params = fn["parameters"]
            self.assertEqual(params["type"], "object")
            self.assertIn("properties", params)
            self.assertIn("required", params)

    def test_risk_classification(self):
        self.assertEqual(TOOL_RISK_MAP["read_file"], RiskLevel.AUTO)
        self.assertEqual(TOOL_RISK_MAP["list_dir"], RiskLevel.AUTO)
        self.assertEqual(TOOL_RISK_MAP["search_code"], RiskLevel.AUTO)
        self.assertEqual(TOOL_RISK_MAP["write_file"], RiskLevel.CONFIRM)
        self.assertEqual(TOOL_RISK_MAP["edit_file"], RiskLevel.CONFIRM)
        self.assertEqual(TOOL_RISK_MAP["run_command"], RiskLevel.CONFIRM)


class TestReadingTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name).resolve()

        (self.base / "sample.txt").write_text("linea 1\nlinea 2\nlinea 3\nlinea 4\n", encoding="utf-8")
        sub = self.base / "subdir"
        sub.mkdir()
        (sub / "nested.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_truncate_output_below_and_above_limit(self):
        short_text = "abc"
        self.assertEqual(truncate_output(short_text, max_chars=10), "abc")

        long_text = "a" * 15
        truncated = truncate_output(long_text, max_chars=10)
        self.assertTrue(truncated.startswith("a" * 10))
        self.assertIn("Salida truncada", truncated)

    def test_read_file_full_and_range(self):
        full = tool_read_file("sample.txt", base_dir=self.base)
        self.assertIn("linea 1", full)
        self.assertIn("linea 4", full)

        ranged = tool_read_file("sample.txt", start_line=2, end_line=3, base_dir=self.base)
        self.assertIn("2: linea 2", ranged)
        self.assertIn("3: linea 3", ranged)
        self.assertNotIn("linea 1", ranged)

    def test_read_file_non_existent(self):
        res = tool_read_file("missing.txt", base_dir=self.base)
        self.assertIn("no existe", res)

    def test_list_dir(self):
        res = tool_list_dir(".", max_depth=2, base_dir=self.base)
        self.assertIn("sample.txt", res)
        self.assertIn("subdir/", res)
        self.assertIn("nested.py", res)

    def test_search_code(self):
        res = tool_search_code("hello", path=".", base_dir=self.base)
        self.assertIn("nested.py:1: def hello():", res)

        no_match = tool_search_code("patron_inexistente", path=".", base_dir=self.base)
        self.assertIn("No se encontraron coincidencias", no_match)


class TestModificationTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_file_confirmed(self):
        res = tool_write_file(
            "new_file.txt",
            "Hola mundo",
            base_dir=self.base,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("exitosamente", res)
        self.assertEqual((self.base / "new_file.txt").read_text(encoding="utf-8"), "Hola mundo")

    def test_write_file_rejected(self):
        res = tool_write_file(
            "cancelled.txt",
            "Texto",
            base_dir=self.base,
            confirm_fn=lambda _d, _det: False,
        )
        self.assertIn("cancelada", res)
        self.assertFalse((self.base / "cancelled.txt").exists())

    def test_edit_file_confirmed(self):
        target_file = self.base / "to_edit.txt"
        target_file.write_text("Hello World\nGoodbye World", encoding="utf-8")

        res = tool_edit_file(
            "to_edit.txt",
            target="Hello World",
            replacement="Hi Universe",
            base_dir=self.base,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("editado exitosamente", res)
        self.assertIn("Hi Universe", target_file.read_text(encoding="utf-8"))

    def test_edit_file_target_not_found(self):
        target_file = self.base / "to_edit2.txt"
        target_file.write_text("Hello World", encoding="utf-8")

        res = tool_edit_file(
            "to_edit2.txt",
            target="Missing Target",
            replacement="Something",
            base_dir=self.base,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("No se encontró la cadena 'target'", res)

    def test_run_command_confirmed(self):
        res = tool_run_command("echo test_run", cwd=self.base, confirm_fn=lambda _d, _det: True)
        self.assertIn("test_run", res)

    def test_run_command_rejected(self):
        res = tool_run_command("echo test_run", cwd=self.base, confirm_fn=lambda _d, _det: False)
        self.assertIn("cancelada", res)


class TestExecuteToolDispatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_execute_unknown_tool(self):
        res = execute_tool("unknown_tool", {}, base_dir=self.base)
        self.assertIn("no existe en el catálogo", res)

    def test_execute_tool_write_and_read(self):
        write_res = execute_tool(
            "write_file",
            {"path": "test.txt", "content": "contenido de prueba"},
            base_dir=self.base,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("exitosamente", write_res)

        read_res = execute_tool("read_file", {"path": "test.txt"}, base_dir=self.base)
        self.assertEqual(read_res, "contenido de prueba")

    def test_execute_tool_blocks_env(self):
        res = execute_tool("read_file", {"path": ".env"}, base_dir=self.base)
        self.assertIn("Violación de seguridad", res)
        self.assertIn("confidencial", res)


class TestMCPTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_mcp_fetch_validates_url_protocol(self):
        res = tool_mcp_fetch("ftp://example.com")
        self.assertIn("Solo se admiten URLs", res)

    def test_mcp_fetch_mocked_success(self):
        from unittest.mock import MagicMock, patch
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers.get_content_type.return_value = "application/json"
        mock_resp.headers.get_content_charset.return_value = "utf-8"
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            out = tool_mcp_fetch("https://api.example.com/data")
            self.assertIn("MCP Fetch Status 200", out)
            self.assertIn('{"status": "ok"}', out)

    def test_mcp_git_info_subcommands(self):
        # Subcomando no soportado
        bad = tool_mcp_git_info("unsupported_subcmd", base_dir=self.base)
        self.assertIn("no soportado", bad)

        # Consulta status sobre el repo actual
        status_out = tool_mcp_git_info("status", base_dir=Path.cwd())
        self.assertIn("MCP Git status", status_out)

        # Despacho via execute_tool
        exec_out = execute_tool("mcp_git_info", {"subcommand": "branch"}, base_dir=Path.cwd())
        self.assertIn("MCP Git branch", exec_out)

    def test_mcp_sqlite_query_in_memory_and_file(self):
        # Crear tabla e insertar fila
        create_res = tool_mcp_sqlite_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
            db_path=":memory:",
        )
        self.assertIn("Sentencia ejecutada con éxito", create_res)

        # Base de datos en archivo
        db_file = self.base / "test.db"
        init_res = tool_mcp_sqlite_query(
            "CREATE TABLE items (id INT, title TEXT); INSERT INTO items VALUES (1, 'Arnes');",
            db_path=str(db_file),
            base_dir=self.base,
        )
        self.assertIn("Sentencia ejecutada", init_res)

        # Consultar SELECT
        select_res = tool_mcp_sqlite_query(
            "SELECT * FROM items;",
            db_path=str(db_file),
            base_dir=self.base,
        )
        self.assertIn("Arnes", select_res)
        self.assertIn("title", select_res)

        # Error de sintaxis SQL
        err_res = tool_mcp_sqlite_query("SELECT FROM INVALID;", db_path=":memory:")
        self.assertIn("MCP SQLite Error", err_res)

        # Bloqueo de path traversal o archivo protegido en sqlite
        blocked = execute_tool(
            "mcp_sqlite_query",
            {"query": "SELECT 1;", "db_path": ".env"},
            base_dir=self.base,
        )
        self.assertIn("Violación de seguridad", blocked)


if __name__ == "__main__":
    unittest.main()
