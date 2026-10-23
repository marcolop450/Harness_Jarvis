"""Bucle de control reactivo del Agente Harness.

Implementa el ciclo central while con límite inamovible MAX_STEPS = 15
y despacho seguro de las 6 herramientas operativas.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Callable
from harness.llm_provider import NormalizedResponse, NormalizedToolCall, call_llm
from harness.tools import execute_tool, get_tools_definitions

MAX_STEPS: int = 15
MAX_SUBAGENT_STEPS: int = 5

SUBAGENT_SYSTEM_PROMPT: str = (
    "Eres un Subagente Especializado de Investigación y Exploración. "
    "Tu objetivo es inspeccionar el código, leer archivos y analizar la estructura del proyecto "
    "para responder a la consulta solicitada con precisión técnica. "
    "Solo dispones de herramientas de solo lectura (read_file, list_dir, search_code). "
    "Al concluir tu investigación, emite un resumen estructurado y conciso con los hallazgos."
)


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
    include_timing: bool = True,
) -> tuple[str, list[dict[str, Any]]]:
    """Ejecuta el ciclo reactivo del agente acotado por MAX_STEPS = 15.

    Retorna una tupla (respuesta_final, historial_completo).
    """
    start_time = time.perf_counter()
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
            if include_timing:
                elapsed = time.perf_counter() - start_time
                time_badge = f"[⏱️ {elapsed:.2f}s]"
                final_content = f"{final_content}\n\n{time_badge}" if final_content else time_badge
            history.append({"role": "assistant", "content": final_content})
            return final_content, history

    # Se agotó el límite estricto de pasos
    elapsed = time.perf_counter() - start_time
    limit_message = f"Se alcanzó el límite estricto de {MAX_STEPS} pasos sin concluir la tarea."
    if include_timing:
        limit_message += f"\n\n[⏱️ {elapsed:.2f}s]"
    history.append({"role": "assistant", "content": limit_message})
    return limit_message, history


def run_subagent(
    task: str,
    base_dir: Path | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    llm_caller: Callable[..., NormalizedResponse] | None = None,
    tool_executor: Callable[[str, dict[str, Any]], str] | None = None,
) -> str:
    """Ejecuta un subagente de investigación aislado con contexto limpio (Figura 1 del PDF).

    Solo tiene acceso a herramientas de lectura y retorna exclusivamente un resumen final
    sin contaminar la ventana de contexto del agente principal.
    """
    caller = llm_caller or call_llm
    cwd = (base_dir or Path.cwd()).resolve()

    # Catálogo acotado estrictamente a solo lectura
    read_only_tools = [
        t for t in get_tools_definitions()
        if t.get("function", {}).get("name") in ("read_file", "list_dir", "search_code")
    ]

    if tool_executor is None:
        def default_subagent_executor(name: str, args: dict[str, Any]) -> str:
            if name not in ("read_file", "list_dir", "search_code"):
                return "Operación denegada: El subagente solo tiene permisos de lectura."
            return execute_tool(name, args, base_dir=cwd)
        active_executor = default_subagent_executor
    else:
        active_executor = tool_executor

    # Contexto limpio y aislado
    subagent_history: list[dict[str, Any]] = [
        {"role": "system", "content": SUBAGENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Tarea de investigación:\n{task}"},
    ]

    step = 0
    while step < MAX_SUBAGENT_STEPS:
        step += 1
        response: NormalizedResponse = caller(
            messages=subagent_history,
            tools=read_only_tools,
            provider_name=provider_name,
            model=model,
        )

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
            subagent_history.append(assistant_msg)

            for tc in response.tool_calls:
                res_text = active_executor(tc.name, tc.arguments)
                subagent_history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": res_text,
                })
        else:
            return response.content or "Subagente completó la investigación sin observaciones adicionales."

    return "Subagente alcanzó el límite de pasos de investigación."


def compact_conversation_history(
    messages: list[dict[str, Any]],
    provider_name: str | None = None,
    model: str | None = None,
    llm_caller: Callable[..., NormalizedResponse] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Condensa semánticamente el historial de conversación para liberar tokens de contexto.

    Retorna una tupla (nuevo_historial, resumen_generado).
    """
    system_msgs = [m for m in messages if m.get("role") == "system"]
    conversation_msgs = [m for m in messages if m.get("role") != "system"]

    if len(conversation_msgs) < 2:
        return messages, "El historial es demasiado breve para requerir compactación."

    caller = llm_caller or call_llm
    compact_prompt = (
        "Por favor, genera un resumen técnico conciso y estructurado de la conversación previa. "
        "Conserva los puntos esenciales: "
        "1) Tareas completadas y decisiones técnicas tomadas. "
        "2) Archivos creados, leídos o editados. "
        "3) Estado actual del trabajo. "
        "Sé directo y objetivo, descartando charlas accesorias."
    )

    request_messages = list(conversation_msgs) + [{"role": "user", "content": compact_prompt}]
    try:
        response = caller(
            messages=request_messages,
            provider_name=provider_name,
            model=model,
        )
        summary = response.content or "Resumen no disponible"
    except Exception as exc:
        summary = f"No se pudo generar el resumen automático debido a un error: {exc}"

    new_history: list[dict[str, Any]] = []
    if system_msgs:
        new_history.extend(system_msgs)

    new_history.append({
        "role": "user",
        "content": "[Contexto anterior compactado por solicitud del usuario]",
    })
    new_history.append({
        "role": "assistant",
        "content": f"Resumen del contexto técnico anterior:\n{summary}",
    })

    return new_history, summary
