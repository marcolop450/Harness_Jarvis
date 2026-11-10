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


def get_console() -> Console:
    """Retorna una instancia configurada de Rich Console."""
    global _console
    if _console is None:
        _console = Console()
    return _console


def set_console(console: Console) -> None:
    """Permite inyectar una consola personalizada (e.g. en pruebas unitarias)."""
    global _console
    _console = console


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

    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Proveedor", style="bold white", width=14)
    table.add_column("Modelo", style="white", min_width=25)
    table.add_column("Estado Credencial", style="dim", width=18)
    table.add_column("Activo", justify="center", width=8)

    for idx, item in enumerate(catalog, 1):
        prov = item.get("provider", "").lower()
        mod = item.get("model", "")
        has_k = item.get("has_key", False)

        is_active = (
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
            str(idx),
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
