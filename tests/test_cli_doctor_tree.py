"""Pruebas unitarias para /doctor, /tree y /diff en harness/cli.py."""

from pathlib import Path
import pytest
from harness.cli import build_directory_tree, handle_diagnostics_command
from harness.session_state import SessionRuntime


def test_build_directory_tree(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "archivo1.py").write_text("a", encoding="utf-8")
    (tmp_path / "archivo2.txt").write_text("b", encoding="utf-8")
    (tmp_path / ".git").mkdir()  # Debe ser ignorado

    tree_str = build_directory_tree(tmp_path, max_depth=2)
    assert "sub/" in tree_str
    assert "archivo1.py" in tree_str
    assert "archivo2.txt" in tree_str
    assert ".git" not in tree_str


def test_command_tree(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('test')", encoding="utf-8")

    handled, msg = handle_diagnostics_command("/tree 2", cwd=tmp_path)
    assert handled is True
    assert "ÁRBOL DE DIRECTORIO" in msg
    assert "main.py" in msg


def test_command_diff(tmp_path: Path):
    rt = SessionRuntime()
    # Sin diffs iniciales
    handled, msg = handle_diagnostics_command("/diff", cwd=tmp_path, runtime=rt)
    assert handled is True
    assert "No se han registrado modificaciones" in msg

    # Modificar archivo registrado
    test_f = tmp_path / "code.py"
    test_f.write_text("version 1\n", encoding="utf-8")
    rt.record_file_snapshot(test_f, "version 1\n")
    test_f.write_text("version 2 con cambio\n", encoding="utf-8")

    handled, msg = handle_diagnostics_command("/diff", cwd=tmp_path, runtime=rt)
    assert handled is True
    assert "DIFERENCIAS REGISTRADAS EN LA SESIÓN" in msg
    assert "-version 1" in msg
    assert "+version 2 con cambio" in msg


def test_command_doctor_unconfigured(tmp_path: Path):
    rt = SessionRuntime()
    handled, msg = handle_diagnostics_command(
        "/doctor",
        provider=None,
        model=None,
        cwd=tmp_path,
        runtime=rt,
    )
    assert handled is True
    assert "HARNESS DOCTOR" in msg
    assert "[NO CONFIGURADO]" in msg


def test_command_doctor_configured(tmp_path: Path):
    rt = SessionRuntime()
    handled, msg = handle_diagnostics_command(
        "/doctor",
        provider="openai",
        model="gpt-4o",
        cwd=tmp_path,
        runtime=rt,
    )
    assert handled is True
    assert "HARNESS DOCTOR" in msg
    assert "OPENAI" in msg
    assert "gpt-4o" in msg
