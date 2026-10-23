"""Gestión de memoria persistente de modelos y configuración de sesión.

Permite:
- Guardar y restaurar el proveedor y modelo activo entre sesiones en '.harness_models.json'.
- Recordar modelos agregados dinámicamente por el usuario.
- Guardar claves de API en el archivo .env local de forma asistida.
- Construir el contexto del espacio de trabajo (cwd y AGENT.md) para el system prompt.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE: str = ".harness_models.json"

DEFAULT_MODELS: dict[str, list[str]] = {
    "gemini": ["gemini-2.5-flash", "gemini-1.5-pro"],
    "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    "ollama": ["qwen2.5-coder:7b", "llama3.2:3b", "deepseek-r1:8b"],
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "openrouter": ["meta-llama/llama-3.3-70b-instruct"],
}


def get_default_config_path(base_dir: Path | None = None) -> Path:
    """Retorna la ruta hacia el archivo de configuración persistente."""
    base = (base_dir or Path.cwd()).resolve()
    return base / DEFAULT_CONFIG_FILE


def load_model_memory(config_path: Path | None = None) -> dict[str, Any]:
    """Carga la configuración y memoria de modelos desde el archivo JSON.

    Si no existe o está corrupto, inicializa con valores predeterminados seguros.
    """
    path = config_path or get_default_config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if "saved_models" not in data or not isinstance(data["saved_models"], dict):
                    data["saved_models"] = {k: list(v) for k, v in DEFAULT_MODELS.items()}
                if "active_provider" not in data:
                    data["active_provider"] = "gemini"
                if "active_model" not in data:
                    data["active_model"] = "gemini-2.5-flash"
                return data
        except Exception:
            pass

    initial_config = {
        "active_provider": "gemini",
        "active_model": "gemini-2.5-flash",
        "saved_models": {k: list(v) for k, v in DEFAULT_MODELS.items()},
    }
    try:
        path.write_text(json.dumps(initial_config, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    return initial_config


def save_model_selection(
    provider: str,
    model: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Registra un nuevo modelo, lo marca como activo y lo persiste en disco."""
    data = load_model_memory(config_path)
    prov = provider.strip().lower()
    mod = model.strip()

    data["active_provider"] = prov
    data["active_model"] = mod

    if prov not in data["saved_models"]:
        data["saved_models"][prov] = []

    if mod not in data["saved_models"][prov]:
        data["saved_models"][prov].append(mod)

    path = config_path or get_default_config_path()
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    return data


def save_api_key_to_env(
    provider: str,
    api_key: str,
    env_path: Path | None = None,
) -> None:
    """Guarda o actualiza una variable de API Key en el archivo .env local."""
    target_env = env_path or (Path.cwd() / ".env")
    env_var_map = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": "OLLAMA_API_KEY",
    }
    var_name = env_var_map.get(provider.lower(), f"{provider.upper()}_API_KEY")

    lines: list[str] = []
    found = False

    if target_env.exists():
        try:
            content = target_env.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith(f"{var_name}=") or line.startswith(f"{var_name} ="):
                    lines.append(f"{var_name}={api_key.strip()}")
                    found = True
                else:
                    lines.append(line)
        except Exception:
            pass

    if not found:
        lines.append(f"{var_name}={api_key.strip()}")

    target_env.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    return "\n\n".join(sections)
