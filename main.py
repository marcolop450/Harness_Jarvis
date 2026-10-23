"""Punto de entrada interactivo para el Agente CLI Harness Jarvis.

Soporta:
- Detección del directorio de trabajo activo (cwd) en banner y prompt.
- Memoria persistente de modelos (.harness_models.json).
- Tolerancia a entorno vacío sin API keys (no se cierra).
- Comandos /model, /key, /cwd, exit/quit.
- Inyección de contexto de trabajo y AGENT.md.
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from harness.agent_loop import MAX_STEPS, run_agent_loop
from harness.llm_provider import SUPPORTED_PROVIDERS, resolve_provider
from harness.model_config import (
    build_workspace_system_prompt,
    load_model_memory,
    save_api_key_to_env,
    save_model_selection,
)

DEFAULT_BASE_PROMPT: str = (
    "Eres Harness Jarvis, un asistente de programación y operaciones en terminal "
    "tipo Claude Code. Responde de forma precisa, concisa y profesional."
)


def has_valid_key_for_provider(provider: str) -> bool:
    """Verifica si el entorno cuenta con una clave configurada para el proveedor."""
    prov = provider.lower()
    if prov == "ollama":
        return True
    info = SUPPORTED_PROVIDERS.get(prov)
    if not info:
        return False
    return bool(os.getenv(info["env_key"]))


def print_banner(
    provider_name: str,
    model_name: str,
    cwd: Path,
    has_key: bool,
) -> None:
    """Imprime el encabezado visual del agente en la terminal."""
    status_str = "CONFIGURADA" if has_key else "NO DETECTADA (Usa /key o /model ollama)"
    banner = f"""
==============================================================
  Harness Jarvis CLI - Multi-API Agent
  Espacio   : {cwd}
  Proveedor : {provider_name.upper()}
  Modelo    : {model_name}
  Estado API: {status_str}
  Limite    : MAX_STEPS={MAX_STEPS} por consulta
  Comandos  : /model [prov] [mod]  |  /key <prov> <clave>  |  exit
