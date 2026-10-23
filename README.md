# Harness Jarvis

Agente CLI autónomo para la terminal (estilo Claude Code) construido con arquitectura de Harness Multi-API.

## 🚀 Instalación en 1 Comando

Puedes instalar y registrar Jarvis en cualquier PC con Python 3.10 o superior:

### En Windows (CMD o doble clic):
Haz doble clic en `install.bat` o ejecútalo en la consola de comandos:
```cmd
install.bat
```

### En PowerShell:
```powershell
.\install.ps1
```

### Instalación manual estándar (Cualquier Sistema Operativo):
```bash
python -m pip install -e .
```

El instalador compilará los metadatos y registrará el comando global `jarvis` en tu terminal.

---

## 💻 Uso de la CLI

Una vez instalado, puedes invocar Jarvis desde cualquier carpeta o terminal:

### Modo interactivo (REPL)
```bash
jarvis
```

### Ejecución directa con prompt inicial
```bash
jarvis -p "Crea una función en Python para calcular números primos"
```

### Opciones de ejecución
```bash
jarvis --provider groq --model llama-3.3-70b-versatile
jarvis --provider gemini --model gemini-2.5-flash
jarvis --provider ollama --model qwen2.5-coder:7b
```

---

## ⚡ Comandos en la sesión interactiva

Dentro de la sesión interactiva de Jarvis puedes usar los siguientes comandos de barra oblicua:

- `/model <nombre>`: Cambia el modelo activo en caliente y lo recuerda para futuras sesiones (e.g., `/model gemini-2.5-flash`).
- `/key <proveedor> <api_key>`: Guarda y configura la clave de API para el proveedor indicado (e.g., `/key groq gsk_...`).
- `/cwd`: Muestra el directorio de trabajo activo y el resumen de archivos.
- `exit` o `quit`: Cierra la sesión del agente.

---

## 🛡️ Guardrails y Seguridad

Jarvis implementa medidas estrictas de seguridad:
- **Protección de credenciales**: Bloqueo absoluto de lectura y modificación de archivos `.env` y secretos.
- **Confinamiento de ruta**: Todas las operaciones de archivo se limitan al directorio de trabajo activo (`cwd`).
- **Confirmación humana interactiva**: Requiere aprobación explícita `[s/n]` antes de modificar archivos o ejecutar comandos en tu consola.

---

## 🧪 Pruebas Automatizadas

Para ejecutar la suite completa de pruebas unitarias:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
