# Tasks

## 1. Proveedores Universales y Sin Clave en Adaptador
- [x] 1.1 Extender `SUPPORTED_PROVIDERS` en `harness/llm_provider.py` con `lmstudio`, `local`, `custom` y `deepseek`, y permitir que proveedores locales o con endpoint local operen sin clave de API. Verificar con test unitario.

## 2. Sanitización de Prompt y Gestión de Claves en CLI
- [x] 2.1 En `main.py`, implementar la sanitización de prefijos (`jarvis>`, `>`, `$`) en el bucle REPL para evitar falsos prompts, actualizar `has_valid_key_for_provider` para soportar proveedores locales/localhost, y desactivar proveedores fantasmas sin clave al iniciar. Verificar con test unitario de CLI.

## 3. Pruebas y Validación Integral
- [x] 3.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p "test_*.py"`) y validar la experiencia de usuario interactiva.
