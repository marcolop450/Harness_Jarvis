"""Gestión de memoria persistente de modelos y configuración de sesión.

Permite:
- Guardar y restaurar el proveedor y modelo activo entre sesiones en '.harness_models.json'.
- Recordar modelos agregados dinámicamente por el usuario.
- Guardar claves de API en el archivo .env local de forma asistida.
- Construir el contexto del espacio de trabajo (cwd y AGENT.md) para el system prompt.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE: str = ".harness_models.json"
SESSION_HISTORY_FILE: str = ".harness_session.json"
SESSIONS_DIR_NAME: str = ".harness_sessions"

DEFAULT_MODELS: dict[str, list[str]] = {}


def get_global_harness_dir() -> Path:
    """Retorna la ruta al directorio de configuración global del usuario ~/.harness/."""
    return Path.home() / ".harness"


def get_default_config_path(base_dir: Path | None = None) -> Path:
    """Retorna la ruta hacia el archivo de configuración persistente con soporte en cascada."""
    if base_dir is not None:
        return (base_dir / DEFAULT_CONFIG_FILE).resolve()
    local_candidate = (Path.cwd() / DEFAULT_CONFIG_FILE).resolve()
    if local_candidate.exists():
        return local_candidate
    global_candidate = (get_global_harness_dir() / DEFAULT_CONFIG_FILE).resolve()
    if global_candidate.exists():
        return global_candidate
    return local_candidate


def get_session_history_path(base_dir: Path | None = None) -> Path:
    """Retorna la ruta hacia el archivo de historial de sesión del espacio de trabajo."""
    base = (base_dir or Path.cwd()).resolve()
    return base / SESSION_HISTORY_FILE


def load_session_history(base_dir: Path | None = None) -> list[dict[str, Any]]:
    """Carga el historial de mensajes de la sesión en el espacio de trabajo."""
    path = get_session_history_path(base_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [m for m in data if isinstance(m, dict) and "role" in m]
    except Exception:
        pass
    return []


def save_session_history(messages: list[dict[str, Any]], base_dir: Path | None = None) -> None:
    """Persiste el historial de mensajes en el archivo de sesión del espacio de trabajo."""
    path = get_session_history_path(base_dir)
    try:
        # Guardar lista limpia serializable
        clean_messages: list[dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg:
                item = {"role": msg["role"], "content": msg.get("content", "")}
                if "tool_calls" in msg and msg["tool_calls"]:
                    item["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg and msg["tool_call_id"]:
                    item["tool_call_id"] = msg["tool_call_id"]
                clean_messages.append(item)
        path.write_text(json.dumps(clean_messages, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def clear_session_history(base_dir: Path | None = None) -> bool:
    """Elimina el historial de mensajes de sesión del espacio de trabajo."""
    path = get_session_history_path(base_dir)
    if path.is_file():
        try:
            path.unlink()
            return True
        except Exception:
            try:
                path.write_text("[]", encoding="utf-8")
                return True
            except Exception:
                return False
    return True


def get_sessions_dir(base_dir: Path | None = None) -> Path:
    """Retorna el directorio de almacenamiento de sesiones históricas."""
    base = (base_dir or Path.cwd()).resolve()
    return base / SESSIONS_DIR_NAME


def save_session_record(
    session_id: str,
    provider: str | None,
    model: str | None,
    messages: list[dict[str, Any]],
    base_dir: Path | None = None,
) -> Path | None:
    """Guarda un registro detallado de la sesión en .harness_sessions/<session_id>.json."""
    sessions_dir = get_sessions_dir(base_dir)
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        record_file = sessions_dir / f"{session_id}.json"

        clean_messages: list[dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg:
                item = {"role": msg["role"], "content": msg.get("content", "")}
                if "tool_calls" in msg and msg["tool_calls"]:
                    item["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg and msg["tool_call_id"]:
                    item["tool_call_id"] = msg["tool_call_id"]
                clean_messages.append(item)

        now = datetime.now()
        data = {
            "session_id": session_id,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": now.isoformat(),
            "provider": provider,
            "model": model,
            "message_count": len(clean_messages),
            "messages": clean_messages,
        }
        record_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return record_file
    except Exception:
        return None


def list_saved_sessions(base_dir: Path | None = None) -> list[dict[str, Any]]:
    """Devuelve la lista ordenada cronológicamente de sesiones guardadas en .harness_sessions/."""
    sessions_dir = get_sessions_dir(base_dir)
    if not sessions_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    for file in sessions_dir.glob("*.json"):
        try:
            content = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(content, dict) and "session_id" in content:
                records.append({
                    "session_id": content.get("session_id", file.stem),
                    "created_at": content.get("created_at", ""),
                    "timestamp": content.get("timestamp", ""),
                    "provider": content.get("provider"),
                    "model": content.get("model"),
                    "message_count": content.get("message_count", len(content.get("messages", []))),
                })
        except Exception:
            continue

    # Ordenar por timestamp o fecha descendente (más reciente primero)
    records.sort(key=lambda r: r.get("timestamp") or r.get("created_at") or "", reverse=True)
    return records


def load_session_by_id(session_id: str, base_dir: Path | None = None) -> dict[str, Any] | None:
    """Carga los datos y mensajes de una sesión específica por su ID."""
    sessions_dir = get_sessions_dir(base_dir)
    clean_id = session_id.strip()
    if clean_id.endswith(".json"):
        clean_id = clean_id[:-5]

    target_file = sessions_dir / f"{clean_id}.json"
    if not target_file.is_file():
        # Búsqueda parcial o insensible a mayúsculas
        for file in sessions_dir.glob("*.json"):
            if file.stem.lower() == clean_id.lower():
                target_file = file
                break
        else:
            return None

    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "messages" in data:
            return data
    except Exception:
        pass
    return None


def load_model_memory(config_path: Path | None = None) -> dict[str, Any]:
    """Carga la configuración y memoria de modelos en cascada (local -> global).

    Si no existe o está corrupto, inicializa con valores limpios sin asumir proveedor.
    """
    path = config_path or get_default_config_path()
    data: dict[str, Any] | None = None

    if path.exists():
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            pass

    if data is None and config_path is None:
        # Fallback global si la ruta local no existe y no se especificó ruta personalizada
        global_path = (get_global_harness_dir() / DEFAULT_CONFIG_FILE).resolve()
        if path.resolve() != global_path and global_path.exists():
            try:
                parsed = json.loads(global_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                pass

    if data is None:
        data = {
            "active_provider": None,
            "active_model": None,
            "saved_models": {k: list(v) for k, v in DEFAULT_MODELS.items()},
            "endpoints": {},
        }
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    if "saved_models" not in data or not isinstance(data["saved_models"], dict):
        data["saved_models"] = {k: list(v) for k, v in DEFAULT_MODELS.items()}
    if "active_provider" not in data:
        data["active_provider"] = None
    if "active_model" not in data:
        data["active_model"] = None
    if "endpoints" not in data or not isinstance(data["endpoints"], dict):
        data["endpoints"] = {}

    # Aplicar variables de entorno de endpoints personalizados si existen
    for prov, url in data.get("endpoints", {}).items():
        if url and isinstance(url, str):
            env_key = f"{prov.upper()}_BASE_URL"
            if not os.getenv(env_key):
                os.environ[env_key] = url.strip()

    return data


def save_model_selection(
    provider: str,
    model: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Registra un nuevo modelo, lo marca como activo y lo persiste en disco."""
    return add_user_model(provider, model, config_path=config_path, set_active=True)


