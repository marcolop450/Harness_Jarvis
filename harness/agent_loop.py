"""Bucle de control reactivo del Agente Harness.

Implementa el ciclo central while con límite inamovible MAX_STEPS = 15
y despacho seguro de las 6 herramientas operativas.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Callable
from harness.llm_provider import NormalizedResponse, NormalizedToolCall, call_llm
from harness.tools import execute_tool, get_tools_definitions

MAX_STEPS: int = 15


def run_agent_loop(
    prompt: str,
    system_prompt: str | None = None,
    messages: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_executor: Callable[[str, dict[str, Any]], str] | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    llm_caller: Callable[..., NormalizedResponse] | None = None,
    on_step: Callable[[int, int], None] | None = None,
    base_dir: Path | None = None,
    confirm_fn: Callable[[str, str], bool] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Ejecuta el ciclo reactivo del agente acotado por MAX_STEPS = 15.

    Retorna una tupla (respuesta_final, historial_completo).
    """
    history: list[dict[str, Any]] = list(messages) if messages is not None else []

    if system_prompt and not any(m.get("role") == "system" for m in history):
        history.insert(0, {"role": "system", "content": system_prompt})

    history.append({"role": "user", "content": prompt})

    caller = llm_caller or call_llm
    active_tools = get_tools_definitions() if tools is None else tools

    if tool_executor is None:
        def default_executor(name: str, args: dict[str, Any]) -> str:
            return execute_tool(name, args, base_dir=base_dir, confirm_fn=confirm_fn)
        active_executor = default_executor
    else:
        active_executor = tool_executor

    step = 0

    while step < MAX_STEPS:
        step += 1

        if on_step:
            on_step(step, MAX_STEPS)

        response: NormalizedResponse = caller(
            messages=history,
            tools=active_tools,
            provider_name=provider_name,
            model=model,
        )

        # Si el modelo invocó herramientas
        if response.tool_calls:
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ],
            }
            history.append(assistant_msg)

            for tc in response.tool_calls:
                result_text = active_executor(tc.name, tc.arguments)

                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })
        else:
            # Respuesta final de texto sin tool calls
            final_content = response.content or ""
            history.append({"role": "assistant", "content": final_content})
            return final_content, history

    # Se agotó el límite estricto de pasos
    limit_message = f"Se alcanzó el límite estricto de {MAX_STEPS} pasos sin concluir la tarea."
    history.append({"role": "assistant", "content": limit_message})
    return limit_message, history
