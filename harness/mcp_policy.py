"""Políticas locales MCP. Las anotaciones remotas nunca conceden permisos."""
from __future__ import annotations

import asyncio
import ipaddress
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any, Callable

ALLOWED_TOOLS = {"fetch": {"fetch"}}


def public_url_syntax(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Fetch requiere una URL HTTP/HTTPS pública.")
    if parsed.username or parsed.password:
        raise ValueError("No se admiten credenciales en la URL.")
    if parsed.port not in (None, 80, 443):
        raise ValueError("Fetch solo permite los puertos web 80 y 443.")
    return parsed.hostname.encode("idna").decode("ascii")


async def validate_public_url(url: str) -> None:
    """Resolver antes del envío; Fetch valida otra vez cada salto HTTP."""
    host = public_url_syntax(url)
    addresses = await asyncio.get_running_loop().getaddrinfo(host, None)
    if not addresses:
        raise ValueError("No se pudo resolver el destino público.")
    for info in addresses:
        address = ipaddress.ip_address(info[4][0])
        if isinstance(address, ipaddress.IPv6Address):
            address = address.ipv4_mapped or address
            if address in ipaddress.ip_network("64:ff9b::/96"):
                address = ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        if not address.is_global or address.is_multicast:
            raise ValueError("Fetch bloqueó un destino local, privado o reservado.")


def prepare_call(server: str, name: str, arguments: dict[str, Any], workspace: Path,
                 confirm_fn: Callable[[str, str], bool] | None = None) -> dict[str, Any]:
    if name not in ALLOWED_TOOLS.get(server, set()):
        raise ValueError("Herramienta MCP no autorizada por la política local.")
    args = dict(arguments)
    if server == "fetch":
        public_url_syntax(args.get("url", ""))
        args["max_length"] = min(int(args.get("max_length", 3500)), 3500)
    return args


def filter_result(server: str, name: str, text: str, arguments: dict[str, Any],
                  workspace: Path) -> str:
    return text
