"""Gestión del estado de ejecución dinámico de la sesión en memoria."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SessionRuntime:
    """Mantiene las opciones mutables en caliente durante la sesión activa."""

    max_steps: int = 15
    mode: str = "ACTOR"  # "ACTOR" o "PLAN"
    approval_policy: str = "CONFIRM"  # "CONFIRM" o "AUTO"
    modified_files: Dict[str, str] = field(default_factory=dict)

    def set_max_steps(self, steps: int) -> bool:
        """Ajusta el límite de pasos dentro del rango válido [1, 50]."""
        if not isinstance(steps, int) or steps < 1 or steps > 50:
            return False
        self.max_steps = steps
        return True

    def set_mode(self, mode: str) -> bool:
        """Establece el modo de razonamiento ('ACTOR' o 'PLAN')."""
        normalized = mode.strip().upper()
        if normalized not in ("ACTOR", "PLAN"):
            return False
        self.mode = normalized
        return True

    def toggle_plan_mode(self) -> str:
        """Alterna entre modo ACTOR y modo PLAN."""
        self.mode = "PLAN" if self.mode == "ACTOR" else "ACTOR"
        return self.mode

    def is_plan_mode(self) -> bool:
        """Retorna True si la sesión se encuentra en modo Arquitecto (solo lectura)."""
        return self.mode == "PLAN"

    def set_approval_policy(self, policy: str) -> bool:
        """Establece la política de confirmación interactiva ('CONFIRM' o 'AUTO')."""
        normalized = policy.strip().upper()
        if normalized not in ("CONFIRM", "AUTO"):
            return False
        self.approval_policy = normalized
        return True

    def toggle_approval_policy(self) -> str:
        """Alterna entre CONFIRM y AUTO."""
        self.approval_policy = "AUTO" if self.approval_policy == "CONFIRM" else "CONFIRM"
        return self.approval_policy

    def record_file_snapshot(self, filepath: str | Path, content: str) -> None:
        """Registra el contenido original del archivo antes de su primera modificación."""
        resolved = str(Path(filepath).resolve())
        if resolved not in self.modified_files:
            self.modified_files[resolved] = content

    def get_diffs(self, cwd: Optional[str | Path] = None) -> List[str]:
        """Calcula las diferencias unificadas entre el estado original y el archivo en disco."""
        base_dir = Path(cwd).resolve() if cwd else Path.cwd()
        diff_outputs: List[str] = []

        for file_str, original_content in self.modified_files.items():
            p = Path(file_str)
            if not p.exists():
                current_content = ""
            else:
                try:
                    current_content = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

            try:
                rel_path = p.relative_to(base_dir).as_posix()
            except ValueError:
                rel_path = p.name

            orig_lines = original_content.splitlines(keepends=True)
            curr_lines = current_content.splitlines(keepends=True)

            diff = list(
                difflib.unified_diff(
                    orig_lines,
                    curr_lines,
                    fromfile=f"a/{rel_path} (original)",
                    tofile=f"b/{rel_path} (actual)",
                )
            )
            if diff:
                diff_outputs.append("".join(diff))

        return diff_outputs

    def reset(self) -> None:
        """Restablece los parámetros por defecto de la sesión."""
        self.max_steps = 15
        self.mode = "ACTOR"
        self.approval_policy = "CONFIRM"
        self.modified_files.clear()


# Instancia singleton predeterminada para el proceso activo
_GLOBAL_RUNTIME: Optional[SessionRuntime] = None


def get_session_runtime() -> SessionRuntime:
    """Devuelve la instancia global de SessionRuntime para el proceso activo."""
    global _GLOBAL_RUNTIME
    if _GLOBAL_RUNTIME is None:
        _GLOBAL_RUNTIME = SessionRuntime()
    return _GLOBAL_RUNTIME
