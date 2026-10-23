import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from harness.llm_provider import (
    NormalizedResponse,
    NormalizedToolCall,
    call_llm,
    format_clean_api_error,
    normalize_arguments,
    resolve_provider,
    SUPPORTED_PROVIDERS,
)


class TestLLMProviderDataClasses(unittest.TestCase):
    def test_normalized_tool_call_instantiation(self):
        call = NormalizedToolCall(
            id="call_123",
            name="read_file",
            arguments={"path": "test.txt"}
        )
        self.assertEqual(call.id, "call_123")
        self.assertEqual(call.name, "read_file")
        self.assertEqual(call.arguments, {"path": "test.txt"})

    def test_normalized_response_instantiation(self):
        call = NormalizedToolCall(
            id="call_abc",
            name="list_dir",
            arguments={"path": "."}
        )
        resp = NormalizedResponse(
            content="Hola mundo",
            tool_calls=[call],
            finish_reason="tool_calls"
        )
        self.assertEqual(resp.content, "Hola mundo")
        self.assertEqual(len(resp.tool_calls), 1)
        self.assertEqual(resp.tool_calls[0].name, "list_dir")
        self.assertEqual(resp.finish_reason, "tool_calls")


class TestResolveProvider(unittest.TestCase):
    def test_resolve_explicit_provider_with_key(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test123"}, clear=True):
            config = resolve_provider("groq")
            self.assertEqual(config.name, "groq")
            self.assertEqual(config.api_key, "gsk_test123")
            self.assertEqual(config.base_url, "https://api.groq.com/openai/v1")
            self.assertEqual(config.default_model, "llama-3.3-70b-versatile")

    def test_resolve_automatic_provider_from_env(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIza_test"}, clear=True):
            config = resolve_provider()
            self.assertEqual(config.name, "gemini")
            self.assertEqual(config.api_key, "AIza_test")
            self.assertEqual(config.base_url, "https://generativelanguage.googleapis.com/v1beta/openai/")

    def test_resolve_ollama_default(self):
        with patch.dict(os.environ, {}, clear=True):
            config = resolve_provider("ollama")
            self.assertEqual(config.name, "ollama")
            self.assertEqual(config.api_key, "ollama")
            self.assertEqual(config.base_url, "http://localhost:11434/v1")

    def test_resolve_missing_api_key_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                resolve_provider("openai")
            self.assertIn("Clave de API no configurada", str(ctx.exception))

    def test_resolve_unsupported_provider_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_provider("unsupported_ai")
        self.assertIn("Proveedor no soportado", str(ctx.exception))


class TestCallLLM(unittest.TestCase):
    def test_normalize_arguments_dict_and_json(self):
        self.assertEqual(normalize_arguments({"key": "val"}), {"key": "val"})
        self.assertEqual(normalize_arguments('{"count": 42}'), {"count": 42})
        self.assertEqual(normalize_arguments(""), {})
        res = normalize_arguments("invalid json")
        self.assertIn("raw_arguments", res)
        self.assertIn("parse_error", res)

    def test_call_llm_text_response(self):
        mock_client = MagicMock()
        mock_msg = SimpleNamespace(content="Hola desde LLM", tool_calls=None)
        mock_choice = SimpleNamespace(message=mock_msg, finish_reason="stop")
        mock_client.chat.completions.create.return_value = SimpleNamespace(choices=[mock_choice])

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-mock"}, clear=True):
            resp = call_llm(
                messages=[{"role": "user", "content": "Hola"}],
                provider_name="openai",
                client=mock_client,
            )
            self.assertEqual(resp.content, "Hola desde LLM")
            self.assertEqual(resp.tool_calls, [])
            self.assertEqual(resp.finish_reason, "stop")

    def test_call_llm_with_tool_calls(self):
        mock_client = MagicMock()
        mock_fn = SimpleNamespace(name="read_file", arguments='{"path": "harness/llm_provider.py"}')
        mock_tool_call = SimpleNamespace(id="call_999", function=mock_fn)
        mock_msg = SimpleNamespace(content=None, tool_calls=[mock_tool_call])
        mock_choice = SimpleNamespace(message=mock_msg, finish_reason="tool_calls")
        mock_client.chat.completions.create.return_value = SimpleNamespace(choices=[mock_choice])

        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIza-mock"}, clear=True):
            resp = call_llm(
                messages=[{"role": "user", "content": "Lee el archivo"}],
                tools=[{"type": "function", "function": {"name": "read_file"}}],
                provider_name="gemini",
                client=mock_client,
            )
            self.assertIsNone(resp.content)
            self.assertEqual(len(resp.tool_calls), 1)
            self.assertEqual(resp.tool_calls[0].id, "call_999")
            self.assertEqual(resp.tool_calls[0].name, "read_file")
            self.assertEqual(resp.tool_calls[0].arguments, {"path": "harness/llm_provider.py"})
            self.assertEqual(resp.finish_reason, "tool_calls")


class TestCleanApiErrorsAndTokens(unittest.TestCase):
    def test_format_clean_api_error_429(self):
        err = Exception("Error code: 429 - {'error': {'message': 'Rate limit reached'}}")
        msg = format_clean_api_error(err)
        self.assertIn("Error 429", msg)
        self.assertIn("Límite de tokens/cuota", msg)
        self.assertNotIn("{'error'", msg)

    def test_format_clean_api_error_401(self):
        err = Exception("Error code: 401 - {'error': {'message': 'Invalid API Key'}}")
        msg = format_clean_api_error(err)
        self.assertIn("Error 401", msg)
        self.assertIn("Clave de API inválida", msg)
        self.assertNotIn("{'error'", msg)

    def test_format_clean_api_error_404(self):
        err = Exception("Error code: 404 - {'error': {'message': 'The model does not exist'}}")
        msg = format_clean_api_error(err)
        self.assertIn("Error 404", msg)
        self.assertIn("Modelo no encontrado", msg)

    def test_format_clean_api_error_500(self):
        err = Exception("Error code: 500 - Internal Server Error")
        msg = format_clean_api_error(err)
        self.assertIn("Error 50", msg)
        self.assertIn("fuera de línea", msg)

    def test_call_llm_catches_api_error_and_raises_clean_message(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Error code: 429 - Rate limit exceeded")

        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                call_llm(
                    messages=[{"role": "user", "content": "Hola"}],
                    provider_name="groq",
                    client=mock_client,
                )
            self.assertIn("Error 429", str(ctx.exception))
            self.assertIn("Límite de tokens/cuota", str(ctx.exception))

    def test_call_llm_passes_max_tokens(self):
        mock_client = MagicMock()
        mock_msg = SimpleNamespace(content="Respuesta", tool_calls=None)
        mock_choice = SimpleNamespace(message=mock_msg, finish_reason="stop")
        mock_client.chat.completions.create.return_value = SimpleNamespace(choices=[mock_choice])

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            call_llm(
                messages=[{"role": "user", "content": "Hola"}],
                provider_name="openai",
                client=mock_client,
                max_tokens=1500,
            )
            _, kwargs = mock_client.chat.completions.create.call_args
            self.assertEqual(kwargs.get("max_tokens"), 1500)


if __name__ == "__main__":
    unittest.main()