def get_available_models_catalog(config_path: Path | None = None) -> list[dict[str, Any]]:
    """Devuelve la lista ordenada y numerada de modelos registrados por el usuario."""
    data = load_model_memory(config_path)
    saved = data.get("saved_models", {})
    catalog: list[dict[str, Any]] = []
    idx = 1
    active_prov = data.get("active_provider")
    active_mod = data.get("active_model")

    for prov in sorted(saved.keys()):
        for mod in sorted(saved[prov]):
            is_active = (prov == active_prov and mod == active_mod)
            catalog.append({
                "index": idx,
                "provider": prov,
                "model": mod,
                "active": is_active,
            })
            idx += 1
    return catalog


def get_provider_endpoints(config_path: Path | None = None) -> dict[str, str]:
    """Retorna el mapeo de endpoints personalizados por proveedor."""
    data = load_model_memory(config_path)
    endpoints = data.get("endpoints", {})
    return dict(endpoints) if isinstance(endpoints, dict) else {}


def set_provider_endpoint(
    provider: str,
    endpoint_url: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Configura y persiste un endpoint personalizado para un proveedor."""
    prov = provider.strip().lower()
    url = endpoint_url.strip()
    if not prov or not url:
        raise ValueError("El proveedor y el endpoint no pueden estar vacíos")

    data = load_model_memory(config_path)
    if "endpoints" not in data or not isinstance(data["endpoints"], dict):
        data["endpoints"] = {}
    data["endpoints"][prov] = url

    # Inyectar inmediatamente en entorno de ejecución
    os.environ[f"{prov.upper()}_BASE_URL"] = url

    path = config_path or get_default_config_path()
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # Guardar también en ~/.harness/ para disponibilidad global
    if config_path is None:
        try:
            g_path = (get_global_harness_dir() / DEFAULT_CONFIG_FILE).resolve()
            if path.resolve() != g_path:
                g_data = load_model_memory(g_path)
                if "endpoints" not in g_data or not isinstance(g_data["endpoints"], dict):
                    g_data["endpoints"] = {}
                g_data["endpoints"][prov] = url
                g_path.write_text(json.dumps(g_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return data


def add_user_model(
    provider: str,
    model: str,
    config_path: Path | None = None,
    set_active: bool = True,
    endpoint_url: str | None = None,
) -> dict[str, Any]:
    """Registra un modelo definido por el usuario, opcionalmente su endpoint y lo activa."""
    data = load_model_memory(config_path)
    prov = provider.strip().lower()
    mod = model.strip()
    if not prov or not mod:
        raise ValueError("El proveedor y el modelo no pueden estar vacíos")

    if "saved_models" not in data or not isinstance(data["saved_models"], dict):
        data["saved_models"] = {}
    if prov not in data["saved_models"]:
        data["saved_models"][prov] = []

    if mod not in data["saved_models"][prov]:
        data["saved_models"][prov].append(mod)

    if endpoint_url and endpoint_url.strip():
        url = endpoint_url.strip()
        if "endpoints" not in data or not isinstance(data["endpoints"], dict):
            data["endpoints"] = {}
        data["endpoints"][prov] = url
        os.environ[f"{prov.upper()}_BASE_URL"] = url

    if set_active:
        data["active_provider"] = prov
        data["active_model"] = mod

    path = config_path or get_default_config_path()
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # Persistir también copia en ~/.harness/ si la ruta es local y no personalizada
    if config_path is None:
        try:
            g_path = (get_global_harness_dir() / DEFAULT_CONFIG_FILE).resolve()
            if path.resolve() != g_path:
                g_data = load_model_memory(g_path)
                if "saved_models" not in g_data or not isinstance(g_data["saved_models"], dict):
                    g_data["saved_models"] = {}
                if prov not in g_data["saved_models"]:
                    g_data["saved_models"][prov] = []
                if mod not in g_data["saved_models"][prov]:
                    g_data["saved_models"][prov].append(mod)
                if endpoint_url and endpoint_url.strip():
                    if "endpoints" not in g_data or not isinstance(g_data["endpoints"], dict):
                        g_data["endpoints"] = {}
                    g_data["endpoints"][prov] = endpoint_url.strip()
                if set_active:
                    g_data["active_provider"] = prov
                    g_data["active_model"] = mod
                g_path.write_text(json.dumps(g_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return data


def remove_user_model(
    target: str | int,
    config_path: Path | None = None,
) -> tuple[bool, str]:
    """Elimina un modelo del catálogo por número de índice o por nombre."""
    data = load_model_memory(config_path)
    catalog = get_available_models_catalog(config_path)
    target_str = str(target).strip()

    found_prov: str | None = None
    found_mod: str | None = None

    if target_str.isdigit():
        idx = int(target_str)
        for item in catalog:
            if item["index"] == idx:
                found_prov = item["provider"]
                found_mod = item["model"]
                break
    else:
        # Primero buscar coincidencia exacta con el nombre del modelo o proveedor:modelo
        for item in catalog:
            if item["model"].lower() == target_str.lower() or f"{item['provider']}:{item['model']}".lower() == target_str.lower():
                found_prov = item["provider"]
                found_mod = item["model"]
                break

        if not found_prov and ":" in target_str:
            p, m = target_str.split(":", 1)
            p = p.strip().lower()
            m = m.strip()
            for item in catalog:
                if item["provider"].lower() == p and item["model"].lower() == m.lower():
                    found_prov = item["provider"]
                    found_mod = item["model"]
                    break

    if not found_prov or not found_mod:
        return False, f"No se encontró el modelo '{target}' en el catálogo."

    if found_prov in data.get("saved_models", {}):
        if found_mod in data["saved_models"][found_prov]:
            data["saved_models"][found_prov].remove(found_mod)
            if not data["saved_models"][found_prov]:
                del data["saved_models"][found_prov]

    if data.get("active_provider") == found_prov and data.get("active_model") == found_mod:
        data["active_provider"] = None
        data["active_model"] = None

    path = config_path or get_default_config_path()
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    return True, f"Modelo {found_prov}:{found_mod} eliminado del catálogo."


def resolve_model_selection(
    selection: str | int,
    config_path: Path | None = None,
) -> tuple[str, str] | None:
    """Resuelve una selección (por índice numérico o por nombre) contra el catálogo registrado."""
    catalog = get_available_models_catalog(config_path)
    sel_str = str(selection).strip()
    if sel_str.isdigit():
        idx = int(sel_str)
        for item in catalog:
            if item["index"] == idx:
                return item["provider"], item["model"]
    else:
        # Primero coincidencia directa por nombre de modelo o proveedor:modelo
        for item in catalog:
            if item["model"].lower() == sel_str.lower() or f"{item['provider']}:{item['model']}".lower() == sel_str.lower():
                return item["provider"], item["model"]

        if ":" in sel_str:
            p, m = sel_str.split(":", 1)
            p = p.strip().lower()
            m = m.strip()
            for item in catalog:
                if item["provider"].lower() == p and item["model"].lower() == m.lower():
                    return item["provider"], item["model"]
    return None


def save_api_key_to_env(
    provider: str,
    api_key: str,
    env_path: Path | None = None,
) -> None:
    """Guarda o actualiza una variable de API Key en el archivo .env local e inyecta en memoria."""
    target_env = env_path or (Path.cwd() / ".env")
    env_var_map = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": "OLLAMA_API_KEY",
    }
    var_name = env_var_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
    cleaned_key = api_key.strip()

    # Inyección inmediata en memoria para activación en vivo
    os.environ[var_name] = cleaned_key

    lines: list[str] = []
    found = False

    if target_env.exists():
        try:
            content = target_env.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith(f"{var_name}=") or line.startswith(f"{var_name} ="):
                    lines.append(f"{var_name}={cleaned_key}")
                    found = True
                else:
                    lines.append(line)
        except Exception:
            pass

    if not found:
        lines.append(f"{var_name}={cleaned_key}")

    try:
        target_env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass

    # Si se guarda en la ubicación estándar por defecto, respaldar también en ~/.harness/.env
    if env_path is None:
        try:
            g_dir = get_global_harness_dir()
            g_dir.mkdir(parents=True, exist_ok=True)
            g_env = g_dir / ".env"
            g_lines: list[str] = []
            g_found = False
            if g_env.exists():
                g_content = g_env.read_text(encoding="utf-8")
                for line in g_content.splitlines():
                    if line.startswith(f"{var_name}=") or line.startswith(f"{var_name} ="):
                        g_lines.append(f"{var_name}={cleaned_key}")
                        g_found = True
                    else:
                        g_lines.append(line)
            if not g_found:
                g_lines.append(f"{var_name}={cleaned_key}")
            g_env.write_text("\n".join(g_lines) + "\n", encoding="utf-8")
        except Exception:
            pass


def build_workspace_system_prompt(
    base_prompt: str,
    base_dir: Path | None = None,
) -> str:
    """Construye el prompt de sistema enriquecido con el espacio de trabajo y AGENT.md."""
    cwd = (base_dir or Path.cwd()).resolve()
    sections: list[str] = [base_prompt.strip()]

    # Inyección de AGENT.md si existe
    agent_md_path = cwd / "AGENT.md"
    if agent_md_path.is_file():
        try:
            agent_content = agent_md_path.read_text(encoding="utf-8", errors="replace").strip()
            if agent_content:
                sections.append(f"\n--- Directrices del Proyecto (AGENT.md) ---\n{agent_content}")
        except Exception:
            pass

    sections.append(f"\n--- Contexto de Ejecución ---\nDirectorio de trabajo actual (CWD): {cwd}")
    sections.append(
        "--- PRINCIPIO DE VERDAD FÁCTICA (ANTI-ALUCINACIÓN) ---\n"
        "1. NUNCA asumas ni inventes que un archivo, carpeta o comando se completó con éxito a menos que la herramienta lo confirme explícitamente en su salida.\n"
        "2. Si una herramienta devuelve 'Acción cancelada' o un error, NUNCA declares la tarea como completada. Informa honestamente al usuario que la acción no se ejecutó.\n"
        "3. Si no tienes certeza de la estructura actual, usa 'list_dir' o 'read_file' antes de emitir conclusiones."
    )
    return "\n\n".join(sections)


def has_valid_key_for_provider(provider: str | None) -> bool:
    """Verifica si el entorno cuenta con una clave o acceso válido para el proveedor."""
    if not provider:
        return False
    prov = provider.lower()
    if prov in ("ollama", "lmstudio", "local", "custom"):
        return True
    from harness.llm_provider import SUPPORTED_PROVIDERS
    info = SUPPORTED_PROVIDERS.get(prov)
    if not info:
        return False
    base_url = os.getenv(f"{prov.upper()}_BASE_URL", "")
    if any(loc in base_url for loc in ("localhost", "127.0.0.1", "0.0.0.0")):
        return True
    return bool(os.getenv(info["env_key"]))

