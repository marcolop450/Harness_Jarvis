import tempfile
import unittest
from pathlib import Path
from typing import Any
from harness.agent_loop import (
    MAX_STEPS,
    apply_observation_masking,
    build_environment_context,
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


class TestKernelIntelligenceAndMemory(unittest.TestCase):
    def test_build_environment_context_includes_all_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            (base / "JARVIS.md").write_text("Regla 1: Ser conciso.\nRegla 2: Seguir tests.", encoding="utf-8")
            (base / "main.py").write_text("print('test')", encoding="utf-8")

            context = build_environment_context(base)
            self.assertIn("=== CONTEXTO DEL ENTORNO DE EJECUCIÓN ===", context)
            self.assertIn("Sistema Operativo:", context)
            self.assertIn("Directorio de Trabajo (CWD):", context)
            self.assertIn("Git:", context)
            self.assertIn("Estructura del Proyecto:", context)
            self.assertIn("main.py", context)
            self.assertIn("Reglas del Proyecto (JARVIS.md):", context)
            self.assertIn("Regla 1: Ser conciso.", context)

    def test_observation_masking_ephemeral_preservation(self):
        # Crear historial con 7 observaciones de herramientas
        history = [{"role": "system", "content": "Prompt"}]
        for i in range(1, 8):
            history.append({
                "role": "assistant",
                "content": f"Llamando herramienta {i}",
                "tool_calls": [{"id": f"tc_{i}", "type": "function", "function": {"name": "read_file", "arguments": "{}"}}]
            })
            history.append({
                "role": "tool",
                "tool_call_id": f"tc_{i}",
                "content": f"Salida muy extensa paso {i}: " + ("x" * 200),
            })

        masked = apply_observation_masking(history, keep_recent_steps=5)

        # 1. Longitudes idénticas
        self.assertEqual(len(masked), len(history))

        # 2. Las 2 primeras observaciones (tc_1 y tc_2) deben estar enmascaradas
        tool_msgs_masked = [m for m in masked if m.get("role") == "tool"]
        self.assertEqual(len(tool_msgs_masked), 7)
        self.assertIn("enmascarado para optimizar", tool_msgs_masked[0]["content"])
        self.assertEqual(tool_msgs_masked[0]["tool_call_id"], "tc_1")
        self.assertIn("enmascarado para optimizar", tool_msgs_masked[1]["content"])
        self.assertEqual(tool_msgs_masked[1]["tool_call_id"], "tc_2")

        # 3. Las últimas 5 observaciones (tc_3 a tc_7) deben estar intactas
        for i in range(2, 7):
            self.assertIn("Salida muy extensa paso", tool_msgs_masked[i]["content"])
            self.assertEqual(tool_msgs_masked[i]["tool_call_id"], f"tc_{i+1}")

        # 4. El historial original NO debe haber sido mutado
        tool_msgs_orig = [m for m in history if m.get("role") == "tool"]
        self.assertIn("Salida muy extensa paso 1", tool_msgs_orig[0]["content"])
        self.assertNotIn("enmascarado", tool_msgs_orig[0]["content"])

    def test_self_healing_error_recovery_loop(self):
        call_step = 0

        def self_healing_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            nonlocal call_step
            call_step += 1
            if call_step == 1:
                # El modelo emite un tool call con JSON malformado (detectado por llm_provider)
                tc = NormalizedToolCall(
                    id="call_broken",
                    name="edit_file",
                    arguments={"raw_arguments": "{broken: json", "parse_error": "JSON malformado no recuperable"},
                )
                return NormalizedResponse(content="Intentando editar archivo", tool_calls=[tc])
            elif call_step == 2:
                # El modelo inspecciona el error en role: tool y se autocorrige
                last_msg = messages[-1]
                self.assertEqual(last_msg["role"], "tool")
                self.assertIn("Error de formato en herramienta 'edit_file'", last_msg["content"])
                return NormalizedResponse(content="Me he autocorregido y completado la tarea.", tool_calls=[])
            return NormalizedResponse(content="Fin", tool_calls=[])

        reply, history = run_agent_loop(
            prompt="Corrige el archivo",
            llm_caller=self_healing_caller,
            system_prompt="Eres Jarvis",
        )

        self.assertIn("Me he autocorregido", reply)
        self.assertEqual(call_step, 2)
        # Verificar que el error se inyectó en el historial sin abortar el bucle
        tool_entry = next(m for m in history if m["role"] == "tool")
        self.assertEqual(tool_entry["tool_call_id"], "call_broken")
        self.assertIn("Error de formato", tool_entry["content"])

    def test_dynamic_max_steps_explicit(self):
        steps_called = 0

        def endless_tool_caller(**kwargs):
            nonlocal steps_called
            steps_called += 1
            return NormalizedResponse(
                content="Pensando...",
                tool_calls=[
                    NormalizedToolCall(id=f"call_{steps_called}", name="list_dir", arguments={"path": "."})
                ],
            )

        reply, history = run_agent_loop(
            prompt="Bucle infinito",
            llm_caller=endless_tool_caller,
            tool_executor=lambda name, args: "[]",
            max_steps=4,
        )

        self.assertEqual(steps_called, 4)
        self.assertIn("Se alcanzó el límite estricto de 4 pasos", reply)

    def test_dynamic_max_steps_from_session_runtime(self):
        from harness.session_state import get_session_runtime

        runtime = get_session_runtime()
        runtime.set_max_steps(3)
        try:
            steps_called = 0

            def endless_tool_caller(**kwargs):
                nonlocal steps_called
                steps_called += 1
                return NormalizedResponse(
                    content="Pensando...",
                    tool_calls=[
                        NormalizedToolCall(id=f"call_{steps_called}", name="list_dir", arguments={"path": "."})
                    ],
                )

            reply, history = run_agent_loop(
                prompt="Bucle infinito",
                llm_caller=endless_tool_caller,
                tool_executor=lambda name, args: "[]",
            )

            self.assertEqual(steps_called, 3)
            self.assertIn("Se alcanzó el límite estricto de 3 pasos", reply)
        finally:
            runtime.reset()

    def test_cancelled_tool_action_injects_grounded_warning(self):
        call_step = 0

        def cancelling_caller(messages: list[dict[str, Any]], **kwargs) -> NormalizedResponse:
            nonlocal call_step
            call_step += 1
            if call_step == 1:
                tc = NormalizedToolCall(
                    id="call_cancel_1",
                    name="run_command",
                    arguments={"command": "mkdir test"},
                )
                return NormalizedResponse(content="Ejecutando comando", tool_calls=[tc])
            return NormalizedResponse(content="Entendido, no se realizaron cambios.", tool_calls=[])

        reply, history = run_agent_loop(
            prompt="Crea el directorio",
            llm_caller=cancelling_caller,
            tool_executor=lambda name, args: "Acción cancelada: El usuario denegó la ejecución del comando 'mkdir test'.",
            system_prompt="Eres Jarvis",
        )

        tool_entry = next(m for m in history if m["role"] == "tool")
        self.assertIn("ALERTA DE SEGURIDAD Y ESTADO REAL", tool_entry["content"])
        self.assertIn("Los cambios NO fueron aplicados", tool_entry["content"])


if __name__ == "__main__":
    unittest.main()
