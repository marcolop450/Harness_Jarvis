# Tasks

## 1. Empaquetado estándar de Python (PEP 621)

- [x] 1.1 Crear `pyproject.toml` configurando `setuptools.build_meta`, metadatos del proyecto y script de consola `jarvis = "main:main"`. Verificar validando sintaxis TOML con `python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['scripts'])"`.
- [x] 1.2 Crear suite de pruebas unitarias en `tests/test_distribution.py` para validar la estructura de `pyproject.toml` y la disponibilidad del callable `main:main`. Verificar ejecutando `python -m unittest tests/test_distribution.py -v`.

## 2. Scripts automatizados de instalación para Windows

- [x] 2.1 Crear script `install.bat` que valide la presencia de Python, ejecute `python -m pip install -e .` y verifique la disponibilidad del comando `jarvis`. Verificar ejecutando el script y comprobando el código de retorno.
- [x] 2.2 Crear script auxiliar para PowerShell `install.ps1` con mensajes claros y validación de variables de entorno PATH. Verificar ejecutando validación de sintaxis con PowerShell.

## 3. Integración global y documentación

- [x] 3.1 Ejecutar la suite completa de pruebas del proyecto para asegurar compatibilidad total y ausencia de regresiones. Verificar mediante `python -m unittest discover -s tests -p "test_*.py" -v`.
- [x] 3.2 Actualizar `README.md` documentando la instalación con un solo comando en cualquier PC (`install.bat` o `pip install -e .`) y el uso del comando `jarvis`. Verificar visualizando el contenido del archivo.

## Workflow follow-up

- Archivar el cambio `cli-distribution` una vez completadas y verificadas todas las tareas tras ejecutar `/opsx-apply`.
