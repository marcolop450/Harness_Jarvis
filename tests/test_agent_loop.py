import tempfile
import unittest
from pathlib import Path
from typing import Any
from harness.agent_loop import (
    MAX_STEPS,
    compact_conversation_history,
    run_agent_loop,
    run_subagent,
)
from harness.llm_provider import NormalizedResponse, NormalizedToolCall


class TestAgentLoop(unittest.TestCase):
    def test_direct_response_terminates_in_one_step(self):
        def mock_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            return NormalizedResponse(content="Hola, ¿en qué te ayudo?", tool_calls=[])

        steps_recorded: list[int] = []

        def on_step(current: int, total: int):
            steps_recorded.append(current)

        reply, history = run_agent_loop(
            prompt="Hola",
            system_prompt="Eres un asistente.",
            llm_caller=mock_caller,
            on_step=on_step,
        )

        self.assertIn("Hola, ¿en qué te ayudo?", reply)
        self.assertIn("[⏱️ ", reply)
        self.assertEqual(steps_recorded, [1])
        self.assertEqual(len(history), 3)  # system, user, assistant
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[2]["role"], "assistant")

    def test_multi_step_tool_execution_then_response(self):
        calls_count = 0

        def mock_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            nonlocal calls_count
            calls_count += 1
            if calls_count == 1:
                tc = NormalizedToolCall(id="call_1", name="search_info", arguments={"q": "clima"})
                return NormalizedResponse(content=None, tool_calls=[tc])
            return NormalizedResponse(content="El clima está soleado.", tool_calls=[])

        def mock_executor(name: str, args: dict[str, Any]) -> str:
            return "25 grados soleado"

        reply, history = run_agent_loop(
            prompt="¿Qué clima hace?",
            tool_executor=mock_executor,
            llm_caller=mock_caller,
        )

        self.assertIn("El clima está soleado.", reply)
        self.assertIn("[⏱️ ", reply)
        self.assertEqual(calls_count, 2)
        roles = [m["role"] for m in history]
        self.assertEqual(roles, ["user", "assistant", "tool", "assistant"])

    def test_real_tools_integration_via_agent_loop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            (base / "doc.txt").write_text("contenido del documento", encoding="utf-8")

            call_seq = 0
            def mock_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
                nonlocal call_seq
                call_seq += 1
                if call_seq == 1:
                    tc = NormalizedToolCall(id="c1", name="read_file", arguments={"path": "doc.txt"})
                    return NormalizedResponse(content=None, tool_calls=[tc])
                return NormalizedResponse(content="Lectura completada exitosamente.", tool_calls=[])

            reply, history = run_agent_loop(
                prompt="Lee doc.txt",
                base_dir=base,
                llm_caller=mock_caller,
            )

            self.assertIn("Lectura completada exitosamente.", reply)
            self.assertIn("[⏱️ ", reply)
            tool_msg = next(m for m in history if m["role"] == "tool")
            self.assertEqual(tool_msg["content"], "contenido del documento")

    def test_strict_limit_max_steps_15(self):
        calls_count = 0

        def endless_tool_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            nonlocal calls_count
            calls_count += 1
            tc = NormalizedToolCall(id=f"call_{calls_count}", name="loop_tool", arguments={})
            return NormalizedResponse(content=None, tool_calls=[tc])

        steps_called: list[int] = []

        def on_step(current: int, total: int):
            steps_called.append(current)

        reply, history = run_agent_loop(
            prompt="Empieza tarea infinita",
            llm_caller=endless_tool_caller,
            on_step=on_step,
        )

        self.assertEqual(calls_count, MAX_STEPS)
        self.assertEqual(len(steps_called), MAX_STEPS)
        self.assertEqual(steps_called[-1], 15)
        self.assertIn(f"Se alcanzó el límite estricto de {MAX_STEPS} pasos", reply)


class TestCompactConversationHistory(unittest.TestCase):
    def test_compact_skips_when_history_too_short(self):
        msgs = [{"role": "user", "content": "hola"}]
        new_msgs, summary = compact_conversation_history(msgs)
        self.assertEqual(msgs, new_msgs)
        self.assertIn("demasiado breve", summary)

    def test_compact_summarizes_and_reduces_history(self):
        msgs = [
            {"role": "system", "content": "Eres Jarvis."},
            {"role": "user", "content": "Crea el archivo prime.py con calculo de primos"},
            {"role": "assistant", "content": "He creado el archivo prime.py con la funcion es_primo."},
            {"role": "user", "content": "Ahora crea tests/test_prime.py"},
            {"role": "assistant", "content": "He creado tests/test_prime.py con 5 tests unitarios."},
        ]

        def mock_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            return NormalizedResponse(
                content="Se creó prime.py con cálculo de primos y tests/test_prime.py con 5 pruebas pasando.",
                tool_calls=[],
            )

        new_history, summary = compact_conversation_history(
            messages=msgs,
            provider_name="groq",
            model="llama-3.3",
            llm_caller=mock_caller,
        )

        # Debe conservar el system prompt original
        self.assertEqual(new_history[0]["role"], "system")
        self.assertEqual(new_history[0]["content"], "Eres Jarvis.")

        # Debe haber reducido los 4 mensajes intermedios a un resumen consolidado
        self.assertEqual(len(new_history), 3)  # system, user marker, assistant summary
        self.assertIn("prime.py", summary)
        self.assertIn("test_prime.py", summary)
        self.assertIn("Contexto anterior compactado", new_history[1]["content"])
        self.assertIn(summary, new_history[2]["content"])


class TestSubagentExecution(unittest.TestCase):
    def test_subagent_clean_context_and_summary_return(self):
        passed_messages: list[list[dict[str, Any]]] = []

        def mock_caller(messages: list[dict[str, Any]], tools=None, **kwargs) -> NormalizedResponse:
            passed_messages.append(list(messages))
            if len(passed_messages) == 1:
                tc = NormalizedToolCall(id="c1", name="search_code", arguments={"query": "def run"})
                return NormalizedResponse(content=None, tool_calls=[tc])
            return NormalizedResponse(content="Hallazgo: Se encontró la función run en agent_loop.py", tool_calls=[])

        def mock_executor(name: str, args: dict[str, Any]) -> str:
            return "harness/agent_loop.py: def run_agent_loop"

        summary = run_subagent(
            task="Investiga dónde está definida la función run_agent_loop",
            llm_caller=mock_caller,
            tool_executor=mock_executor,
        )

        self.assertIn("Hallazgo: Se encontró la función run", summary)
        # Verificar que el contexto inicial del subagente estaba limpio (solo system prompt y task)
        self.assertEqual(len(passed_messages[0]), 2)
        self.assertEqual(passed_messages[0][0]["role"], "system")
        self.assertIn("Subagente Especializado", passed_messages[0][0]["content"])
        self.assertEqual(passed_messages[0][1]["role"], "user")
        self.assertIn("Tarea de investigación:", passed_messages[0][1]["content"])

    def test_subagent_rejects_write_operations(self):
        def mock_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            if len(messages) == 2:
                tc = NormalizedToolCall(id="c_bad", name="write_file", arguments={"path": "x.txt", "content": "bad"})
                return NormalizedResponse(content=None, tool_calls=[tc])
            return NormalizedResponse(content="Terminado", tool_calls=[])

        summary = run_subagent(
            task="Intenta escribir archivo",
            llm_caller=mock_caller,
        )
        self.assertIn("Terminado", summary)


if __name__ == "__main__":
    unittest.main()
