# Tasks: Experiencia de Terminal Limpia, Gestión de Modelos y Memoria de Chat por Carpeta

## 1. Catálogo limpio de modelos y activación en vivo de claves

- [x] 1.1 Eliminar modelos de prueba precargados en `harness/model_config.py` permitiendo catálogo inicial limpio y verificar que no aparezcan modelos no registrados.
- [x] 1.2 Implementar funciones `add_user_model` y `remove_user_model` con resolución por índice en `harness/model_config.py` y verificar con pruebas unitarias en `tests/test_model_config.py`.
- [x] 1.3 Modificar `save_api_key_to_env` en `harness/model_config.py` para inyectar inmediatamente `os.environ[var_name] = api_key.strip()` y verificar con prueba unitaria.

## 2. Memoria de conversación persistente por carpeta

- [x] 2.1 Implementar `load_session_history`, `save_session_history` y `clear_session_history` en `harness/model_config.py` y verificar con pruebas unitarias.
- [x] 2.2 Asegurar protección de `.harness_session.json` en `harness/guardrails.py` para evitar manipulaciones indebidas por herramientas del agente.

## 3. Terminal interactiva limpia y experiencia de usuario

- [x] 3.1 Implementar el comando `/clear` (limpieza nativa de pantalla y regeneración de cabecera) y el comando `/reset` (vaciado de memoria de chat) en `main.py`.
- [x] 3.2 Actualizar el comando `/model` en `main.py` para soportar listado numerado, `/model add`, `/model rm` y selección rápida por número (`/model 1`).
- [x] 3.3 Integrar prompt dinámico contextual (`[<carpeta> | ⚡ <prov>:<modelo>] jarvis> `) y restauración automática de sesión previa en `main.py`.

## 4. Verificación integral del sistema

- [x] 4.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p "test_*.py" -v`) asegurando cobertura total sin regresiones.
