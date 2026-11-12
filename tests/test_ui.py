"""Pruebas unitarias para componentes visuales Rich en harness/ui.py."""

from pathlib import Path
import pytest
from rich.console import Console

from harness.ui import (
    create_banner_panel,
    create_models_table,
    get_console,
    set_console,
    print_rich_banner,
)


def test_create_banner_panel(tmp_path: Path):
    panel = create_banner_panel(
        provider="lmstudio",
        model="qwen3.5-9b",
        cwd=tmp_path,
        has_key=True,
        max_steps=20,
        mode="PLAN",
        approval_policy="AUTO",
    )
    assert panel is not None

    test_console = Console(record=True, width=120)
    test_console.print(panel)
    output = test_console.export_text()

    assert "Harness Jarvis CLI" in output
    assert "LMSTUDIO" in output
    assert "qwen3.5-9b" in output
    assert "PLAN" in output
    assert "AUTO" in output
    assert "20 pasos" in output


def test_create_models_table():
    catalog = [
        {"provider": "openai", "model": "gpt-4o", "has_key": True},
        {"provider": "ollama", "model": "qwen2.5-coder:7b", "has_key": False},
    ]

    table = create_models_table(
        catalog,
        active_provider="openai",
        active_model="gpt-4o",
    )
    assert table is not None

    test_console = Console(record=True, width=120)
    test_console.print(table)
    output = test_console.export_text()

    assert "Catálogo de Modelos Registrados" in output
    assert "OPENAI" in output
    assert "gpt-4o" in output
    assert "OLLAMA" in output
    assert "Local (No req)" in output
    assert "SI" in output


def test_print_rich_banner_execution(tmp_path: Path):
    test_console = Console(record=True, width=120)
    set_console(test_console)

    print_rich_banner(
        provider="groq",
        model="llama-3.3-70b",
        cwd=tmp_path,
        has_key=False,
    )

    output = test_console.export_text()
    assert "GROQ" in output
    assert "llama-3.3-70b" in output
    assert "Pendiente" in output


def test_compact_spinner():
    from harness.ui import compact_spinner
    # En entorno sin TTY debe ejecutarse limpiamente sin lanzar excepciones
    with compact_spinner("Cargando prueba..."):
        pass


def test_print_rich_user_guide():
    from harness.ui import print_rich_user_guide
    test_console = Console(record=True, width=120)
    set_console(test_console)

    print_rich_user_guide()
    out = test_console.export_text()
    assert "GUIA RAPIDA DE INICIO" in out
    assert "/plan" in out
    assert "/approval" in out
    assert "/doctor" in out
    assert "/tree" in out


def test_create_sessions_and_endpoints_tables():
    from harness.ui import create_sessions_table, create_endpoints_table, print_rich_status_card
    test_console = Console(record=True, width=120)
    set_console(test_console)

    sessions = [
        {"session_id": "sess_123", "created_at": "2026-11-12T19:00:00", "provider": "openai", "model": "gpt-4o", "message_count": 5}
    ]
    st = create_sessions_table(sessions)
    test_console.print(st)
    s_out = test_console.export_text()
    assert "sess_123" in s_out
    assert "openai:gpt-4o" in s_out

    providers = {"ollama": {"base_url": "http://localhost:11434/v1"}}
    endpoints = {"ollama": "http://localhost:1234/v1"}
    et = create_endpoints_table(providers, endpoints)
    test_console.print(et)
    e_out = test_console.export_text()
    assert "OLLAMA" in e_out
    assert "http://localhost:1234/v1" in e_out

    print_rich_status_card("Prueba de Estado", [("Clave", "Valor")])
    c_out = test_console.export_text()
    assert "Prueba de Estado" in c_out
    assert "Clave" in c_out
    assert "Valor" in c_out

