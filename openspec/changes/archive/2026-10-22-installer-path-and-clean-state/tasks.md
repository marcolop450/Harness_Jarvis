# Tasks

## 1. Estado limpio no configurado

- [x] 1.1 Modificar `harness/model_config.py` para que `load_model_memory()` retorne `(None, None)` o strings vacíos cuando no exista configuración ni claves en `.env`, y actualizar pruebas asociadas. Verificar ejecutando `python -m unittest tests/test_model_config.py -v`.
- [x] 1.2 Actualizar `main.py` para renderizar `[SIN CONFIGURAR]` en proveedor y modelo en el banner inicial, y emitir orientación amigable al usuario si envía una consulta sin proveedor configurado. Verificar ejecutando `python -m unittest tests/test_cli.py -v`.

## 2. Inyección automática de PATH en Windows

- [x] 2.1 Actualizar `install.bat` para detectar automáticamente la carpeta Scripts de Python, registrarla de forma permanente en el PATH de usuario en el Registro de Windows y añadirla a la sesión activa actual. Verificar ejecutando validación con `--no-pause`.
- [x] 2.2 Actualizar `install.ps1` con la misma lógica de inyección de PATH permanente y verificación en PowerShell. Verificar ejecutando análisis de sintaxis con PowerShell.

## 3. Verificación global y documentación

- [x] 3.1 Ejecutar la suite completa de pruebas unitarias para confirmar la ausencia total de regresiones. Verificar mediante `python -m unittest discover -s tests -p "test_*.py" -v`.
- [x] 3.2 Actualizar `README.md` documentando la configuración automática de PATH y el estado inicial transparente. Verificar visualizando el contenido del archivo.

## Workflow follow-up

- Archivar el cambio `installer-path-and-clean-state` una vez implementado y verificado mediante `/opsx-apply`.
