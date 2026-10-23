"""Pruebas unitarias para validar el empaquetado, distribución y punto de entrada de Jarvis."""

import importlib
from pathlib import Path
import unittest

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


class TestCliDistribution(unittest.TestCase):
    """Verifica la configuración de distribución estándar PEP 518/621."""

    def setUp(self) -> None:
        self.root_dir = Path(__file__).resolve().parent.parent
        self.pyproject_path = self.root_dir / "pyproject.toml"

    def test_pyproject_toml_exists(self) -> None:
        """Verifica que pyproject.toml exista en la raíz del proyecto."""
        self.assertTrue(self.pyproject_path.is_file(), "pyproject.toml debe existir en la raíz")

    def test_pyproject_toml_structure_and_scripts(self) -> None:
        """Verifica que pyproject.toml tenga la estructura estándar y registre el script jarvis."""
        with open(self.pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Build-system
        self.assertIn("build-system", data)
        self.assertEqual(data["build-system"].get("build-backend"), "setuptools.build_meta")

        # Project metadata
        project = data.get("project", {})
        self.assertEqual(project.get("name"), "harness-jarvis")
        self.assertIn("version", project)
        self.assertIn("dependencies", project)

        # Scripts
        scripts = project.get("scripts", {})
        self.assertIn("jarvis", scripts, "Debe registrarse el comando 'jarvis' en project.scripts")
        self.assertEqual(scripts["jarvis"], "main:main")

    def test_entrypoint_callable(self) -> None:
        """Verifica que el target main:main sea importable y ejecutable."""
        main_mod = importlib.import_module("main")
        self.assertTrue(hasattr(main_mod, "main"), "El módulo main debe definir la función main")
        main_func = getattr(main_mod, "main")
        self.assertTrue(callable(main_func), "main.main debe ser un objeto invocable (callable)")


if __name__ == "__main__":
    unittest.main()
