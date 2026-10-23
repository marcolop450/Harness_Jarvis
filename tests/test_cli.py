import io
import unittest
from pathlib import Path
from unittest.mock import patch

from main import handle_slash_command, main, parse_args, print_banner


class TestCLI(unittest.TestCase):
    def test_parse_args_defaults(self):
        args = parse_args([])
        self.assertIsNone(args.provider)
        self.assertIsNone(args.model)
        self.assertIsNone(args.prompt)
        self.assertIn("Harness Jarvis", args.system)

    def test_banner_output_includes_workspace(self):
        buf = io.StringIO()
        cwd = Path("D:/Harness Jarvis")
        with patch("sys.stdout", buf):
            print_banner("groq", "llama-3.3", cwd, has_key=True)
        output = buf.getvalue()
        self.assertIn("GROQ", output)
        self.assertIn("llama-3.3", output)
        self.assertIn("Espacio", output)
        self.assertIn("CONFIGURADA", output)

    def test_banner_unconfigured_state(self):
        buf = io.StringIO()
        cwd = Path("D:/Harness Jarvis")
        with patch("sys.stdout", buf):
            print_banner(None, None, cwd, has_key=False)
        output = buf.getvalue()
        self.assertIn("[SIN CONFIGURAR]", output)
        self.assertIn("Pendiente", output)

    def test_unconfigured_prompt_shows_guidance(self):
        buf = io.StringIO()
        with patch("main.load_model_memory", return_value={"active_provider": None, "active_model": None}):
            with patch("builtins.input", side_effect=["hola", "exit"]):
                with patch("sys.stdout", buf):
                    ret = main([])
        self.assertEqual(ret, 0)
        output = buf.getvalue()
        self.assertIn("[SIN CONFIGURAR]", output)
        self.assertIn("No tienes ningún proveedor ni modelo configurado todavía", output)

    def test_handle_slash_command_cwd(self):
        buf = io.StringIO()
        cwd = Path("D:/Harness Jarvis")
        with patch("sys.stdout", buf):
            prov, model, handled = handle_slash_command("/cwd", "gemini", "gemini-2.5-flash", cwd)
        self.assertTrue(handled)
        self.assertEqual(prov, "gemini")
        self.assertIn("D:\\Harness Jarvis", buf.getvalue())

    def test_handle_slash_command_model_change(self):
        buf = io.StringIO()
        cwd = Path("D:/Harness Jarvis")
        with patch("sys.stdout", buf):
            prov, model, handled = handle_slash_command("/model groq llama-3.3", "gemini", "gemini-2.5-flash", cwd)
        self.assertTrue(handled)
        self.assertEqual(prov, "groq")
        self.assertEqual(model, "llama-3.3")
        self.assertIn("GROQ -> llama-3.3", buf.getvalue())

    def test_handle_slash_command_clear(self):
        buf = io.StringIO()
        cwd = Path("D:/Harness Jarvis")
        with patch("os.system") as mock_sys, patch("sys.stdout", buf):
            prov, model, handled = handle_slash_command("/clear", "groq", "llama-3.3", cwd)
        self.assertTrue(handled)
        self.assertEqual(prov, "groq")
        self.assertEqual(model, "llama-3.3")
        mock_sys.assert_called_once()
        self.assertIn("Harness Jarvis CLI", buf.getvalue())

    def test_handle_slash_command_reset(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            session_file = tmp_path / ".harness_session.json"
            session_file.write_text('[{"role": "user", "content": "hola"}]', encoding="utf-8")

            conv_history = [{"role": "user", "content": "hola"}]
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                prov, model, handled = handle_slash_command(
                    "/reset", "groq", "llama-3.3", tmp_path, conversation_history=conv_history
                )
            self.assertTrue(handled)
            self.assertEqual(len(conv_history), 0)
            self.assertFalse(session_file.exists())
            self.assertIn("Memoria de conversación reiniciada", buf.getvalue())

    def test_handle_slash_command_model_add_list_select_rm(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 1. /model en catálogo vacío
            buf1 = io.StringIO()
            with patch("sys.stdout", buf1):
                p, m, h = handle_slash_command("/model", None, None, tmp_path)
            self.assertTrue(h)
            self.assertIn("Catálogo vacío", buf1.getvalue())

            # 2. /model add groq llama-3.3-70b-versatile
            buf2 = io.StringIO()
            with patch("sys.stdout", buf2):
                p, m, h = handle_slash_command("/model add groq llama-3.3-70b-versatile", None, None, tmp_path)
            self.assertTrue(h)
            self.assertEqual(p, "groq")
            self.assertEqual(m, "llama-3.3-70b-versatile")
            self.assertIn("Modelo agregado y activado", buf2.getvalue())

            # Agregar segundo modelo sin activar
            handle_slash_command("/model add ollama qwen2.5-coder:7b", p, m, tmp_path)

            # 3. /model lista numerada
            buf3 = io.StringIO()
            with patch("sys.stdout", buf3):
                p, m, h = handle_slash_command("/model", p, m, tmp_path)
            self.assertTrue(h)
            self.assertIn("[1]", buf3.getvalue())
            self.assertIn("[2]", buf3.getvalue())

            # 4. /model 2 seleccionar por número
            buf4 = io.StringIO()
            with patch("sys.stdout", buf4):
                p, m, h = handle_slash_command("/model 2", p, m, tmp_path)
            self.assertTrue(h)
            self.assertEqual(p, "ollama")
            self.assertEqual(m, "qwen2.5-coder:7b")
            self.assertIn("Modelo activo cambiado a", buf4.getvalue())

            # 5. /model rm 1 eliminar
            buf5 = io.StringIO()
            with patch("sys.stdout", buf5):
                p, m, h = handle_slash_command("/model rm 1", p, m, tmp_path)
            self.assertTrue(h)
            self.assertIn("eliminado del catálogo", buf5.getvalue())

    def test_repl_dynamic_prompt_contextual(self):
        buf = io.StringIO()
        prompts_seen = []

        def mock_input(prompt):
            prompts_seen.append(prompt)
            return "exit"

        with patch("main.load_model_memory", return_value={"active_provider": "groq", "active_model": "llama-3.3"}):
            with patch("builtins.input", side_effect=mock_input):
                with patch("sys.stdout", buf):
                    ret = main([])
        self.assertEqual(ret, 0)
        self.assertTrue(any("⚡ groq:llama-3.3" in p for p in prompts_seen))

    def test_handle_slash_command_guide_and_help(self):
        for cmd in ("/guide", "/guia", "/help", "/ayuda"):
            buf = io.StringIO()
            cwd = Path("D:/Harness Jarvis")
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command(cmd, None, None, cwd)
            self.assertTrue(handled)
            self.assertIsNone(p)
            self.assertIsNone(m)
            out = buf.getvalue()
            self.assertIn("GUIA RAPIDA DE INICIO", out)
            self.assertIn("/key", out)
            self.assertIn("/model", out)
            self.assertIn("Ollama", out)

    def test_repl_graceful_exit_without_api_keys(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["exit"]):
            with patch("sys.stdout", buf):
                ret = main([])
        self.assertEqual(ret, 0)
        self.assertIn("¡Hasta luego!", buf.getvalue())

    def test_handle_slash_command_sessions_and_resume(self):
        import tempfile
        from harness.model_config import list_saved_sessions, load_session_by_id, save_session_record

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Caso 1: /sessions vacío
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command("/sessions", "groq", "llama-3.3", tmp_path)
            self.assertTrue(handled)
            self.assertIn("No hay sesiones anteriores registradas", buf.getvalue())

            # Guardar dos sesiones de prueba
            save_session_record(
                "session_alpha",
                "gemini",
                "gemini-2.5-flash",
                [{"role": "user", "content": "hola 1"}, {"role": "assistant", "content": "res 1"}],
                base_dir=tmp_path,
            )
            save_session_record(
                "session_beta",
                "groq",
                "llama-3.3",
                [{"role": "user", "content": "hola 2"}],
                base_dir=tmp_path,
            )

            # Caso 2: /sessions con registros
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command("/sessions", "groq", "llama-3.3", tmp_path)
            self.assertTrue(handled)
            out = buf.getvalue()
            self.assertIn("session_alpha", out)
            self.assertIn("session_beta", out)
            self.assertIn("HISTORIAL DE SESIONES", out)

            # Caso 3: /resume sin argumentos
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command("/resume", "groq", "llama-3.3", tmp_path)
            self.assertTrue(handled)
            self.assertIn("[Uso]: /resume <id_de_sesion>", buf.getvalue())

            # Caso 4: /resume con id inexistente
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command("/resume non_existent", "groq", "llama-3.3", tmp_path)
            self.assertTrue(handled)
            self.assertIn("No se encontró la sesión", buf.getvalue())

            # Caso 5: /resume exitoso restaurando historial y modelo
            history = []
            state = {"id": "initial_session"}
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                new_p, new_m, handled = handle_slash_command(
                    "/resume session_alpha",
                    "groq",
                    "llama-3.3",
                    tmp_path,
                    conversation_history=history,
                    session_state=state,
                )
            self.assertTrue(handled)
            self.assertEqual(new_p, "gemini")
            self.assertEqual(new_m, "gemini-2.5-flash")
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["content"], "hola 1")
            self.assertEqual(state["id"], "session_alpha")
            self.assertIn("reanudada con éxito", buf.getvalue())

    def test_handle_slash_command_compact(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Caso 1: historial vacío o menor a 2 mensajes
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                p, m, handled = handle_slash_command(
                    "/compact", "groq", "llama-3.3", tmp_path, conversation_history=[]
                )
            self.assertTrue(handled)
            self.assertIn("demasiado breve", buf.getvalue())

            # Caso 2: historial suficiente
            history = [
                {"role": "user", "content": "tarea 1"},
                {"role": "assistant", "content": "completada 1"},
                {"role": "user", "content": "tarea 2"},
            ]
            buf = io.StringIO()
            with patch(
                "main.compact_conversation_history",
                return_value=([{"role": "system", "content": "resumen"}], "resumen"),
            ):
                with patch("sys.stdout", buf):
                    p, m, handled = handle_slash_command(
                        "/compact", "groq", "llama-3.3", tmp_path, conversation_history=history
                    )
            self.assertTrue(handled)
            self.assertIn("Historial compactado exitosamente", buf.getvalue())
            self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
