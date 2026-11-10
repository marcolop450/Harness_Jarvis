"""Pruebas unitarias para la política de aprobación en caliente en harness/guardrails.py."""

from pathlib import Path
import pytest

from harness.guardrails import (
    SecurityViolationError,
    confirm_action,
    authorize_and_dispatch,
)
from harness.session_state import get_session_runtime


def test_confirm_action_policy_confirm_asks_user():
    runtime = get_session_runtime()
    runtime.set_approval_policy("CONFIRM")

    asked = False

    def mock_input(prompt: str) -> str:
        nonlocal asked
        asked = True
        return "s"

    res = confirm_action("Modificar archivo", details="Ruta: foo.txt", input_fn=mock_input)
    assert asked is True
    assert res is True


def test_confirm_action_policy_auto_skips_user_prompt():
    runtime = get_session_runtime()
    runtime.set_approval_policy("AUTO")

    asked = False

    def mock_input(prompt: str) -> str:
        nonlocal asked
        asked = True
        return "n"

    try:
        # Bajo AUTO, no debe llamar a mock_input y debe retornar True
        res = confirm_action("Modificar archivo", details="Ruta: foo.txt", input_fn=mock_input)
        assert asked is False
        assert res is True
    finally:
        runtime.reset()


def test_authorize_and_dispatch_policy_auto_preserves_security_rules(tmp_path: Path):
    runtime = get_session_runtime()
    runtime.set_approval_policy("AUTO")

    try:
        # 1. Operación válida no interrumpe
        allowed = authorize_and_dispatch(
            "write_file",
            {"path": "valid.txt", "content": "hola"},
            base_dir=tmp_path,
        )
        assert allowed is True

        # 2. Intento de acceder a .env DEBE ser bloqueado con SecurityViolationError
        with pytest.raises(SecurityViolationError):
            authorize_and_dispatch("read_file", {"path": ".env"}, base_dir=tmp_path)

        # 3. Intento de path traversal DEBE ser bloqueado con SecurityViolationError
        with pytest.raises(SecurityViolationError):
            authorize_and_dispatch(
                "write_file",
                {"path": "../../escaped.txt", "content": "malicioso"},
                base_dir=tmp_path,
            )
    finally:
        runtime.reset()
