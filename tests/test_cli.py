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

    def test_repl_graceful_exit_without_api_keys(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["exit"]):
            with patch("sys.stdout", buf):
                ret = main([])
        self.assertEqual(ret, 0)
        self.assertIn("¡Hasta luego!", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
