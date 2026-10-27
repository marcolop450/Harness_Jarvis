## 1. Especificación y dependencias
- [x] 1.1 Validar propuesta, diseño y deltas; actualizar reglas obsoletas y comprobar openspec validate --strict.
- [x] 1.2 Instalar SDK y servidores fijados con Node local; verificar versiones, pip check y comandos de inicio sin descargas.

## 2. Cliente y Fetch
- [x] 2.1 Implementar gestor MCP, configuración, paginación, ciclo de vida y Fetch público; verificar pruebas unitarias y llamada Fetch real.

## 3. Git
- [x] 3.1 Añadir política Git de solo lectura del repositorio activo; verificar rechazo de repositorio ajeno y consultas reales de estado e historial.

## 4. Filesystem
- [x] 4.1 Añadir políticas de rutas, secretos, búsqueda/listado y confirmaciones; verificar lecturas reales, escritura aprobada y rechazada y enlaces externos.

## 5. CLI y migración
- [x] 5.1 Conectar gestor a REPL y -p, /mcp y reconexión; verificar fallos, cierre y trazabilidad con pruebas de CLI.
- [x] 5.2 Retirar falsos MCP y conservar SQLite nativo seguro; probar confirmaciones, escapes SQL, truncado y regresión completa.

## 6. Verificación y entrega
- [ ] 6.1 Ejecutar integración de los tres servidores y demostración Ollama con llamadas verificadas, registrar evidencia y cierre de procesos.
- [ ] 6.2 Actualizar documentación y reglas, validar artefactos y pruebas finales, sincronizar especificaciones y archivar; verificar commits con identidad existente y sin push.
