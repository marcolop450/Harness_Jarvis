# Tasks: Volcado Inmediato de Confirmación y Guía Interactiva Fuera de Línea

## 1. Volcado y resiliencia en confirmación interactiva

- [x] 1.1 Modificar `confirm_action` en `harness/guardrails.py` para realizar volcado explícito (`flush=True`) previo al prompt de entrada y verificar con prueba unitaria en `tests/test_guardrails.py`.
- [x] 1.2 Actualizar la lógica de aceptación en `confirm_action` para admitir variantes afirmativas comunes (`ss`, `sí`, `yes`, etc.) y verificar con pruebas unitarias en `tests/test_guardrails.py`.

## 2. Guía interactiva local para nuevos usuarios

- [x] 2.1 Implementar la función `print_user_guide()` y vincularla a los comandos `/guide`, `/guia` y `/help` en `main.py` de forma totalmente fuera de línea.
- [x] 2.2 Agregar pruebas unitarias en `tests/test_cli.py` para verificar que `/guide` y `/help` muestren la guía completa sin requerir API keys.

## 3. Verificación integral del sistema

- [x] 3.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p "test_*.py" -v`) asegurando cobertura total sin regresiones.
