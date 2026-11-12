"""Componentes visuales de terminal con Rich para Harness Jarvis.

Proporciona renderizado de banners con bordes redondeados Unicode (╭─╮),
tablas de catálogo estilizadas, jerarquía semántica de color y fallback
seguro a texto plano en entornos no interactivos.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List, Optional

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Consola global con autodetección de capacidades de terminal
_console: Optional[Console] = None
_custom_console: bool = False


def get_console() -> Console:
    """Retorna una instancia configurada de Rich Console, respetando redirecciones de sys.stdout."""
    global _console
    if _custom_console and _console is not None:
        return _console
    if _console is None or _console.file != sys.stdout:
        _console = Console(file=sys.stdout)
    return _console


def set_console(console: Console) -> None:
    """Permite inyectar una consola personalizada (e.g. en pruebas unitarias)."""
    global _console, _custom_console
    _console = console
    _custom_console = True


def create_banner_panel(
    provider: Optional[str],
    model: Optional[str],
    cwd: Path,
    has_key: bool,
    max_steps: int = 15,
    mode: str = "ACTOR",
    approval_policy: str = "CONFIRM",
) -> Panel:
    """Construye un panel visual estilizado con bordes redondeados Unicode para el inicio de la CLI."""
    prov_str = provider.upper() if provider else "[yellow]SIN CONFIGURAR[/yellow]"
    model_str = model if model else "[yellow]SIN CONFIGURAR[/yellow]"

    if has_key:
        api_status = "[green]● CONFIGURADA[/green]"
    else:
        api_status = "[yellow]○ Pendiente (Usa /key o /model)[/yellow]"

    mode_badge = (
        "[bold magenta]ARQUITECTO (Solo Lectura)[/bold magenta]"
        if mode == "PLAN"
        else "[bold green]ACTUADOR (Lectura y Escritura)[/bold green]"
    )
    pol_badge = "[cyan]CONFIRMAR [s/n][/cyan]" if approval_policy == "CONFIRM" else "[bold yellow]AUTO[/bold yellow]"

    content = Text()
    content.append(" Espacio   : ", style="bold dim")
    content.append(f"{cwd}\n", style="bold white")

    content.append(" Proveedor : ", style="bold dim")
    content.append(f"{provider.upper() if provider else '[SIN CONFIGURAR]'}\n", style="bold cyan")

    content.append(" Modelo    : ", style="bold dim")
    content.append(f"{model if model else '[SIN CONFIGURAR]'}\n", style="bold green")

    content.append(" Estado API: ", style="bold dim")
    content.append("● CONFIGURADA\n" if has_key else "○ Pendiente (Usa /key o /guide)\n", style="green" if has_key else "yellow")

    content.append(" Modo      : ", style="bold dim")
    content.append(f"{mode} ", style="bold magenta" if mode == "PLAN" else "bold blue")
    content.append(" | ", style="dim")
    content.append("Aprobación: ", style="bold dim")
    content.append(f"{approval_policy} ", style="cyan")
    content.append(" | ", style="dim")
    content.append("Límite: ", style="bold dim")
    content.append(f"{max_steps} pasos\n", style="white")

    content.append("\n Comandos clave:\n", style="bold dim")
    content.append("   /model    ", style="bold cyan")
    content.append("Gestionar y alternar modelos activos\n", style="dim")
    content.append("   /plan     ", style="bold magenta")
    content.append("Alternar modo Arquitecto (solo lectura) / Actuador\n", style="dim")
    content.append("   /steps    ", style="bold white")
    content.append("Modificar límite de pasos por consulta en caliente\n", style="dim")
    content.append("   /approval ", style="bold yellow")
    content.append("Conmutar política de confirmación (CONFIRM / AUTO)\n", style="dim")
    content.append("   /doctor   ", style="bold green")
    content.append("Diagnóstico de conectividad LLM y procesos MCP\n", style="dim")
    content.append("   /tokens   ", style="bold blue")
    content.append("Estimar consumo de tokens y ventana de contexto\n", style="dim")
    content.append("   /diff     ", style="bold yellow")
    content.append("Ver cambios de archivos realizados en la sesión\n", style="dim")
    content.append("   /tree     ", style="bold green")
    content.append("Imprimir árbol del espacio de trabajo\n", style="dim")
    content.append("   /export   ", style="bold cyan")
    content.append("Exportar conversación a archivo Markdown\n", style="dim")
    content.append("   /compact  ", style="bold white")
    content.append("Compactar memoria con resumen estructurado\n", style="dim")
    content.append("   /help     ", style="bold white")
    content.append("Guía interactiva completa de uso | exit para salir\n", style="dim")

    return Panel(
        content,
        title="[bold cyan]╭─ Harness Jarvis CLI [/bold cyan][dim](Multi-API Agent)[/dim][bold cyan] ─╮[/bold cyan]",
        subtitle="[dim]Escribe '/' para autocompletar comandos[/dim]",
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(1, 2),
    )


def create_models_table(
    catalog: List[dict[str, Any]],
    active_provider: Optional[str] = None,
    active_model: Optional[str] = None,
) -> Table:
    """Genera una tabla elegante con los modelos registrados y su estado."""
    table = Table(
        title="Catálogo de Modelos Registrados",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", justify="right", width=6)
    table.add_column("Proveedor", style="bold white", width=14)
    table.add_column("Modelo", style="white", min_width=25)
    table.add_column("Estado Credencial", style="dim", width=18)
    table.add_column("Activo", justify="center", width=8)

    for idx, item in enumerate(catalog, 1):
        num_str = str(item.get("index", idx))
        prov = item.get("provider", "").lower()
        mod = item.get("model", "")
        if "has_key" in item:
            has_k = item.get("has_key", False)
        else:
            try:
                from harness.model_config import has_valid_key_for_provider
                has_k = has_valid_key_for_provider(prov)
            except Exception:
                has_k = False

        item_active = item.get("active", False)
        is_active = item_active or (
            active_provider is not None
            and active_model is not None
            and active_provider.lower() == prov
            and active_model.lower() == mod.lower()
        )

        k_str = "[green]● Configurada[/green]" if has_k else "[yellow]○ Sin clave[/yellow]"
        if prov in ("ollama", "lmstudio", "local"):
            k_str = "[cyan]Local (No req)[/cyan]"

        active_str = "[bold green]✓ SI[/bold green]" if is_active else "[dim]-[/dim]"
        row_style = "bold white" if is_active else ""

        table.add_row(
            f"[{num_str}]",
            prov.upper(),
            mod,
            k_str,
            active_str,
            style=row_style,
        )

    return table


def print_rich_banner(
    provider: Optional[str],
    model: Optional[str],
    cwd: Path,
    has_key: bool,
    max_steps: int = 15,
    mode: str = "ACTOR",
    approval_policy: str = "CONFIRM",
) -> None:
    """Renderiza el banner principal en la consola usando Rich."""
    panel = create_banner_panel(
        provider,
        model,
        cwd,
        has_key,
        max_steps=max_steps,
        mode=mode,
        approval_policy=approval_policy,
    )
    console = get_console()
    console.print(panel)


def print_rich_markdown(text: str) -> None:
    """Renderiza texto en Markdown enriquecido."""
    console = get_console()
    console.print(Markdown(text))


@contextmanager
def compact_spinner(
    status_text: str = "Razonando...",
    spinner_style: str = "dots",
) -> Iterator[Any]:
    """Context manager que despliega un spinner minimalista no bloqueante si es TTY."""
    console = get_console()
    if console.is_terminal:
        with console.status(f"[bold cyan]{status_text}[/bold cyan]", spinner=spinner_style) as status:
            yield status
    else:
        yield None


def print_rich_user_guide() -> None:
    """Renderiza una guía de usuario visualmente enriquecida usando paneles Rich con bordes curvos."""
    console = get_console()

    content = (
        "[bold cyan]🚀 1. Conexión de Modelos y Proveedores:[/bold cyan]\n"
        "  • [yellow]/key <proveedor> <clave>[/yellow]       : Configura tu clave de API (Groq, Gemini, OpenAI, OpenRouter).\n"
        "  • [yellow]/endpoint <proveedor> <url>[/yellow]   : Personaliza la URL base (Meta Model API, Ollama, LM Studio).\n"
        "  • [yellow]/model[/yellow]                        : Visualiza tu catálogo numerado de modelos registrados.\n"
        "  • [yellow]/model <numero>[/yellow]               : Cambia de modelo activo en caliente (ej: /model 1).\n"
        "  • [yellow]/model add <prov> <mod> [url][/yellow]: Registra un nuevo modelo con o sin endpoint propio.\n\n"
        "[bold green]🛡️ 2. Control de Razonamiento y Seguridad:[/bold green]\n"
        "  • [yellow]/plan[/yellow]                         : Alterna entre modo [bold magenta]Arquitecto[/bold magenta] (solo lectura) y [bold green]Actuador[/bold green] (edición).\n"
        "  • [yellow]/approval [auto|confirm][/yellow]     : Conmuta entre aprobación automática o confirmación interactiva [s/n/a].\n"
        "  • [yellow]/steps <1-50>[/yellow]                 : Modifica el límite de pasos de razonamiento por turno.\n\n"
        "[bold magenta]🔍 3. Observabilidad, Contexto y Diagnóstico:[/bold magenta]\n"
        "  • [yellow]/doctor[/yellow]                       : Diagnostica la latencia del LLM activo y el estado de servidores MCP.\n"
        "  • [yellow]/tree [profundidad][/yellow]           : Muestra el árbol visual del directorio filtrando basura.\n"
        "  • [yellow]/diff[/yellow]                         : Muestra las diferencias de líneas agregadas/eliminadas en la sesión.\n"
        "  • [yellow]/tokens[/yellow]                       : Estima el consumo de caracteres y porcentaje de ventana de contexto.\n"
        "  • [yellow]/compact[/yellow]                      : Condensa la conversación activa con el LLM conservando acuerdos clave.\n"
        "  • [yellow]/export [ruta.md][/yellow]             : Exporta el historial limpio a un archivo Markdown del proyecto.\n"
        "  • [yellow]/sessions[/yellow] | [yellow]/resume <id>[/yellow]  : Lista o reanuda sesiones anteriores guardadas en este espacio.\n\n"
        "[bold blue]🔌 4. Servidores MCP (Model Context Protocol):[/bold blue]\n"
        "  • [yellow]/mcp[/yellow]                          : Inspecciona el estado de conexión y herramientas descubiertas.\n"
        "  • [yellow]/mcp reconnect[/yellow]                : Reinicia y reconecta los procesos MCP en segundo plano."
    )

    panel = Panel(
        content,
        title="[bold white on dark_blue] ⚡ GUIA RAPIDA DE INICIO - HARNESS JARVIS CLI ⚡ [/bold white on dark_blue]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def create_sessions_table(sessions: List[dict[str, Any]]) -> Table:
    """Genera una tabla Rich estilizada para el historial de sesiones guardadas."""
    table = Table(
        title="HISTORIAL DE SESIONES GUARDADAS EN ESTE ESPACIO",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
    )
    table.add_column("ID de Sesion", style="bold white", min_width=25)
    table.add_column("Fecha y Hora", style="dim", width=20)
    table.add_column("Modelo", style="yellow", width=22)
    table.add_column("Msgs", justify="right", width=8)

    for s in sessions:
        sid = s.get("session_id", "")
        dt = (s.get("created_at") or "")[:19]
        m_info = f"{s.get('provider') or '?'}:{s.get('model') or '?'}"
        cnt = str(s.get("message_count", 0))
        table.add_row(sid, dt, m_info, cnt)

    return table


def create_endpoints_table(
    providers: dict[str, Any],
    endpoints: dict[str, str],
) -> Table:
    """Genera una tabla Rich estilizada para las direcciones y endpoints de los proveedores."""
    import os
    table = Table(
        title="DIRECCIONES Y ENDPOINTS DE PROVEEDORES",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
    )
    table.add_column("Proveedor", style="bold white", width=14)
    table.add_column("Endpoint Activo", style="yellow", min_width=35)
    table.add_column("Estado", justify="center", width=18)

    for p, info in providers.items():
        custom_url = endpoints.get(p) or os.getenv(f"{p.upper()}_BASE_URL")
        active_url = custom_url or info.get("base_url", "")
        is_custom = bool(custom_url)
        tag = "[Personalizado]" if is_custom else "[Por defecto]"
        table.add_row(p.upper(), active_url, tag)

    return table


def print_rich_status_card(title: str, lines: List[tuple[str, str]], border_style: str = "green") -> None:
    """Imprime una tarjeta de estado estilizada con bordes redondeados."""
    console = get_console()
    content = Text()
    for label, val in lines:
        content.append(f"  • {label}: ", style="dim")
        content.append(f"{val}\n", style="bold white")
    panel = Panel(
        content,
        title=f"[bold {border_style}]╭─ {title} ─╮[/bold {border_style}]",
        box=box.ROUNDED,
        border_style=border_style,
        padding=(0, 1),
    )
    console.print(panel)
