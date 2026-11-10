"""Pruebas unitarias para SessionRuntime en harness/session_state.py."""

import pytest
from pathlib import Path
from harness.session_state import SessionRuntime, get_session_runtime


def test_session_runtime_defaults():
    runtime = SessionRuntime()
    assert runtime.max_steps == 15
    assert runtime.mode == "ACTOR"
    assert not runtime.is_plan_mode()
    assert runtime.approval_policy == "CONFIRM"
    assert runtime.modified_files == {}


def test_set_max_steps():
    runtime = SessionRuntime()
    assert runtime.set_max_steps(25) is True
    assert runtime.max_steps == 25

    # Casos límites inválidos
    assert runtime.set_max_steps(0) is False
    assert runtime.set_max_steps(51) is False
    assert runtime.set_max_steps("10") is False  # type: ignore
    assert runtime.max_steps == 25


def test_mode_and_plan_toggle():
    runtime = SessionRuntime()
    assert runtime.toggle_plan_mode() == "PLAN"
    assert runtime.is_plan_mode() is True

    assert runtime.toggle_plan_mode() == "ACTOR"
    assert runtime.is_plan_mode() is False

    assert runtime.set_mode("plan") is True
    assert runtime.is_plan_mode() is True
    assert runtime.set_mode("invalido") is False


def test_approval_policy_toggle():
    runtime = SessionRuntime()
    assert runtime.toggle_approval_policy() == "AUTO"
    assert runtime.approval_policy == "AUTO"

    assert runtime.toggle_approval_policy() == "CONFIRM"
    assert runtime.approval_policy == "CONFIRM"

    assert runtime.set_approval_policy("auto") is True
    assert runtime.approval_policy == "AUTO"
    assert runtime.set_approval_policy("otro") is False


def test_record_file_snapshot_and_diffs(tmp_path: Path):
    runtime = SessionRuntime()
    test_file = tmp_path / "app.py"
    test_file.write_text("linea1\nlinea2\n", encoding="utf-8")

    # Registrar snapshot original
    runtime.record_file_snapshot(test_file, "linea1\nlinea2\n")

    # Segundo llamado no debe sobrescribir el original
    runtime.record_file_snapshot(test_file, "otra_cosa\n")
    assert runtime.modified_files[str(test_file.resolve())] == "linea1\nlinea2\n"

    # Inicialmente no hay diffs
    assert runtime.get_diffs(cwd=tmp_path) == []

    # Modificar archivo
    test_file.write_text("linea1\nlinea2_modificada\nlinea3\n", encoding="utf-8")
    diffs = runtime.get_diffs(cwd=tmp_path)
    assert len(diffs) == 1
    assert "-linea2" in diffs[0]
    assert "+linea2_modificada" in diffs[0]
    assert "+linea3" in diffs[0]


def test_global_singleton():
    r1 = get_session_runtime()
    r2 = get_session_runtime()
    assert r1 is r2
