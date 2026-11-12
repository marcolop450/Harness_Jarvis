# agent-loop Specification

## Purpose
Controla el ciclo de ejecución reactivo del agente mediante un bucle while con límite estricto de pasos para evitar ejecuciones descontroladas o consumo excesivo de tokens.

## Requirements

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

### Requirement: Registro de historial de conversación
El bucle SHALL mantener un historial de mensajes ordenado e inyectar proactivamente el contexto del entorno (SO, CWD, Git, JARVIS.md) en el System Prompt, aplicando Observation Masking sobre una copia efímera para ahorrar tokens de contexto.

#### Scenario: Acumulación de contexto durante el ciclo
- **GIVEN** un mensaje entrante del usuario
- **WHEN** el bucle inicia la interacción
- **THEN** añade el mensaje del usuario y conserva el historial durante todos los pasos del turno

#### Scenario: Inyección proactiva de contexto de entorno
- **GIVEN** el inicio de un turno en el bucle del agente
- **WHEN** se construye el prompt del sistema
- **THEN** se inyectan automáticamente el SO, la ruta CWD, la lista superficial de archivos, el estado de Git y las reglas de JARVIS.md o AGENT.md

#### Scenario: Enmascaramiento de observaciones remotas (Observation Masking)
- **GIVEN** una conversación con llamadas a herramientas anteriores a los últimos 4 pasos
- **WHEN** se prepara el payload para el modelo de lenguaje
- **THEN** se genera una copia efímera donde las salidas antiguas extensas se reemplazan por resúmenes breves sin alterar el historial persistente en memoria

### Requirement: Despacho seguro de herramientas en el bucle
El bucle de ejecución SHALL despachar cada tool_call emitido por el modelo a través de los guardrails de seguridad e inyectar cualquier error operativo, de sintaxis o cancelación interactiva como respuesta fáctica de rol 'tool' para obligar al modelo a anclarse en la verdad real del entorno (Anti-Hallucination Circuit).

#### Scenario: Interceptación y ejecución de herramienta permitida
- **GIVEN** un tool_call emitido por el modelo en el paso N
- **WHEN** los guardrails validan la llamada y se ejecuta la herramienta
- **THEN** el resultado (o confirmación) se añade como mensaje de rol 'tool' y el ciclo avanza al siguiente paso

#### Scenario: Bucle de auto-reparación ante fallo de herramienta
- **GIVEN** una herramienta que falla por sintaxis, archivo no encontrado o texto no coincidente
- **WHEN** la herramienta retorna la descripción del fallo
- **THEN** el bucle inyecta el error instructivo como mensaje de rol 'tool' permitiendo al modelo autocorregir su acción en el paso siguiente

#### Scenario: Intercepción de cancelación interactiva humana (HITL)
- **GIVEN** una herramienta de escritura o consola que requiere confirmación y el usuario rechaza la operación o presiona Enter sin autorizar
- **WHEN** la herramienta retorna la cancelación
- **THEN** el bucle inyecta un mensaje explícito de cancelación con prohibición terminante de asumir la creación de archivos, impidiendo que el modelo declare el paso como completado

### Requirement: Anclaje Fáctico Post-Ejecución de Herramientas
El bucle de ejecución SHALL verificar el resultado reportado por las herramientas de modificación de disco y comandos de creación antes de permitir que el modelo cierre el turno como exitoso.

#### Scenario: Rechazo de afirmación falsa tras herramienta cancelada
- **GIVEN** un turno donde una herramienta de creación o comando fue denegada por el usuario
- **WHEN** el modelo emite su respuesta final de texto
- **THEN** el sistema asegura que la conversación registre el estado cancelado y no promueva estados alucinados en turnos futuros

### Requirement: Medición y reporte del tiempo de respuesta
El bucle de ejecución SHALL cronometrar la duración de cada turno completo del agente y reportar el tiempo transcurrido en segundos o milisegundos junto a la respuesta final.

#### Scenario: Visualización del tiempo de ejecución en turno completado
- **GIVEN** un turno interactivo del usuario
- **WHEN** el ciclo de agente completa la respuesta final
- **THEN** se imprime una línea informativa indicando el tiempo transcurrido (e.g., '[⏱️ 2.34s]')

### Requirement: Subagente especializado con contexto aislado
El sistema SHALL proveer la capacidad de ejecutar un subagente de investigación aislado que recibe una tarea específica con un contexto limpio y devuelve un resumen conciso al orquestador principal, evitando contaminar la ventana de tokens del contexto padre.

#### Scenario: Ejecución de subagente para exploración de archivos
- **GIVEN** una instrucción compleja o comando que requiere investigación detallada
- **WHEN** se invoca el subagente de investigación
- **THEN** el subagente ejecuta en su propio contexto independiente con herramientas de solo lectura y retorna exclusivamente un sumario ejecutivo al bucle principal

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

### Requirement: Directiva y Salvaguarda de Acción Inmediata (Bias for Action)
El bucle de ejecución SHALL exigir la invocación inmediata de herramientas de acción ante solicitudes de creación, modificación o inspección de archivos, detectando cuando un modelo emite promesas conversacionales vacías sin llamadas a herramientas e induciendo su ejecución.

#### Scenario: Detección y corrección de promesa conversacional sin herramientas
- **GIVEN** un turno donde el usuario solicitó crear, editar o mejorar un archivo de código
- **WHEN** el modelo genera únicamente una respuesta textual de promesa como 'Entendido, voy a modificar el archivo' sin emitir ningún tool_call
- **THEN** el bucle de ejecución intercepta la omisión, inyecta un aviso correctivo exigiendo la ejecución inmediata de la herramienta y continúa el turno para aplicar los cambios reales en disco
