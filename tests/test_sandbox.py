"""Suite de verificación en Sandbox aislado (tests/sandbox_tmp/).

Verifica de forma integral:
1. Operaciones permitidas de las 6 herramientas en sandbox.
2. Bloqueo estricto e intransigente ante archivos .env y confidenciales.
3. Bloqueo ante intentos de Path Traversal (escape de cwd).
4. Flujo interactivo de cancelación por el usuario.
5. Truncado a 4000 caracteres y tolerancia a fallos.
"""

import shutil
import unittest
from pathlib import Path

from harness.tools import (
    execute_tool,
    tool_edit_file,
    tool_list_dir,
    tool_read_file,
    tool_run_command,
    tool_search_code,
    tool_write_file,
    truncate_output,
)


class TestSandboxEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox_dir = (Path(__file__).parent / "sandbox_tmp").resolve()
        if cls.sandbox_dir.exists():
            shutil.rmtree(cls.sandbox_dir)
        cls.sandbox_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.sandbox_dir.exists():
            shutil.rmtree(cls.sandbox_dir)

    def setUp(self):
        # Limpieza interna entre tests
        for item in self.sandbox_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # ---------------------------------------------------------
    # 1. Verificación Funcional de Herramientas en Sandbox
    # ---------------------------------------------------------

    def test_sandbox_write_and_read_file(self):
        write_res = tool_write_file(
            "sample.txt",
            "Contenido inicial en sandbox\nSegunda linea de prueba\n",
            base_dir=self.sandbox_dir,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("exitosamente", write_res)

        read_res = tool_read_file("sample.txt", base_dir=self.sandbox_dir)
        self.assertIn("Contenido inicial en sandbox", read_res)

    def test_sandbox_edit_file(self):
        tool_write_file(
            "code.py",
            "def calculate(x):\n    return x * 2\n",
            base_dir=self.sandbox_dir,
            confirm_fn=lambda _d, _det: True,
        )

        edit_res = tool_edit_file(
            "code.py",
            target="return x * 2",
            replacement="return x * 10",
            base_dir=self.sandbox_dir,
            confirm_fn=lambda _d, _det: True,
        )
        self.assertIn("editado exitosamente", edit_res)

        content = tool_read_file("code.py", base_dir=self.sandbox_dir)
        self.assertIn("return x * 10", content)
        self.assertNotIn("return x * 2", content)

    def test_sandbox_list_dir_and_search_code(self):
        sub = self.sandbox_dir / "modules"
        sub.mkdir()
        tool_write_file("modules/helper.py", "def magic_fn(): pass", base_dir=self.sandbox_dir, confirm_fn=lambda _d, _det: True)

        list_res = tool_list_dir(".", max_depth=2, base_dir=self.sandbox_dir)
        self.assertIn("modules/", list_res)
        self.assertIn("helper.py", list_res)

        search_res = tool_search_code("magic_fn", path=".", base_dir=self.sandbox_dir)
        self.assertIn("helper.py:1: def magic_fn(): pass", search_res)

    def test_sandbox_run_command_safe(self):
        cmd_res = tool_run_command("echo sandbox_ok", cwd=self.sandbox_dir, confirm_fn=lambda _d, _det: True)
        self.assertIn("sandbox_ok", cmd_res)

    # ---------------------------------------------------------
    # 2. Guardrails de Seguridad: Bloqueo de .env y Path Traversal
    # ---------------------------------------------------------

    def test_sandbox_blocks_reading_and_writing_env(self):
        env_names = [".env", ".env.local", ".env.production", "sub/.env"]
        for env_path in env_names:
            with self.subTest(env_path=env_path):
                # Lectura bloqueada
                read_res = execute_tool("read_file", {"path": env_path}, base_dir=self.sandbox_dir)
                self.assertIn("Violación de seguridad", read_res)
                self.assertIn("confidencial", read_res)

                # Escritura bloqueada
                write_res = execute_tool(
                    "write_file",
                    {"path": env_path, "content": "SECRET=123"},
                    base_dir=self.sandbox_dir,
                    confirm_fn=lambda _d, _det: True,
                )
                self.assertIn("Violación de seguridad", write_res)
                self.assertFalse((self.sandbox_dir / env_path).exists())

    def test_sandbox_blocks_path_traversal(self):
        traversal_attempts = [
            "../secret.txt",
            "../../escape.txt",
            "..\\..\\system.ini",
        ]
        for trav in traversal_attempts:
            with self.subTest(trav=trav):
                res = execute_tool("read_file", {"path": trav}, base_dir=self.sandbox_dir)
                self.assertIn("Violación de seguridad", res)
                self.assertIn("Path Traversal", res)

    def test_sandbox_user_cancellation(self):
        # El usuario responde 'n'
        cancel_res = execute_tool(
            "write_file",
            {"path": "never_created.txt", "content": "data"},
            base_dir=self.sandbox_dir,
            confirm_fn=lambda _d, _det: False,
        )
        self.assertIn("Acción cancelada", cancel_res)
        self.assertFalse((self.sandbox_dir / "never_created.txt").exists())

    # ---------------------------------------------------------
    # 3. Límites y Resiliencia ante Errores
    # ---------------------------------------------------------

    def test_sandbox_truncation_limit(self):
        large_content = "X" * 6000
        truncated = truncate_output(large_content, max_chars=4000)
        self.assertLessEqual(len(truncated), 4200)
        self.assertIn("Salida truncada", truncated)


if __name__ == "__main__":
    unittest.main()
