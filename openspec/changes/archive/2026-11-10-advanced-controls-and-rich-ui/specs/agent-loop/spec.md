# Spec Delta

## MODIFIED Requirements

### Requirement: Ciclo de pasos acotado a MAX_STEPS
El bucle de ejecución SHALL iterar secuencialmente ejecutando pasos hasta que el modelo emita una respuesta final o se alcance el límite de pasos configurado (por defecto 15 o el asignado dinámicamente).

#### Scenario: Terminación normal por respuesta del modelo
- **GIVEN** un bucle en el paso 3 de N pasos configurados
- **WHEN** el modelo genera una respuesta final sin invocar herramientas
- **THEN** el bucle termina exitosamente devolviendo el mensaje al usuario

#### Scenario: Interrupción al alcanzar MAX_STEPS
- **GIVEN** una ejecución continua que llega al límite de pasos configurado (por defecto 15 o el asignado dinámicamente) sin converger
- **WHEN** se completa dicho paso límite
- **THEN** el ciclo se detiene inmediatamente y emite un mensaje notificando que se alcanzó el límite de pasos

#### Scenario: Ajuste dinámico del límite en tiempo de ejecución
- **GIVEN** una sesión donde el usuario definió un nuevo límite de pasos
- **WHEN** el bucle procesa la siguiente consulta
- **THEN** el ciclo utiliza el nuevo límite fijado sin afectar sesiones previas ni reiniciar el proceso

## ADDED Requirements

### Requirement: Modo Arquitecto de solo lectura (Plan Mode)
El bucle de ejecución SHALL soportar una modalidad de razonamiento en la cual se prohíbe la modificación de archivos y la ejecución de comandos destructivos, limitando la acción a lectura y diseño.

#### Scenario: Restricción de escritura en modo Arquitecto
- **GIVEN** el bucle operando en modo Arquitecto
- **WHEN** el modelo de lenguaje intenta invocar una herramienta de escritura o modificación de archivos
- **THEN** el bucle intercepta la llamada, rechaza la operación informando la restricción de modo y preserva la integridad del sistema

#### Scenario: Presentación de plan de diseño sin efectos colaterales
- **GIVEN** una consulta que requiere cambios de arquitectura bajo el modo Arquitecto
- **WHEN** el modelo concluye su análisis
- **THEN** retorna la propuesta y diseño en texto estructurado sin haber modificado ningún archivo del espacio de trabajo
