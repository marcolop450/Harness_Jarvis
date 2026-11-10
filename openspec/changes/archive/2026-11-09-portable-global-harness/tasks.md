# Tasks

## 1. Empaquetado y Plantillas de Recursos

- [x] 1.1 Crear directorio `harness/data/` con la plantilla `default_mcp.json` y configurar `pyproject.toml` con `package_data` para empaquetado no-código. Verificar que la plantilla sea leíble desde el paquete.

## 2. Configuración en Cascada de Servidores MCP

- [x] 2.1 Implementar la resolución en cascada en `harness/mcp_client.py` (`load_config`): Workspace local -> Directorio global `~/.harness/mcp.json` -> Plantilla empaquetada en `harness/data/`. Verificar con prueba unitaria en carpeta vacía.

## 3. Directorio Global de Usuario y Persistencia

- [x] 3.1 Actualizar `harness/model_config.py` y `main.py` para soportar carga en cascada de `.env` y configuración de modelos desde `~/.harness/` con precedencia del workspace local. Verificar que `/key` y `/model` persistan y resuelvan correctamente.

## 4. Pruebas de Integración y Portabilidad

- [x] 4.1 Ejecutar la suite completa de pruebas unitarias (`python -m unittest discover -s tests -p \"test_*.py\"`) y validar la portabilidad en un directorio temporal virgen confirmando el descubrimiento de herramientas MCP.
