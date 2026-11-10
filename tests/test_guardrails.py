import unittest
from pathlib import Path
from harness.guardrails import (
    ActionCancelledError,
    RISK_LEVEL_AUTO,
    RISK_LEVEL_WORKSPACE,
    RISK_LEVEL_DANGEROUS,
    SecurityViolationError,
    authorize_and_dispatch,
    classify_risk,
    clear_session_approvals,
    clear_turn_approvals,
    confirm_action,
    is_safe_command,
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


class TestSmartHITLGuardrails(unittest.TestCase):
    def test_risk_classification(self):
        # Nivel 0 (Lectura y consultas seguras)
        self.assertEqual(classify_risk("read_file", {"path": "a.txt"})[0], RISK_LEVEL_AUTO)
        self.assertEqual(classify_risk("list_dir", {"path": "."})[0], RISK_LEVEL_AUTO)
        self.assertEqual(classify_risk("search_code", {"pattern": "def"})[0], RISK_LEVEL_AUTO)
        self.assertEqual(classify_risk("git_status", {})[0], RISK_LEVEL_AUTO)
        self.assertEqual(classify_risk("sqlite_query", {"query": "SELECT * FROM users"})[0], RISK_LEVEL_AUTO)

        # Nivel 1 (Escritura en workspace)
        self.assertEqual(classify_risk("write_file", {"path": "a.txt"})[0], RISK_LEVEL_WORKSPACE)
        self.assertEqual(classify_risk("edit_file", {"path": "a.txt"})[0], RISK_LEVEL_WORKSPACE)
        self.assertEqual(classify_risk("sqlite_query", {"query": "INSERT INTO users VALUES(1)"})[0], RISK_LEVEL_WORKSPACE)

        # Nivel 2 (Comandos y Red)
        self.assertEqual(classify_risk("fetch", {"url": "https://example.com"})[0], RISK_LEVEL_DANGEROUS)
        self.assertEqual(classify_risk("run_command", {"command": "rm -rf /"})[0], RISK_LEVEL_DANGEROUS)
        # Comando en whitelist sin encadenamiento -> Auto
        self.assertEqual(classify_risk("run_command", {"command": "pytest tests/test_tools.py"})[0], RISK_LEVEL_AUTO)

    def test_safe_command_whitelist_and_chaining_rejection(self):
        # Comandos válidos en whitelist
        self.assertTrue(is_safe_command("pytest"))
        self.assertTrue(is_safe_command("pytest -v tests/"))
        self.assertTrue(is_safe_command("python -m unittest discover"))
        self.assertTrue(is_safe_command("git status"))
        self.assertTrue(is_safe_command("git diff --staged"))
        self.assertTrue(is_safe_command("git log -n 5"))
        self.assertTrue(is_safe_command("git branch -a"))
        self.assertTrue(is_safe_command("ruff check ."))
        self.assertTrue(is_safe_command("black --check harness/"))
        self.assertTrue(is_safe_command("mypy harness/"))

        # Inyecciones y encadenamientos que DEBEN ser rechazados
        self.assertFalse(is_safe_command("pytest && rm -rf ."))
        self.assertFalse(is_safe_command("pytest ; cat /etc/passwd"))
        self.assertFalse(is_safe_command("git status | grep modified"))
        self.assertFalse(is_safe_command("git diff || echo hacked"))
        self.assertFalse(is_safe_command("pytest `rm file`"))
        self.assertFalse(is_safe_command("pytest $(whoami)"))
        self.assertFalse(is_safe_command("git status > out.txt"))
        self.assertFalse(is_safe_command("pytest < input.txt"))
        self.assertFalse(is_safe_command("pytest\nrm -rf /"))

    def test_session_approval_memory_across_turns(self):
        clear_turn_approvals()
        session_approved = set()
        prompts = 0

        def ask_once(prompt):
            nonlocal prompts
            prompts += 1
            return "a"

        # Turno 1: el usuario autoriza con 'a'
        ok1 = authorize_and_dispatch("write_file", {"path": "module.py"}, session_approved_targets=session_approved, input_fn=ask_once)
        self.assertTrue(ok1)
        self.assertEqual(prompts, 1)
        self.assertIn("module.py", session_approved)

        # Se limpia el turno (simulando fin de turno en el bucle)
        clear_turn_approvals()

        # Turno 2: en la misma sesión, NO debe pedir confirmación nuevamente
        ok2 = authorize_and_dispatch("edit_file", {"path": "module.py"}, session_approved_targets=session_approved, input_fn=ask_once)
        self.assertTrue(ok2)
        self.assertEqual(prompts, 1, "No debió preguntar en el siguiente turno para el archivo autorizado en sesión")

        # Turno 2 pero para un archivo NO autorizado: debe preguntar
        ok3 = authorize_and_dispatch("edit_file", {"path": "other_file.py"}, session_approved_targets=session_approved, input_fn=lambda _: "s")
        self.assertTrue(ok3)

    def test_authorize_and_dispatch_action_cancelled(self):
        with self.assertRaises(ActionCancelledError):
            authorize_and_dispatch("run_command", {"command": "curl http://evil.com"}, input_fn=lambda _: "n")


if __name__ == "__main__":
    unittest.main()
