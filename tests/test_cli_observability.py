"""Pruebas unitarias para comandos /tokens y /export en harness/cli.py."""

from pathlib import Path
import pytest
from harness.cli import handle_observability_command


def test_command_tokens():
    mock_history = [
        {"role": "system", "content": "Eres Jarvis."},
        {"role": "user", "content": "Hola mundo"},
        {"role": "assistant", "content": "Hola, ¿en qué te colaboro hoy?"},
    ]

    handled, msg = handle_observability_command("/tokens", history=mock_history)
    assert handled is True
    assert "OBSERVABILIDAD DE TOKENS Y CONTEXTO" in msg
    assert "Mensajes en contexto activo : 3" in msg
    assert "Tokens estimados" in msg


def test_command_export_default_filename(tmp_path: Path):
    mock_history = [
        {"role": "user", "content": "Crea una función suma"},
        {"role": "assistant", "content": "def suma(a, b): return a + b"},
    ]

    handled, msg = handle_observability_command("/export", history=mock_history, cwd=tmp_path)
    assert handled is True
    assert "[+] Sesión exportada exitosamente a:" in msg

    # Verificar que el archivo se creó en tmp_path
    md_files = list(tmp_path.glob("sesion_jarvis_*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "# Historial de Sesión de Jarvis CLI" in content
    assert "def suma(a, b): return a + b" in content
    assert "### 👤 Usuario" in content
    assert "### 🤖 Jarvis" in content


def test_command_export_custom_filename(tmp_path: Path):
    mock_history = [{"role": "user", "content": "Test"}]

    handled, msg = handle_observability_command("/export mi_informe", history=mock_history, cwd=tmp_path)
    assert handled is True

    target_file = tmp_path / "mi_informe.md"
    assert target_file.exists()
    assert "Test" in target_file.read_text(encoding="utf-8")
