# Spec Delta: multi-api-provider

## MODIFIED Requirements

### Requirement: Configuración de proveedor y cliente unificado
El módulo llm_provider SHALL instanciar un cliente compatible con la API de OpenAI resolviendo dinámicamente la base_url y la api_key correspondientes al proveedor seleccionado o detectado, soportando proveedores locales (ollama, lmstudio, local, custom) sin requerir claves de API y permitiendo URLs base personalizadas.

#### Scenario: Selección automática de proveedor según entorno
- **GIVEN** que existe la variable de entorno GROQ_API_KEY pero ninguna otra clave
- **WHEN** se inicializa el adaptador sin especificar proveedor explícito
- **THEN** el adaptador selecciona automáticamente el proveedor Groq con su base_url predeterminada

#### Scenario: Selección explícita mediante parámetro
- **GIVEN** múltiples claves de API en el entorno
- **WHEN** se solicita explícitamente el proveedor 'gemini'
- **THEN** el adaptador configura la base_url correspondiente a Gemini y utiliza GEMINI_API_KEY

#### Scenario: Sobrescritura de endpoint con URL personalizada
- **GIVEN** una URL base configurada para un proveedor (ej. OLLAMA_BASE_URL=http://localhost:1234/v1)
- **WHEN** se resuelve la configuración del proveedor
- **THEN** el adaptador utiliza la URL personalizada en lugar del valor predeterminado permitiendo operar con cualquier puerto o servidor

#### Scenario: Uso de proveedor local sin clave de API
- **GIVEN** un proveedor local configurado ('ollama', 'lmstudio', 'local', 'custom' o base_url apuntando a localhost)
- **WHEN** se resuelve la configuración del proveedor sin variable de entorno de clave
- **THEN** el adaptador asigna una clave por defecto 'local' y no arroja error de autenticación

#### Scenario: Soporte de proveedores adicionales (DeepSeek, LM Studio)
- **GIVEN** una solicitud para utilizar un proveedor soportado ampliado (ej. 'deepseek' o 'lmstudio')
- **WHEN** se inicializa el adaptador
- **THEN** el cliente se conecta a la URL predeterminada o configurada del servicio con el modelo especificado
