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
from datetime import datetime
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from harness.agent_loop import MAX_STEPS, compact_conversation_history, run_agent_loop
from harness.guardrails import clear_turn_approvals
from harness.llm_provider import SUPPORTED_PROVIDERS, format_clean_api_error, resolve_provider
from harness.model_config import (
    add_user_model,
    build_workspace_system_prompt,
    clear_session_history,
    get_available_models_catalog,
    list_saved_sessions,
    load_model_memory,
    load_session_by_id,
    load_session_history,
    remove_user_model,
    resolve_model_selection,
    save_api_key_to_env,
    save_model_selection,
    save_session_history,
    save_session_record,
)

DEFAULT_BASE_PROMPT: str = (
    "Eres Harness Jarvis, un asistente de programación y operaciones en terminal "
    "tipo Claude Code. Responde de forma precisa, concisa y profesional."
)


def has_valid_key_for_provider(provider: str | None) -> bool:
    """Verifica si el entorno cuenta con una clave configurada para el proveedor."""
    if not provider:
        return False
    prov = provider.lower()
    if prov == "ollama":
        return True
    info = SUPPORTED_PROVIDERS.get(prov)
    if not info:
        return False
    return bool(os.getenv(info["env_key"]))


def get_prompt_symbol() -> str:
    """Retorna un símbolo para el prompt que no cause errores de codificación en Windows."""
    try:
        "⚡".encode(sys.stdout.encoding or "utf-8")
        return "⚡"
    except Exception:
        return "*"


def print_user_guide() -> None:
    """Imprime una guía visual completa para nuevos usuarios (operativa sin conexión ni IA)."""
    guide = """
+------------------------------------------------------------------------+
|             GUIA RAPIDA DE INICIO - HARNESS JARVIS CLI                 |
+------------------------------------------------------------------------+
  ¡Bienvenido! Jarvis es tu agente CLI de programacion autonomo.
  Opera en el directorio donde abras la terminal y puede crear archivos,
  editar codigo y ejecutar comandos bajo tu supervision.

1. CONFIGURAR PROVEEDOR Y CLAVE DE API (Primer uso):
   - Con API Key (Groq gratuito, Gemini, OpenAI, OpenRouter):
     /key groq <tu_api_key_gsk>
     /key gemini <tu_api_key_ai>
     (Tu clave se inyecta en memoria y se guarda en tu .env local).

   - O 100% Local y Gratuito sin Internet (con Ollama):
     Descarga Ollama (https://ollama.com) y ejecuta: ollama pull qwen2.5-coder:7b
     Luego en Jarvis:
     /model add ollama qwen2.5-coder:7b

2. ADMINISTRAR TUS MODELOS:
   - Ver tu catalogo numerado:   /model
   - Agregar un modelo propio:   /model add <proveedor> <modelo>
                                 (ej. /model add groq qwen/qwen3.8-27b)
   - Cambiar de modelo activo:   /model <numero> (ej. /model 1)
   - Eliminar un modelo:         /model rm <numero> (ej. /model 2)

3. COMO PEDIRLE TAREAS AL AGENTE:
   - Solo escribe lo que necesitas en lenguaje natural:
     * "Crea un script python test.py que calcule factoriales"
     * "Explica el contenido de main.py"
     * "Busca en el proyecto donde se define la funcion X"

4. SEGURIDAD Y CONFIRMACION [s/n]:
   - Para proteger tu entorno, antes de crear/editar archivos o correr
     comandos, Jarvis se detendra y te pedira autorizacion interactiva:
     ¿Desea autorizar esta operacion? [s/n]: s
   - Escribe 's', 'si', 'sí', 'ss' o 'yes' para autorizar, o 'n' para cancelar.

5. COMANDOS UTILES DE SESION:
   - /guide o /help  : Vuelve a mostrar esta guia en cualquier momento.
   - /clear          : Limpia la pantalla de la terminal.
   - /reset          : Reinicia la memoria de chat de la carpeta de trabajo.
   - /cwd            : Muestra la carpeta de trabajo actual.
   - exit o quit     : Cierra la sesion de Jarvis de forma ordenada.
+------------------------------------------------------------------------+
"""
    print(guide.strip())


