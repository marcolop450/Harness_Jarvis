import tempfile
import unittest
from pathlib import Path
from harness.model_config import (
    build_workspace_system_prompt,
    load_model_memory,
    save_api_key_to_env,
    save_model_selection,
)


class TestModelConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name).resolve()
        self.config_path = self.base / ".harness_models.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_default_when_missing(self):
        config = load_model_memory(self.config_path)
        self.assertIn("active_provider", config)
        self.assertIsNone(config["active_provider"])
        self.assertIsNone(config["active_model"])
        self.assertIn("saved_models", config)
        self.assertTrue(self.config_path.exists())

    def test_save_and_reload_model_selection(self):
        save_model_selection("groq", "mi-modelo-custom:70b", self.config_path)
        reloaded = load_model_memory(self.config_path)
        self.assertEqual(reloaded["active_provider"], "groq")
        self.assertEqual(reloaded["active_model"], "mi-modelo-custom:70b")
        self.assertIn("mi-modelo-custom:70b", reloaded["saved_models"]["groq"])

    def test_save_api_key_to_env(self):
        env_file = self.base / ".env"
        save_api_key_to_env("groq", "gsk_secret_123", env_path=env_file)
        content = env_file.read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=gsk_secret_123", content)

        # Actualización de clave existente
        save_api_key_to_env("groq", "gsk_secret_456", env_path=env_file)
        updated = env_file.read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=gsk_secret_456", updated)
        self.assertNotIn("gsk_secret_123", updated)

    def test_build_workspace_system_prompt(self):
        agent_file = self.base / "AGENT.md"
        agent_file.write_text("Regla 1: Usar siempre TypeScript.", encoding="utf-8")

        prompt = build_workspace_system_prompt("Eres Jarvis.", base_dir=self.base)
        self.assertIn("Eres Jarvis.", prompt)
        self.assertIn("Regla 1: Usar siempre TypeScript.", prompt)
        self.assertIn(f"CWD): {self.base}", prompt)


if __name__ == "__main__":
    unittest.main()