==============================================================
"""
    print(banner.strip())


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Harness Jarvis CLI: Agente autónomo con arquitectura Multi-API."
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Proveedor LLM a utilizar (openai, gemini, groq, openrouter, ollama).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Modelo específico a utilizar.",
    )
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default=None,
        help="Prompt inicial opcional para ejecución directa sin REPL.",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=DEFAULT_BASE_PROMPT,
        help="System prompt para el agente.",
    )
    return parser.parse_args(args)


def handle_slash_command(
    command_line: str,
    current_provider: str,
    current_model: str,
    cwd: Path,
) -> tuple[str, str, bool]:
    """Procesa comandos de barra oblicua (/model, /key, /cwd).

    Retorna (nuevo_proveedor, nuevo_modelo, handled).
    """
    parts = command_line.strip().split()
    cmd = parts[0].lower()

    if cmd == "/cwd" or cmd == "/workspace":
        print(f"\n[+] Directorio de trabajo activo: {cwd}")
        return current_provider, current_model, True

    if cmd == "/model":
        if len(parts) == 1:
            memory = load_model_memory()
            print(f"\n[+] Proveedor activo: {current_provider.upper()} | Modelo: {current_model}")
            print("[+] Modelos guardados en memoria:")
            for prov, models in memory.get("saved_models", {}).items():
                active_mark = " (activo)" if prov == current_provider else ""
                print(f"    - {prov.upper()}{active_mark}: {', '.join(models)}")
            print("\nPara cambiar de modelo usa: /model <proveedor> <nombre_modelo>")
            return current_provider, current_model, True

        elif len(parts) >= 3:
            new_prov = parts[1].lower()
            new_model = parts[2]
            if new_prov not in SUPPORTED_PROVIDERS:
                print(f"\n[Error]: Proveedor '{new_prov}' no soportado. Opciones: {', '.join(SUPPORTED_PROVIDERS.keys())}")
                return current_provider, current_model, True

            save_model_selection(new_prov, new_model)
            print(f"\n[+] Modelo actualizado y recordado: {new_prov.upper()} -> {new_model}")
            return new_prov, new_model, True
        else:
            print("\nUso: /model o /model <proveedor> <nombre_modelo>")
            return current_provider, current_model, True

    if cmd == "/key":
        if len(parts) >= 3:
            target_prov = parts[1].lower()
            key_val = parts[2]
            if target_prov not in SUPPORTED_PROVIDERS:
                print(f"\n[Error]: Proveedor '{target_prov}' no soportado.")
                return current_provider, current_model, True
            save_api_key_to_env(target_prov, key_val)
            load_dotenv(override=True)
            print(f"\n[+] Clave para {target_prov.upper()} guardada exitosamente en .env.")
            return current_provider, current_model, True
        else:
            print("\nUso: /key <proveedor> <tu_clave_de_api>")
            return current_provider, current_model, True

    return current_provider, current_model, False


def run_repl(
    provider_name: str | None = None,
    model: str | None = None,
    system_prompt: str = DEFAULT_BASE_PROMPT,
    cwd: Path | None = None,
) -> int:
    """Inicia el bucle REPL interactivo con tolerancia a entorno sin API."""
    load_dotenv()
    working_dir = (cwd or Path.cwd()).resolve()

    # Cargar memoria persistente de modelos
    memory = load_model_memory()
    active_provider = (provider_name or memory.get("active_provider") or "gemini").lower()
    active_model = model or memory.get("active_model") or SUPPORTED_PROVIDERS[active_provider]["default_model"]

    has_key = has_valid_key_for_provider(active_provider)
    print_banner(active_provider, active_model, working_dir, has_key)

    conversation_history: list[dict[str, Any]] = []

    def on_step(current: int, total: int) -> None:
        if current > 1:
            print(f"  [*] [Paso {current}/{total}] Razonando...", flush=True)

    folder_name = working_dir.name or str(working_dir)

    while True:
        try:
            prompt_symbol = f"\n[{folder_name}] jarvis> "
            user_input = input(prompt_symbol).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada por el usuario.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("¡Hasta luego!")
            break

        # Manejo de comandos slash
        if user_input.startswith("/"):
            active_provider, active_model, handled = handle_slash_command(
                user_input, active_provider, active_model, working_dir
            )
            if handled:
                continue

        # Validar si el proveedor requiere API key y si está ausente
        if not has_valid_key_for_provider(active_provider):
            print(
                f"\n[Aviso]: No se ha detectado una clave de API para el proveedor '{active_provider.upper()}'.\n"
                f"  - Configura tu clave en la terminal con: /key {active_provider} <tu_clave>\n"
                f"  - O usa Ollama local (sin API) con:     /model ollama qwen2.5-coder:7b"
            )
            continue

        # Enriquecer system prompt con el espacio de trabajo
        full_system_prompt = build_workspace_system_prompt(system_prompt, base_dir=working_dir)

        try:
            reply, conversation_history = run_agent_loop(
                prompt=user_input,
                system_prompt=full_system_prompt,
                messages=conversation_history,
                provider_name=active_provider,
                model=active_model,
                base_dir=working_dir,
                on_step=on_step,
            )
            print(f"\n{reply}")
        except Exception as exc:
            print(f"\n[Error durante el turno]: {exc}", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Función principal de ejecución."""
    args = parse_args(argv)

    if args.prompt:
        try:
            config = resolve_provider(args.provider)
            full_system = build_workspace_system_prompt(args.system)
            reply, _ = run_agent_loop(
                prompt=args.prompt,
                system_prompt=full_system,
                provider_name=config.name,
                model=args.model or config.default_model,
            )
            print(reply)
            return 0
        except Exception as exc:
            print(f"[Error]: {exc}", file=sys.stderr)
            return 1

    return run_repl(
        provider_name=args.provider,
        model=args.model,
        system_prompt=args.system,
    )


if __name__ == "__main__":
    sys.exit(main())
