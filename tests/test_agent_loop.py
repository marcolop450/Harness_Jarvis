import tempfile
import unittest
from pathlib import Path
from typing import Any
from harness.agent_loop import MAX_STEPS, run_agent_loop
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

        self.assertEqual(reply, "Hola, ¿en qué te ayudo?")
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

        self.assertEqual(reply, "El clima está soleado.")
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

            self.assertEqual(reply, "Lectura completada exitosamente.")
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


if __name__ == "__main__":
    unittest.main()
