"""Adaptador Multi-API para el Agente Harness.

Este es el único módulo autorizado para interactuar con APIs externas
de modelos de lenguaje (OpenAI, Gemini, Groq, OpenRouter, Ollama).
"""

from __future__ import annotations
import json
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable
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
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "ollama": {
        "env_key": "OLLAMA_API_KEY",
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5-coder:7b",
    },
    "lmstudio": {
        "env_key": "LMSTUDIO_API_KEY",
        "base_url": "http://localhost:1234/v1",
        "default_model": "default",
    },
    "local": {
        "env_key": "LOCAL_API_KEY",
        "base_url": "http://localhost:1234/v1",
        "default_model": "default",
    },
    "custom": {
        "env_key": "CUSTOM_API_KEY",
        "base_url": "http://localhost:8000/v1",
        "default_model": "default",
    },
}

LOCAL_PROVIDERS: set[str] = {"ollama", "lmstudio", "local", "custom"}


def resolve_provider(provider_name: str | None = None) -> ProviderConfig:
    """Resuelve la configuración del proveedor por nombre o detección de entorno.

    Si no se especifica proveedor, evalúa HARNESS_PROVIDER o busca la primera
    clave disponible entre proveedores de nube.
    """
    target = (provider_name or os.getenv("HARNESS_PROVIDER") or "").strip().lower()

    if not target:
        # Autodetección según variables de entorno disponibles
        for prov, info in SUPPORTED_PROVIDERS.items():
            if prov in LOCAL_PROVIDERS:
                continue
            if os.getenv(info["env_key"]):
                target = prov
                break
        else:
            # Si no hay claves de nube, revisar si se configuró URL local
            if os.getenv("OLLAMA_BASE_URL"):
                target = "ollama"
            elif os.getenv("LMSTUDIO_BASE_URL"):
                target = "lmstudio"
            elif os.getenv("LOCAL_BASE_URL"):
                target = "local"
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

    is_local_endpoint = (
        target in LOCAL_PROVIDERS
        or "localhost" in base_url
        or "127.0.0.1" in base_url
        or "0.0.0.0" in base_url
    )

    if is_local_endpoint and not api_key:
        api_key = "local"

    if not api_key and not is_local_endpoint:
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


def repair_json_arguments(raw_args: Any) -> dict[str, Any]:
    """Sanea y repara argumentos JSON emitidos por modelos de lenguaje."""
    if isinstance(raw_args, dict):
        return raw_args
    if not isinstance(raw_args, str) or not raw_args.strip():
        return {}

    text = raw_args.strip()

    # 1. Si está envuelto en bloques markdown ```json ... ``` o ``` ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            first_line = lines[0].strip()
            if first_line.startswith("```"):
                if lines[-1].strip() == "```":
                    text = "\n".join(lines[1:-1]).strip()
                else:
                    text = "\n".join(lines[1:]).strip()

    # 2. Intentar parseo directo
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except Exception:
        pass

    # 3. Remover comas finales (trailing commas) antes de } o ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except Exception:
        pass

    # 4. Si el modelo incluyó texto explicativo antes o después, extraer el primer objeto {...}
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        candidate = match.group(1)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            cand_clean = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                parsed = json.loads(cand_clean)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    # 5. Si sigue sin parsear, retornar diccionario descriptivo con error estructurado
    return {"raw_arguments": raw_args, "parse_error": "JSON malformado no recuperable"}


def normalize_arguments(raw_args: Any) -> dict[str, Any]:
    """Parsea y auto-repara de forma segura los argumentos de un tool_call a un diccionario."""
    return repair_json_arguments(raw_args)


def format_clean_api_error(error: Exception) -> str:
    """Mapea excepciones de API o red a mensajes limpios y concisos de una sola línea.

    Elimina volcados de diccionarios JSON técnicos y categoriza por código HTTP.
    """
    status_code = getattr(error, "status_code", None)
    err_str = str(error)

    # Detección por código de estado explícito
    if status_code == 429 or "429" in err_str or "rate limit" in err_str.lower():
        return (
            "[Error 429]: Límite de tokens/cuota agotado en el proveedor. "
            "Espere un momento o cambie de modelo con /model."
        )
    if status_code == 401 or "401" in err_str or "invalid_api_key" in err_str.lower():
        return (
            "[Error 401]: Clave de API inválida o no autorizada. "
            "Configure su clave con /key <proveedor> <clave>."
        )
    if status_code == 404 or "404" in err_str or "model_not_found" in err_str.lower():
        return (
            "[Error 404]: Modelo no encontrado o no disponible en este proveedor. "
            "Seleccione otro modelo con /model."
        )
    if status_code == 400 or "400" in err_str or "tool_use_failed" in err_str.lower():
        return (
            "[Error 400]: Solicitud rechazada por formato o argumentos inválidos en el proveedor."
        )
    if status_code in (500, 502, 503, 504) or any(c in err_str for c in ("500", "502", "503", "504")):
        return (
            f"[Error {status_code or '50x'}]: Servicio del proveedor temporalmente fuera de línea. "
            "Reintente en unos instantes."
        )
    if "connection" in err_str.lower() or "timeout" in err_str.lower():
        return (
            "[Error de Conexión]: No se pudo contactar al proveedor. "
            "Verifique su conexión a Internet o el endpoint."
        )

    # Si es otra excepción, limpiar posibles bloques JSON
    clean_msg = err_str.split("\n")[0]
    if "{" in clean_msg and "}" in clean_msg:
        # Extraer texto previo a cualquier JSON volcado
        clean_msg = clean_msg.split("{")[0].strip(" -:")
    return f"[Error]: {clean_msg}" if clean_msg else "[Error]: Ocurrió un error inesperado al consultar el modelo."


def call_llm(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    client: OpenAI | None = None,
    max_tokens: int | None = 4096,
    max_retries: int = 5,
    base_delay: float = 2.0,
    sleep_fn: Callable[[float], None] | None = None,
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

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    sleeper = sleep_fn or time.sleep
    response = None

    for attempt in range(max_retries + 1):
        try:
            response = active_client.chat.completions.create(**kwargs)
            break
        except Exception as exc:
            err_str = str(exc)
            status_code = getattr(exc, "status_code", None)
            is_429 = status_code == 429 or "429" in err_str or "rate limit" in err_str.lower()

            if is_429 and attempt < max_retries:
                retry_after = None
                resp = getattr(exc, "response", None)
                if resp is not None and hasattr(resp, "headers"):
                    h_val = resp.headers.get("retry-after")
                    if h_val:
                        try:
                            retry_after = float(h_val)
                        except (ValueError, TypeError):
                            pass

                if retry_after is not None and retry_after > 0:
                    delay = retry_after
                else:
                    jitter = random.uniform(0.1, 1.0)
                    delay = (base_delay * (2 ** attempt)) + jitter
                    delay = min(delay, 60.0)

                print(
                    f"\n[Aviso 429]: Límite de cuota alcanzado. Esperando {delay:.1f}s antes de reintentar (intento {attempt + 1}/{max_retries})...",
                    flush=True,
                )
                sleeper(delay)
                continue

            raise RuntimeError(format_clean_api_error(exc)) from exc

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
