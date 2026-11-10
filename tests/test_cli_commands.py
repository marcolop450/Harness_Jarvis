"""Pruebas unitarias para comandos de control agéntico en harness/cli.py."""

import pytest
from harness.cli import handle_control_command
from harness.session_state import SessionRuntime


def test_command_plan_toggle():
    rt = SessionRuntime()
    assert rt.mode == "ACTOR"

    handled, msg = handle_control_command("/plan", runtime=rt)
    assert handled is True
    assert rt.mode == "PLAN"
    assert "Arquitecto" in msg

    handled, msg = handle_control_command("/plan", runtime=rt)
    assert handled is True
    assert rt.mode == "ACTOR"
    assert "Actuador" in msg


def test_command_steps():
    rt = SessionRuntime()
    assert rt.max_steps == 15

    # Consulta de pasos sin argumento
    handled, msg = handle_control_command("/steps", runtime=rt)
    assert handled is True
    assert "15" in msg

    # Modificar a valor válido
    handled, msg = handle_control_command("/steps 25", runtime=rt)
    assert handled is True
    assert rt.max_steps == 25
    assert "25 pasos por consulta" in msg

    # Modificar a valor fuera de rango
    handled, msg = handle_control_command("/steps 99", runtime=rt)
    assert handled is True
    assert rt.max_steps == 25  # No cambia
    assert "entre 1 y 50" in msg

    # Argumento no numérico
    handled, msg = handle_control_command("/steps diez", runtime=rt)
    assert handled is True
    assert rt.max_steps == 25
    assert "no es un número válido" in msg


def test_command_approval():
    rt = SessionRuntime()
    assert rt.approval_policy == "CONFIRM"

    # Conmutar sin argumento
    handled, msg = handle_control_command("/approval", runtime=rt)
    assert handled is True
    assert rt.approval_policy == "AUTO"
    assert "Automática" in msg

    handled, msg = handle_control_command("/approval", runtime=rt)
    assert handled is True
    assert rt.approval_policy == "CONFIRM"
    assert "Confirmación interactiva" in msg

    # Asignar explícito
    handled, msg = handle_control_command("/approval auto", runtime=rt)
    assert handled is True
    assert rt.approval_policy == "AUTO"

    handled, msg = handle_control_command("/approval confirm", runtime=rt)
    assert handled is True
    assert rt.approval_policy == "CONFIRM"

    # Política inválida
    handled, msg = handle_control_command("/approval desconocida", runtime=rt)
    assert handled is True
    assert rt.approval_policy == "CONFIRM"
    assert "no válida" in msg
