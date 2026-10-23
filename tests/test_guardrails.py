import unittest
from pathlib import Path
from harness.guardrails import (
    SecurityViolationError,
    clear_turn_approvals,
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

    def test_confirm_action_batch_authorization_with_a(self):
        clear_turn_approvals()
        prompts_count = 0

        def counting_input(prompt_text):
            nonlocal prompts_count
            prompts_count += 1
            return "a"

        # Primera llamada para 'test.py': responde 'a'
        res1 = confirm_action("Modificar archivo", details="Ruta: test.py", input_fn=counting_input)
        self.assertTrue(res1)
        self.assertEqual(prompts_count, 1)

        # Segunda llamada para el mismo 'test.py': no debe volver a preguntar
        res2 = confirm_action("Modificar archivo", details="Ruta: test.py", input_fn=counting_input)
        self.assertTrue(res2)
        self.assertEqual(prompts_count, 1, "No debió llamar a input_fn una segunda vez")

        # Tercera llamada para otro archivo distinto: debe preguntar
        res3 = confirm_action("Modificar archivo", details="Ruta: other.py", input_fn=lambda _: "s")
        self.assertTrue(res3)

        # Reiniciar aprobaciones por turno
        clear_turn_approvals()
        # Ahora para 'test.py' debe volver a preguntar
        res4 = confirm_action("Modificar archivo", details="Ruta: test.py", input_fn=counting_input)
        self.assertTrue(res4)
        self.assertEqual(prompts_count, 2)


if __name__ == "__main__":
    unittest.main()
