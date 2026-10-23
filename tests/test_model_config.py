import tempfile
import unittest
from pathlib import Path
from harness.model_config import (
    add_user_model,
    build_workspace_system_prompt,
    clear_session_history,
    get_available_models_catalog,
    load_model_memory,
    load_session_history,
    remove_user_model,
    resolve_model_selection,
    save_api_key_to_env,
    save_model_selection,
    save_session_history,
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
        self.assertEqual(config["saved_models"], {}, "El catálogo inicial debe estar completamente limpio")
        self.assertTrue(self.config_path.exists())

    def test_save_and_reload_model_selection(self):
        save_model_selection("groq", "mi-modelo-custom:70b", self.config_path)
        reloaded = load_model_memory(self.config_path)
        self.assertEqual(reloaded["active_provider"], "groq")
        self.assertEqual(reloaded["active_model"], "mi-modelo-custom:70b")
        self.assertIn("mi-modelo-custom:70b", reloaded["saved_models"]["groq"])

    def test_catalog_add_remove_and_resolve(self):
        # Catálogo inicialmente vacío
        catalog_empty = get_available_models_catalog(self.config_path)
        self.assertEqual(len(catalog_empty), 0)

        # Agregar primer modelo
        add_user_model("groq", "llama-3.3-70b-versatile", self.config_path, set_active=True)
        # Agregar segundo modelo sin activar
        add_user_model("ollama", "qwen2.5-coder:7b", self.config_path, set_active=False)

        cat = get_available_models_catalog(self.config_path)
        self.assertEqual(len(cat), 2)
        self.assertEqual(cat[0]["index"], 1)
        self.assertEqual(cat[0]["provider"], "groq")
        self.assertEqual(cat[0]["model"], "llama-3.3-70b-versatile")
        self.assertTrue(cat[0]["active"])
        self.assertFalse(cat[1]["active"])

        # Resolver por índice
        res1 = resolve_model_selection(1, self.config_path)
        self.assertEqual(res1, ("groq", "llama-3.3-70b-versatile"))
        res2 = resolve_model_selection("2", self.config_path)
        self.assertEqual(res2, ("ollama", "qwen2.5-coder:7b"))

        # Resolver por formato 'provider:model'
        res_str = resolve_model_selection("groq:llama-3.3-70b-versatile", self.config_path)
        self.assertEqual(res_str, ("groq", "llama-3.3-70b-versatile"))

        # Eliminar modelo por índice
        ok, msg = remove_user_model(1, self.config_path)
        self.assertTrue(ok)
        self.assertIn("eliminado", msg)

        # Catálogo ahora tiene 1 modelo (el de ollama) y el modelo activo (que era el 1) quedó en None
        cat_after = get_available_models_catalog(self.config_path)
        self.assertEqual(len(cat_after), 1)
        self.assertEqual(cat_after[0]["provider"], "ollama")

        data = load_model_memory(self.config_path)
        self.assertIsNone(data["active_provider"])
        self.assertIsNone(data["active_model"])

        # Eliminar por nombre
        ok2, _ = remove_user_model("qwen2.5-coder:7b", self.config_path)
        self.assertTrue(ok2)
        self.assertEqual(len(get_available_models_catalog(self.config_path)), 0)

    def test_save_api_key_to_env(self):
        import os
        env_file = self.base / ".env"
        save_api_key_to_env("groq", "gsk_secret_123", env_path=env_file)
        content = env_file.read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=gsk_secret_123", content)
        # Verificación de inyección inmediata en memoria
        self.assertEqual(os.environ.get("GROQ_API_KEY"), "gsk_secret_123")

        # Actualización de clave existente
        save_api_key_to_env("groq", "gsk_secret_456", env_path=env_file)
        updated = env_file.read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=gsk_secret_456", updated)
        self.assertNotIn("gsk_secret_123", updated)
        self.assertEqual(os.environ.get("GROQ_API_KEY"), "gsk_secret_456")

    def test_build_workspace_system_prompt(self):
        agent_file = self.base / "AGENT.md"
        agent_file.write_text("Regla 1: Usar siempre TypeScript.", encoding="utf-8")

        prompt = build_workspace_system_prompt("Eres Jarvis.", base_dir=self.base)
        self.assertIn("Eres Jarvis.", prompt)
        self.assertIn("Regla 1: Usar siempre TypeScript.", prompt)
        self.assertIn(f"CWD): {self.base}", prompt)

    def test_session_history_persistence_and_clear(self):
        # Inicialmente vacío
        history = load_session_history(base_dir=self.base)
        self.assertEqual(history, [])

        messages = [
            {"role": "user", "content": "Hola Jarvis"},
            {"role": "assistant", "content": "Hola, ¿en qué te ayudo hoy?"},
        ]
        save_session_history(messages, base_dir=self.base)

        loaded = load_session_history(base_dir=self.base)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["content"], "Hola Jarvis")
        self.assertEqual(loaded[1]["role"], "assistant")

        # Limpiar sesión
        ok = clear_session_history(base_dir=self.base)
        self.assertTrue(ok)
        self.assertEqual(load_session_history(base_dir=self.base), [])


if __name__ == "__main__":
    unittest.main()
