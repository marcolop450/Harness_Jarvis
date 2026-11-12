"""Bucle de control reactivo del Agente Harness.

Implementa el ciclo central while con límite inamovible MAX_STEPS = 15,
inyección proactiva de contexto ambiental, observation masking efímero
y auto-reparación ante fallos de herramientas.
"""

from __future__ import annotations
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Callable
from harness.llm_provider import NormalizedResponse, NormalizedToolCall, call_llm
from harness.session_state import get_session_runtime
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


def build_environment_context(base_dir: Path | None = None) -> str:
    """Construye un bloque de contexto ambiental estructurado para inyectar en el System Prompt."""
    cwd = (base_dir or Path.cwd()).resolve()
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    # 1. Información Git (rama y estado)
    git_info = "No es un repositorio Git o Git no está disponible"
    try:
        branch_proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if branch_proc.returncode == 0:
            branch = branch_proc.stdout.strip()
            status_proc = subprocess.run(
                ["git", "status", "--short"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=3,
            )
            dirty_lines = [l for l in status_proc.stdout.splitlines() if l.strip()]
            status_summary = f"{len(dirty_lines)} cambios pendientes" if dirty_lines else "limpio"
            git_info = f"Rama: {branch} ({status_summary})"
    except Exception:
        pass

    # 2. Árbol de archivos resumido
    ignore_dirs = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".harness_sessions"}
    tree_lines = []
    try:
        entries = sorted(list(cwd.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries[:25]:
            if entry.name in ignore_dirs:
                continue
            if entry.is_dir():
                tree_lines.append(f"  ├── {entry.name}/")
            else:
                tree_lines.append(f"  ├── {entry.name}")
        if len(entries) > 25:
            tree_lines.append(f"  └── ... ({len(entries) - 25} elementos más)")
    except Exception as exc:
        tree_lines.append(f"  [Error al listar directorio: {exc}]")

    tree_str = "\n".join(tree_lines) if tree_lines else "  (directorio vacío)"

    # 3. Reglas del proyecto si existe JARVIS.md o AGENT.md
    rules_block = ""
    for rule_file in ("JARVIS.md", "AGENT.md"):
        candidate = cwd / rule_file
        if candidate.exists() and candidate.is_file():
            try:
                rule_content = candidate.read_text(encoding="utf-8", errors="replace")
                if len(rule_content) > 2000:
                    rule_content = rule_content[:2000] + "\n[... Reglas truncadas a 2000 caracteres ...]"
                rules_block = f"\n\n## Reglas del Proyecto ({rule_file}):\n{rule_content}"
                break
            except Exception:
                pass

    context = (
        "=== CONTEXTO DEL ENTORNO DE EJECUCIÓN ===\n"
        f"- Sistema Operativo: {os_info}\n"
        f"- Directorio de Trabajo (CWD): {cwd}\n"
        f"- Git: {git_info}\n"
        "- Estructura del Proyecto:\n"
        f"{tree_str}"
        f"{rules_block}\n"
        "- Regla Fáctica Obligatoria: Solo reporta como creados o modificados los archivos cuya herramienta "
        "haya devuelto éxito en este turno. Si dudas de la existencia de un directorio, usa list_dir antes de responder.\n"
        "========================================="
    )
    return context


def apply_observation_masking(messages: list[dict[str, Any]], keep_recent_steps: int = 5) -> list[dict[str, Any]]:
    """Genera una copia efímera del historial enmascarando observaciones antiguas (> keep_recent_steps).

    Preserva intactos todos los role, tool_call_id y la estructura del mensaje.
    """
    ephemeral = [dict(m) for m in messages]
    tool_indices = [idx for idx, m in enumerate(ephemeral) if m.get("role") == "tool"]

    if len(tool_indices) > keep_recent_steps:
        mask_indices = set(tool_indices[:-keep_recent_steps])
        for idx in mask_indices:
            orig = ephemeral[idx]
            ephemeral[idx] = {
                **orig,
                "content": "[Contenido de herramienta anterior enmascarado para optimizar ventana de contexto RAM. Usa read_file o reejecuta si requieres refrescarlo.]",
            }

    return ephemeral


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
    session_approved_targets: set[str] | None = None,
    inject_environment: bool = True,
    max_steps: int | None = None,
    plan_mode: bool | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Ejecuta el ciclo reactivo del agente acotado por MAX_STEPS (configurable dinámicamente).

    Retorna una tupla (respuesta_final, historial_completo).
    """
    start_time = time.perf_counter()
    history: list[dict[str, Any]] = list(messages) if messages is not None else []
    runtime = get_session_runtime()
    effective_max_steps = max_steps if max_steps is not None else runtime.max_steps
    is_plan = plan_mode if plan_mode is not None else runtime.is_plan_mode()

    if system_prompt:
        if inject_environment:
            env_context = build_environment_context(base_dir)
            full_system_prompt = f"{system_prompt}\n\n{env_context}"
        else:
            full_system_prompt = system_prompt

        if is_plan:
            full_system_prompt += (
                "\n\n[MODO ARQUITECTO / PLAN ACTIVO]\n"
                "Operas en modo de solo lectura y diseño arquitectónico. Tienes estrictamente prohibido "
                "modificar o crear archivos en disco (write_file y edit_file están bloqueadas). "
                "Tu objetivo es analizar, inspeccionar y estructurar la solución técnica en tu respuesta."
            )

        if not any(m.get("role") == "system" for m in history):
            history.insert(0, {"role": "system", "content": full_system_prompt})
    elif is_plan:
        history.insert(0, {
            "role": "system",
            "content": (
                "[MODO ARQUITECTO / PLAN ACTIVO]\n"
                "Operas en modo de solo lectura y diseño arquitectónico. Tienes estrictamente prohibido "
                "modificar o crear archivos en disco (write_file y edit_file están bloqueadas)."
            ),
        })

    history.append({"role": "user", "content": prompt})

    caller = llm_caller or call_llm
    active_tools = get_tools_definitions() if tools is None else tools

    if tool_executor is None:
        def default_executor(name: str, args: dict[str, Any]) -> str:
            def local_confirmer(desc: str, details: str) -> bool:
                from harness.guardrails import confirm_action
                return confirm_action(desc, details, session_approved_targets=session_approved_targets)
            cf = confirm_fn or local_confirmer
            return execute_tool(name, args, base_dir=base_dir, confirm_fn=cf)
        active_executor = default_executor
    else:
        active_executor = tool_executor

    step = 0
    nudge_count = 0

    PROMISE_PATTERNS = (
        "ahora sí lo",
        "ahora si lo",
        "voy a modificar",
        "voy a editar",
        "voy a crear",
        "procedo a",
        "mejoro ese mismo archivo",
        "modifico ese mismo archivo",
        "enseguida lo",
        "ahora procedo",
        "paso a modificar",
        "procederé a",
    )

    try:
        while step < effective_max_steps:
            step += 1

            if on_step:
                on_step(step, effective_max_steps)

            # Preparar copia efímera con observation masking para el LLM
            ephemeral_history = apply_observation_masking(history, keep_recent_steps=5)

            try:
                from harness.ui import compact_spinner
                spinner_cm = compact_spinner("Jarvis está procesando tu solicitud...")
            except Exception:
                from contextlib import nullcontext
                spinner_cm = nullcontext()

            with spinner_cm:
                response: NormalizedResponse = caller(
                    messages=ephemeral_history,
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
                    # Bucle de auto-reparación (Self-Healing)
                    try:
                        if is_plan and tc.name in ("write_file", "edit_file"):
                            result_text = (
                                f"Operación bloqueada en herramienta '{tc.name}': El modo Arquitecto (/plan) está activo. "
                                "No se permiten modificaciones ni escrituras de archivos en disco. "
                                "Presenta tu análisis, plan o código dentro del cuerpo de tu respuesta de texto."
                            )
                        elif "parse_error" in tc.arguments:
                            result_text = (
                                f"Error de formato en herramienta '{tc.name}': Los argumentos JSON son inválidos. "
                                f"Detalle: {tc.arguments.get('parse_error')}. "
                                f"Argumentos recibidos: {tc.arguments.get('raw_arguments')}. "
                                "Por favor corrige la sintaxis JSON y vuelve a emitir la llamada."
                            )
                        else:
                            if tc.name in ("write_file", "edit_file") and "path" in tc.arguments:
                                target_p = (base_dir or Path.cwd()) / tc.arguments["path"]
                                if target_p.exists() and target_p.is_file():
                                    try:
                                        runtime.record_file_snapshot(
                                            target_p,
                                            target_p.read_text(encoding="utf-8", errors="replace"),
                                        )
                                    except Exception:
                                        pass
                            result_text = active_executor(tc.name, tc.arguments)
                    except Exception as exc:
                        result_text = f"Error al ejecutar herramienta '{tc.name}': {exc}"

                    if "Acción cancelada" in result_text or "Operación cancelada" in result_text or "denegó" in result_text:
                        grounded_warning = (
                            "[ALERTA DE SEGURIDAD Y ESTADO REAL]: La operación fue cancelada o rechazada por el usuario. "
                            "Los cambios NO fueron aplicados en el disco ni en la consola. "
                            "Tienes estrictamente prohibido afirmar que este paso fue completado con éxito. "
                            "Informa con honestidad al usuario que la acción no se ejecutó y espera sus instrucciones."
                        )
                        result_text = f"{grounded_warning}\n\n{result_text}"

                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    })
            else:
                # Respuesta final de texto sin tool calls
                final_content = response.content or ""

                # Salvaguarda Bias for Action:
                # Si el modelo emite una promesa conversacional evasiva sin invocar herramientas
                # y aún no se agotaron los pasos, inyectar un recordatorio para forzar la ejecución real.
                lower_content = final_content.lower()
                if (
                    not is_plan
                    and nudge_count < 1
                    and step < effective_max_steps
                    and len(final_content) < 300
                    and any(pattern in lower_content for pattern in PROMISE_PATTERNS)
                ):
                    nudge_count += 1
                    history.append({"role": "assistant", "content": final_content})
                    history.append({
                        "role": "user",
                        "content": (
                            "[DIRECTIVA DEL ARNÉS - BIAS FOR ACTION]: No anuncies ni prometas lo que vas a hacer. "
                            "Emite de inmediato la llamada a la herramienta ('write_file', 'edit_file', 'run_command') "
                            "para aplicar los cambios directamente en el sistema ahora mismo."
                        ),
                    })
                    continue

                if include_timing:
                    elapsed = time.perf_counter() - start_time
                    time_badge = f"[⏱️ {elapsed:.2f}s]"
                    final_content = f"{final_content}\n\n{time_badge}" if final_content else time_badge
                history.append({"role": "assistant", "content": final_content})
                return final_content, history

        # Se agotó el límite estricto de pasos
        elapsed = time.perf_counter() - start_time
        limit_message = f"Se alcanzó el límite estricto de {effective_max_steps} pasos sin concluir la tarea."
        if include_timing:
            limit_message += f"\n\n[⏱️ {elapsed:.2f}s]"
        history.append({"role": "assistant", "content": limit_message})
        return limit_message, history
    finally:
        from harness.guardrails import clear_turn_approvals
        clear_turn_approvals()


def run_subagent(
    task: str,
    base_dir: Path | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    llm_caller: Callable[..., NormalizedResponse] | None = None,
    tool_executor: Callable[[str, dict[str, Any]], str] | None = None,
) -> str:
    """Ejecuta un subagente de investigación aislado con contexto limpio.

    Solo tiene acceso a herramientas de lectura y retorna exclusivamente un resumen final
    sin contaminar la ventana de contexto del agente principal.
    """
    caller = llm_caller or call_llm
    cwd = (base_dir or Path.cwd()).resolve()

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