def print_banner(
    provider_name: str | None,
    model_name: str | None,
    cwd: Path,
    has_key: bool,
) -> None:
    """Imprime el encabezado visual del agente en la terminal."""
    if not provider_name or not model_name:
        prov_str = "[SIN CONFIGURAR]"
        model_str = "[SIN CONFIGURAR]"
        status_str = "Pendiente (Usa /key o /guide para empezar)"
    else:
        prov_str = provider_name.upper()
        model_str = model_name
        status_str = "CONFIGURADA" if has_key else "NO DETECTADA (Usa /key o /model add/ollama)"

    banner = f"""
==============================================================
  Harness Jarvis CLI - Multi-API Agent
  Espacio   : {cwd}
  Proveedor : {prov_str}
  Modelo    : {model_str}
  Estado API: {status_str}
  Limite    : MAX_STEPS={MAX_STEPS} por consulta
  Comandos  : /model | /key | /compact | /sessions | /resume | /guide | /clear | /reset | exit
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
    current_provider: str | None,
    current_model: str | None,
    cwd: Path,
    conversation_history: list[dict[str, Any]] | None = None,
    session_state: dict[str, Any] | None = None,
) -> tuple[str | None, str | None, bool]:
    """Procesa comandos de barra oblicua (/model, /key, /cwd, /clear, /reset, /sessions, /resume).

    Retorna (nuevo_proveedor, nuevo_modelo, handled).
    """
    parts = command_line.strip().split()
    if not parts:
        return current_provider, current_model, False
    cmd = parts[0].lower()

    if cmd in ("/cwd", "/workspace"):
        print(f"\n[+] Directorio de trabajo activo: {cwd}")
        return current_provider, current_model, True

    if cmd in ("/guide", "/guia", "/help", "/ayuda"):
        print_user_guide()
        return current_provider, current_model, True

    if cmd == "/clear":
        os.system("cls" if os.name == "nt" else "clear")
        has_key = has_valid_key_for_provider(current_provider) if current_provider else False
        print_banner(current_provider, current_model, cwd, has_key)
        return current_provider, current_model, True

    if cmd == "/reset":
        if conversation_history is not None:
            conversation_history.clear()
        clear_session_history(cwd)
        print("\n+--------------------------------------------------------+")
        print("| [+] Memoria de conversación reiniciada para la carpeta |")
        print("+--------------------------------------------------------+")
        return current_provider, current_model, True

    if cmd in ("/compact", "/compactar"):
        if conversation_history is None or len([m for m in conversation_history if m.get("role") != "system"]) < 2:
            print("\n[Compactar]: El historial es demasiado breve (menos de 2 mensajes) para requerir compactación.")
            return current_provider, current_model, True

        if not current_provider or not current_model:
            print("\n[Error]: Debes tener un modelo configurado para compactar el historial.")
            return current_provider, current_model, True

        print("\n[*] Compactando historial de conversación con el LLM activo...", flush=True)
        old_char_count = sum(len(str(m.get("content", ""))) for m in conversation_history)
        new_history, summary = compact_conversation_history(
            conversation_history,
            provider_name=current_provider,
            model=current_model,
        )
        conversation_history.clear()
        conversation_history.extend(new_history)
        save_session_history(conversation_history, base_dir=cwd)
        new_char_count = sum(len(str(m.get("content", ""))) for m in conversation_history)
        reduction = max(0, int((1 - (new_char_count / max(old_char_count, 1))) * 100))

        print("\n+--------------------------------------------------------+")
        print("| [+] Historial compactado exitosamente!                 |")
        print(f"|     Caracteres previos : {old_char_count}".ljust(57) + "|")
        print(f"|     Caracteres actuales: {new_char_count}".ljust(57) + "|")
        print(f"|     Reducción estimada : ~{reduction}% de tokens".ljust(57) + "|")
        print("+--------------------------------------------------------+")
        print(f"\n[Resumen conservado en contexto]:\n{summary}")
        return current_provider, current_model, True

    if cmd in ("/sessions", "/sesiones"):
        sessions = list_saved_sessions(cwd)
        if not sessions:
            print("\n[Sesiones]: No hay sesiones anteriores registradas en este espacio de trabajo.")
        else:
            print("\n+----------------------------------------------------------------------------------+")
            print("| HISTORIAL DE SESIONES GUARDADAS EN ESTE ESPACIO                                  |")
            print("+----------------------------------------------------------------------------------+")
            print("| ID de Sesion                  | Fecha y Hora        | Modelo             | Msgs  |")
            print("+-------------------------------+---------------------+--------------------+-------+")
            for s in sessions:
                sid = (s["session_id"][:29]).ljust(29)
                dt = (s.get("created_at") or "")[:19].ljust(19)
                m_info = f"{s.get('provider') or '?'}:{s.get('model') or '?'}"[:18].ljust(18)
                cnt = str(s.get("message_count", 0)).rjust(5)
                print(f"| {sid} | {dt} | {m_info} | {cnt} |")
            print("+----------------------------------------------------------------------------------+")
            print("| Usa: /resume <id_de_sesion> para continuar cualquiera de estas sesiones.          |")
            print("+----------------------------------------------------------------------------------+")
        return current_provider, current_model, True

    if cmd in ("/resume", "/reanudar"):
        if len(parts) < 2:
            print("\n[Uso]: /resume <id_de_sesion>")
            print("  Ejemplo: /resume session_20261022_223015")
            print("  Consulta las sesiones disponibles con: /sessions")
            return current_provider, current_model, True

        target_id = parts[1]
        session_data = load_session_by_id(target_id, cwd)
        if not session_data:
            print(f"\n[Error]: No se encontró la sesión '{target_id}'. Consulta las disponibles con /sessions.")
            return current_provider, current_model, True

        restored_msgs = session_data.get("messages", [])
        if conversation_history is not None:
            conversation_history.clear()
            conversation_history.extend(restored_msgs)
        save_session_history(restored_msgs, base_dir=cwd)

        if session_state is not None:
            session_state["id"] = session_data.get("session_id", target_id)

        restored_prov = session_data.get("provider")
        restored_mod = session_data.get("model")
        if restored_prov and restored_mod:
            current_provider = restored_prov
            current_model = restored_mod

        print("\n+--------------------------------------------------------+")
        print(f"| [+] Sesión '{target_id}' reanudada con éxito!           |")
        print(f"|     Mensajes cargados : {len(restored_msgs)}".ljust(57) + "|")
        if current_provider and current_model:
            print(f"|     Modelo restaurado : {current_provider.upper()} ({current_model})".ljust(57) + "|")
        print("+--------------------------------------------------------+")
        return current_provider, current_model, True

    if cmd == "/model":
        config_path = cwd / ".harness_models.json"

        # Subcomando: /model o /model list -> mostrar catálogo numerado
        if len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == "list"):
            catalog = get_available_models_catalog(config_path)
            prov_disp = current_provider.upper() if current_provider else "[SIN CONFIGURAR]"
            mod_disp = current_model if current_model else "[SIN CONFIGURAR]"

            print("\n+--------------------------------------------------------+")
            print(f"| Modelo activo: {prov_disp} -> {mod_disp}".ljust(57) + "|")
            print("+--------------------------------------------------------+")

            if not catalog:
                print("| (Catálogo vacío: no tienes modelos registrados)       |")
                print("| Para agregar uno usa: /model add <proveedor> <modelo>  |")
                print("+--------------------------------------------------------+")
            else:
                print("| Modelos registrados:                                   |")
                for item in catalog:
                    has_k = has_valid_key_for_provider(item["provider"])
                    k_str = "[OK Clave]" if has_k else "[Sin clave]"
                    if item["provider"] == "ollama":
                        k_str = "[OK Local]"
                    act_str = " *Activo" if item["active"] else ""
                    line_str = f"  [{item['index']}] {item['provider'].upper()}: {item['model']} {k_str}{act_str}"
                    print(f"| {line_str}".ljust(57) + "|")
                print("+--------------------------------------------------------+")
                print("| Uso: /model <numero> | /model add <prov> <modelo>      |")
                print("|      /model rm <numero>                                |")
                print("+--------------------------------------------------------+")
            return current_provider, current_model, True

        # Subcomando: /model add <prov> <modelo>
        if parts[1].lower() == "add":
            if len(parts) < 4:
                print("\n[Uso]: /model add <proveedor> <nombre_modelo>")
                print(f"Proveedores soportados: {', '.join(SUPPORTED_PROVIDERS.keys())}")
                return current_provider, current_model, True
            prov = parts[2].lower()
            mod = parts[3]
            if prov not in SUPPORTED_PROVIDERS:
                print(f"\n[Error]: Proveedor '{prov}' no soportado. Opciones: {', '.join(SUPPORTED_PROVIDERS.keys())}")
                return current_provider, current_model, True
            add_user_model(prov, mod, config_path, set_active=True)
            print("\n+--------------------------------------------------------+")
            print(f"| [+] Modelo agregado y activado:                        |")
            print(f"|     {prov.upper()} -> {mod}".ljust(57) + "|")
            print("+--------------------------------------------------------+")
            return prov, mod, True

        # Subcomando: /model rm <target>
        if parts[1].lower() in ("rm", "del", "remove", "delete"):
            if len(parts) < 3:
                print("\n[Uso]: /model rm <numero_de_indice_o_nombre>")
                return current_provider, current_model, True
            target = parts[2]
            ok, msg = remove_user_model(target, config_path)
            if ok:
                print(f"\n[+] {msg}")
                mem = load_model_memory(config_path)
                return mem.get("active_provider"), mem.get("active_model"), True
            else:
                print(f"\n[Error]: {msg}")
                return current_provider, current_model, True

        # Subcomando: /model <numero>
        if len(parts) == 2 and parts[1].isdigit():
            idx = int(parts[1])
            res = resolve_model_selection(idx, config_path)
            if not res:
                print(f"\n[Error]: No existe el modelo número [{idx}] en el catálogo.")
                return current_provider, current_model, True
            new_prov, new_model = res
            save_model_selection(new_prov, new_model, config_path)
            has_k = has_valid_key_for_provider(new_prov)
            auth_str = "Autenticado y listo" if has_k else "Requiere clave con /key"
            if new_prov == "ollama":
                auth_str = "Local (Ollama)"
            print("\n+--------------------------------------------------------+")
            print(f"| [+] Modelo activo cambiado a:                          |")
            print(f"|     {new_prov.upper()} -> {new_model}".ljust(57) + "|")
            print(f"|     Estado: {auth_str}".ljust(57) + "|")
            print("+--------------------------------------------------------+")
            return new_prov, new_model, True

        # Subcomando clásico: /model <prov> <modelo>
        if len(parts) >= 3 and parts[1].lower() not in ("add", "rm", "del", "remove"):
            new_prov = parts[1].lower()
            new_model = parts[2]
            if new_prov not in SUPPORTED_PROVIDERS:
                print(f"\n[Error]: Proveedor '{new_prov}' no soportado. Opciones: {', '.join(SUPPORTED_PROVIDERS.keys())}")
                return current_provider, current_model, True

            save_model_selection(new_prov, new_model, config_path)
            print(f"\n[+] Modelo actualizado y recordado: {new_prov.upper()} -> {new_model}")
            return new_prov, new_model, True

        # Subcomando: /model <nombre_o_proveedor:nombre>
        if len(parts) == 2:
            res = resolve_model_selection(parts[1], config_path)
            if res:
                new_prov, new_model = res
                save_model_selection(new_prov, new_model, config_path)
                print(f"\n[+] Modelo actualizado y recordado: {new_prov.upper()} -> {new_model}")
                return new_prov, new_model, True

        print("\nUso: /model  |  /model <numero>  |  /model add <prov> <mod>  |  /model rm <numero>")
        return current_provider, current_model, True

    if cmd == "/key":
        if len(parts) >= 3:
            target_prov = parts[1].lower()
            key_val = parts[2]
            if target_prov not in SUPPORTED_PROVIDERS:
                print(f"\n[Error]: Proveedor '{target_prov}' no soportado. Opciones: {', '.join(SUPPORTED_PROVIDERS.keys())}")
                return current_provider, current_model, True
            save_api_key_to_env(target_prov, key_val, env_path=cwd / ".env")
            load_dotenv(cwd / ".env", override=True)
            print("\n+--------------------------------------------------------+")
            print(f"| [+] Clave para {target_prov.upper()} activada en memoria y guardada. |")
            print("+--------------------------------------------------------+")

            if not current_provider:
                config_path = cwd / ".harness_models.json"
                catalog = get_available_models_catalog(config_path)
                found = next((m for m in catalog if m["provider"] == target_prov), None)
                if found:
                    current_provider = target_prov
                    current_model = found["model"]
                else:
                    current_provider = target_prov
                    current_model = SUPPORTED_PROVIDERS[target_prov]["default_model"]
                    add_user_model(current_provider, current_model, config_path=config_path, set_active=True)
                print(f"[+] Proveedor configurado automáticamente a: {current_provider.upper()} ({current_model})")

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

    # Cargar memoria persistente de modelos sin asumir proveedor por defecto
    memory = load_model_memory(working_dir / ".harness_models.json")
    raw_provider = provider_name or memory.get("active_provider")
    active_provider = raw_provider.lower() if raw_provider else None

    raw_model = model or memory.get("active_model")
    active_model = raw_model if raw_model else None

    if active_provider and not active_model:
        info = SUPPORTED_PROVIDERS.get(active_provider)
        if info:
            active_model = info["default_model"]

    has_key = has_valid_key_for_provider(active_provider) if active_provider else False
    print_banner(active_provider, active_model, working_dir, has_key)

    # Cargar historial de conversación de la carpeta de trabajo
    conversation_history: list[dict[str, Any]] = load_session_history(working_dir)
    if conversation_history:
        print(f"[*] Historial de sesión cargado ({len(conversation_history)} mensajes previos en esta carpeta).")

    session_state: dict[str, Any] = {
        "id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

    def on_step(current: int, total: int) -> None:
        if current > 1:
            print(f"  [*] [Paso {current}/{total}] Razonando...", flush=True)

    folder_name = working_dir.name or str(working_dir)
    sym = get_prompt_symbol()

    while True:
        try:
            if active_provider and active_model:
                prompt_symbol = f"\n[{folder_name} | {sym} {active_provider}:{active_model}] jarvis> "
            else:
                prompt_symbol = f"\n[{folder_name} | {sym} [sin configurar]] jarvis> "
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
                user_input,
                active_provider,
                active_model,
                working_dir,
                conversation_history,
                session_state=session_state,
            )
            if handled:
                continue

        # Validar si no hay ningún proveedor configurado
        if not active_provider or not active_model:
            print(
                "\n[Aviso]: No tienes ningún proveedor ni modelo configurado todavía.\n"
                "  - Consulta la guía de inicio con: /guide\n"
                "  - Si tienes una clave API:        /key <proveedor> <tu_clave>\n"
                "  - O agrega tu modelo con:         /model add <proveedor> <nombre_modelo>\n"
                "  - O si usas Ollama local:         /model add ollama qwen2.5-coder:7b"
            )
            continue

        # Validar si el proveedor requiere API key y si está ausente
        if not has_valid_key_for_provider(active_provider):
            print(
                f"\n[Aviso]: No se ha detectado una clave de API para el proveedor '{active_provider.upper()}'.\n"
                f"  - Configura tu clave en la terminal con: /key {active_provider} <tu_clave>\n"
                f"  - O agrega un modelo local Ollama con:  /model add ollama qwen2.5-coder:7b"
            )
            continue

        # Enriquecer system prompt con el espacio de trabajo
        full_system_prompt = build_workspace_system_prompt(system_prompt, base_dir=working_dir)
        clear_turn_approvals()

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
            save_session_history(conversation_history, base_dir=working_dir)
            save_session_record(
                session_state["id"],
                active_provider,
                active_model,
                conversation_history,
                base_dir=working_dir,
            )
            print(f"\n{reply}")
        except Exception as exc:
            err_msg = str(exc)
            if not err_msg.startswith("[Error"):
                err_msg = format_clean_api_error(exc)
            print(f"\n{err_msg}", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Función principal de ejecución."""
    load_dotenv(Path.cwd() / ".env")
    load_dotenv()
    args = parse_args(argv)

    if args.prompt:
        try:
            memory = load_model_memory()
            target_provider = args.provider or memory.get("active_provider")
            if not target_provider:
                print(
                    "[Error]: No hay ningún proveedor configurado. Ejecuta 'jarvis' e ingresa /key o /model.",
                    file=sys.stderr,
                )
                return 1
            config = resolve_provider(target_provider)
            target_model = args.model or memory.get("active_model") or config.default_model
            full_system = build_workspace_system_prompt(args.system)
            reply, _ = run_agent_loop(
                prompt=args.prompt,
                system_prompt=full_system,
                provider_name=config.name,
                model=target_model,
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
