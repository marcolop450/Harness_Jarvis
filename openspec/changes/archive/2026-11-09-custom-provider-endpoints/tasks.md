# Tasks

## 1. Persistencia y Resolución de Endpoints

- [x] 1.1 Extender `harness/model_config.py` con `get_provider_endpoints()`, `set_provider_endpoint()` y soporte de endpoints personalizados en `load_model_memory()` y `add_user_model()`. Verificar con test unitario.

## 2. Comandos CLI y Diagnóstico

- [x] 2.1 Implementar el comando interactivo `/endpoint` y extender `/model add <prov> <mod> [url]` en `main.py`, mejorando el diagnóstico de errores de conexión con sugerencia de reconfiguración. Verificar con test unitario de CLI.

## 3. Pruebas y Validación Integral

- [x] 3.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p \"test_*.py\"`) y validar la asignación dinámica de endpoints.
