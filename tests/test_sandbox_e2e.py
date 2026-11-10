"""Prueba de integración de punta a punta en sandbox para Harness Jarvis CLI."""

import io
from pathlib import Path
from unittest.mock import patch
import pytest

from main import main
from harness.session_state import get_session_runtime


def test_e2e_sandbox_workflow(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runtime = get_session_runtime()
    runtime.reset()

    # Secuencia de comandos en el REPL interactivo
    command_sequence = [
        "/guide",
        "/plan",
        "/steps 20",
        "/approval auto",
        "/tokens",
        "/tree 1",
        "/doctor",
        "exit",
    ]

    out_buf = io.StringIO()

    with patch("sys.stdout", out_buf):
        with patch("builtins.input", side_effect=command_sequence):
            ret_code = main([])

    assert ret_code == 0
    output = out_buf.getvalue()

    # 1. Verificación de banner y comandos
    assert "Harness Jarvis CLI" in output
    assert "GUIA RAPIDA DE INICIO" in output

    # 2. Verificación de conmutación de modo Arquitecto
    assert "Modo de razonamiento conmutado a: PLAN" in output
    assert runtime.is_plan_mode() is True

    # 3. Verificación de ajuste dinámico de pasos
    assert "Límite de pasos actualizado a: 20 pasos por consulta" in output
    assert runtime.max_steps == 20

    # 4. Verificación de conmutación de política de aprobación
    assert "AUTO" in output
    assert runtime.approval_policy == "AUTO"

    # 5. Verificación de observabilidad de tokens
    assert "OBSERVABILIDAD DE TOKENS Y CONTEXTO" in output

    # 6. Verificación de árbol de directorio
    assert "ÁRBOL DE DIRECTORIO" in output

    # 7. Verificación de diagnóstico /doctor
    assert "DIAGNÓSTICO DEL SISTEMA - HARNESS DOCTOR" in output

    # 8. Cierre ordenado
    assert "¡Hasta luego!" in output

    runtime.reset()
