"""Adaptador Multi-API para el Agente Harness.

Este es el único módulo autorizado para interactuar con APIs externas
de modelos de lenguaje (OpenAI, Gemini, Groq, OpenRouter, Ollama).
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno si existen
load_dotenv()


@dataclass
class NormalizedToolCall:
    """Representa una llamada a herramienta normalizada de manera uniforme."""
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedResponse:
    """Respuesta unificada de cualquier proveedor LLM."""
    content: str | None = None
    tool_calls: list[NormalizedToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


@dataclass
class ProviderConfig:
    """Configuración resuelta para la conexión con un proveedor."""
    name: str
    base_url: str
    api_key: str
    default_model: str


SUPPORTED_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "gemini": {
        "env_key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
    },
    "groq": {
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
    },
    "ollama": {
        "env_key": "OLLAMA_API_KEY",
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5-coder:7b",
    },
}


def resolve_provider(provider_name: str | None = None) -> ProviderConfig:
    """Resuelve la configuración del proveedor por nombre o detección de entorno.

    Si no se especifica proveedor, evalúa HARNESS_PROVIDER o busca la primera
    clave disponible entre GEMINI, GROQ, OPENROUTER y OPENAI.
    """
    target = (provider_name or os.getenv("HARNESS_PROVIDER") or "").strip().lower()

    if not target:
        # Autodetección según variables de entorno disponibles
        for prov, info in SUPPORTED_PROVIDERS.items():
            if prov == "ollama":
                continue
            if os.getenv(info["env_key"]):
                target = prov
                break
        else:
            # Si no hay claves de nube, revisar si se configuró OLLAMA_BASE_URL
            if os.getenv("OLLAMA_BASE_URL"):
                target = "ollama"
            else:
                target = "gemini"  # Proveedor predeterminado de referencia

    if target not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Proveedor no soportado: '{target}'. "
            f"Proveedores disponibles: {', '.join(SUPPORTED_PROVIDERS.keys())}"
        )

    info = SUPPORTED_PROVIDERS[target]
    env_key = info["env_key"]
    base_url = os.getenv(f"{target.upper()}_BASE_URL", info["base_url"])
    api_key = os.getenv(env_key, "")

    if target == "ollama" and not api_key:
        api_key = "ollama"

    if not api_key and target != "ollama":
        raise ValueError(
            f"Clave de API no configurada para el proveedor '{target}'. "
            f"Por favor configure la variable de entorno {env_key}."
        )

    return ProviderConfig(
        name=target,
        base_url=base_url,
        api_key=api_key,
        default_model=info["default_model"],
    )


def normalize_arguments(raw_args: Any) -> dict[str, Any]:
    """Parsea de forma segura los argumentos de un tool_call a un diccionario."""
    if isinstance(raw_args, dict):
        return raw_args
    if not isinstance(raw_args, str) or not raw_args.strip():
        return {}
    try:
        parsed = json.loads(raw_args)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except Exception as exc:
        return {"raw_arguments": raw_args, "parse_error": str(exc)}


def call_llm(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    client: OpenAI | None = None,
) -> NormalizedResponse:
    """Ejecuta una llamada al modelo de lenguaje y retorna una respuesta normalizada."""
    config = resolve_provider(provider_name)
    target_model = model or config.default_model

    active_client = client or OpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
    )

    kwargs: dict[str, Any] = {
        "model": target_model,
        "messages": messages,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = active_client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    msg = choice.message

    raw_tool_calls = getattr(msg, "tool_calls", None) or []
    normalized_tool_calls: list[NormalizedToolCall] = []

    for i, call in enumerate(raw_tool_calls):
        call_id = getattr(call, "id", None) or f"call_{i}"
        fn = getattr(call, "function", None)
        fn_name = getattr(fn, "name", "") if fn else getattr(call, "name", "")
        raw_args = getattr(fn, "arguments", "{}") if fn else getattr(call, "arguments", "{}")

        normalized_tool_calls.append(
            NormalizedToolCall(
                id=call_id,
                name=fn_name,
                arguments=normalize_arguments(raw_args),
            )
        )

    return NormalizedResponse(
        content=getattr(msg, "content", None),
        tool_calls=normalized_tool_calls,
        finish_reason=choice.finish_reason or "stop",
    )
