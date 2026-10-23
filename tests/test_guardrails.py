import unittest
from pathlib import Path
from harness.guardrails import (
    SecurityViolationError,
    confirm_action,
    is_sensitive_path,
    validate_safe_path,
)


class TestGuardrailsPathSecurity(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path("D:/Harness Jarvis").resolve()

    def test_safe_relative_path(self):
        safe = validate_safe_path("harness/tools.py", base_dir=self.base_dir)
        self.assertEqual(safe, (self.base_dir / "harness" / "tools.py").resolve())

    def test_blocks_env_files(self):
        env_files = [".env", ".env.local", ".env.production", "subdir/.env"]
        for env_file in env_files:
            with self.subTest(env_file=env_file):
                with self.assertRaises(SecurityViolationError) as ctx:
                    validate_safe_path(env_file, base_dir=self.base_dir)
                self.assertIn("confidencial", str(ctx.exception))

    def test_blocks_sensitive_keys(self):
        sensitive_files = [
            "id_rsa",
            "id_rsa.pub",
            "cert.pem",
            "private.key",
            ".harness_session.json",
            ".harness_models.json",
        ]
        for s_file in sensitive_files:
            with self.subTest(s_file=s_file):
                with self.assertRaises(SecurityViolationError) as ctx:
                    validate_safe_path(s_file, base_dir=self.base_dir)
                self.assertIn("confidencial", str(ctx.exception))

    def test_blocks_path_traversal_above_cwd(self):
        traversal_paths = [
            "../secret.txt",
            "../../etc/passwd",
            "..\\Windows\\System32\\cmd.exe",
        ]
        for t_path in traversal_paths:
            with self.subTest(t_path=t_path):
                with self.assertRaises(SecurityViolationError) as ctx:
                    validate_safe_path(t_path, base_dir=self.base_dir)
                self.assertIn("Path Traversal", str(ctx.exception))


class TestGuardrailsConfirmation(unittest.TestCase):
    def test_confirm_action_accepts(self):
        affirmatives = [
            "s", "S", "si", "SI", "sí", "SÍ", "ss", "SS", "y", "Y", "yes", "YES", "ok", "OK"
        ]
        for affirmative in affirmatives:
            with self.subTest(affirmative=affirmative):
                result = confirm_action("Crear archivo", input_fn=lambda _: affirmative)
                self.assertTrue(result)

    def test_confirm_action_rejects(self):
        for negative in ["n", "N", "no", "NO", "cancel", "", "denegar"]:
            with self.subTest(negative=negative):
                result = confirm_action("Ejecutar comando", input_fn=lambda _: negative)
                self.assertFalse(result)

    def test_confirm_action_prints_details_and_flushes(self):
        import io
        from unittest.mock import patch
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            confirm_action("Eliminar archivo", details="archivo.txt", input_fn=lambda _: "s")
        output = buf.getvalue()
        self.assertIn("[CONFIRMACION REQUERIDA]", output)
        self.assertIn("Eliminar archivo", output)
        self.assertIn("archivo.txt", output)


if __name__ == "__main__":
    unittest.main()
