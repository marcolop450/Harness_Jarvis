"""Pruebas unitarias para el modo Arquitecto (Plan Mode) en harness/agent_loop.py."""

from pathlib import Path
from typing import Any
import pytest

from harness.agent_loop import run_agent_loop
from harness.llm_provider import NormalizedResponse, NormalizedToolCall
from harness.session_state import get_session_runtime


def test_plan_mode_blocks_write_and_edit_tools(tmp_path: Path):
    executed_tools = []

    def mock_executor(name: str, args: dict[str, Any]) -> str:
        executed_tools.append(name)
        return "OK"

    turn_step = 0

    def mock_llm_caller(**kwargs) -> NormalizedResponse:
        nonlocal turn_step
        turn_step += 1
        if turn_step == 1:
            return NormalizedResponse(
                content="Voy a intentar escribir un archivo",
                tool_calls=[
                    NormalizedToolCall(
                        id="call_write",
                        name="write_file",
                        arguments={"path": "solucion.py", "content": "print('hola')"},
                    )
                ],
            )
        elif turn_step == 2:
            messages = kwargs.get("messages", [])
            last_msg = messages[-1]
            assert last_msg["role"] == "tool"
            assert "El modo Arquitecto (/plan) está activo" in last_msg["content"]
            assert "write_file" in last_msg["content"]
            return NormalizedResponse(
                content="Entendido. Mi plan propuesto es: Crear arquitectura en solucion.py sin escribirla directamente.",
                tool_calls=[],
            )
        return NormalizedResponse(content="Fin", tool_calls=[])

    reply, history = run_agent_loop(
        prompt="Genera la solución en solucion.py",
        llm_caller=mock_llm_caller,
        tool_executor=mock_executor,
        base_dir=tmp_path,
        plan_mode=True,
    )

    # write_file NO debe haber sido ejecutado por el executor real
    assert "write_file" not in executed_tools
    assert not (tmp_path / "solucion.py").exists()
    assert "Mi plan propuesto" in reply


def test_plan_mode_allows_read_tools(tmp_path: Path):
    test_file = tmp_path / "readme.txt"
    test_file.write_text("contenido seguro", encoding="utf-8")

    executed_tools = []

    def mock_executor(name: str, args: dict[str, Any]) -> str:
        executed_tools.append(name)
        if name == "read_file":
            return test_file.read_text(encoding="utf-8")
        return "OK"

    turn_step = 0

    def mock_llm_caller(**kwargs) -> NormalizedResponse:
        nonlocal turn_step
        turn_step += 1
        if turn_step == 1:
            return NormalizedResponse(
                content="Leyendo archivo...",
                tool_calls=[
                    NormalizedToolCall(
                        id="call_read",
                        name="read_file",
                        arguments={"path": "readme.txt"},
                    )
                ],
            )
        return NormalizedResponse(content="Leído con éxito: contenido seguro", tool_calls=[])

    reply, history = run_agent_loop(
        prompt="Lee readme.txt",
        llm_caller=mock_llm_caller,
        tool_executor=mock_executor,
        base_dir=tmp_path,
        plan_mode=True,
    )

    assert "read_file" in executed_tools
    assert "contenido seguro" in reply


def test_plan_mode_inherited_from_session_runtime(tmp_path: Path):
    runtime = get_session_runtime()
    runtime.set_mode("PLAN")

    executed_tools = []

    def mock_executor(name: str, args: dict[str, Any]) -> str:
        executed_tools.append(name)
        return "OK"

    try:
        def mock_llm_caller(**kwargs) -> NormalizedResponse:
            return NormalizedResponse(
                content="Plan generado",
                tool_calls=[
                    NormalizedToolCall(
                        id="call_edit",
                        name="edit_file",
                        arguments={"path": "foo.py", "old_str": "a", "new_str": "b"},
                    )
                ],
            )

        reply, history = run_agent_loop(
            prompt="Edita",
            llm_caller=mock_llm_caller,
            tool_executor=mock_executor,
            base_dir=tmp_path,
            max_steps=1,
        )

        assert "edit_file" not in executed_tools
        tool_entry = next(m for m in history if m.get("role") == "tool")
        assert "El modo Arquitecto (/plan) está activo" in tool_entry["content"]
    finally:
        runtime.reset()
