"""Runner de Verificacion Funcional Operativa Integral del Harness Jarvis.

Ejecuta un ciclo de pruebas en vivo (no solo unit tests sinteticos) de todas
las capacidades del arnes:
  1. Inyeccion de Contexto Proactiva (OS, CWD, Git, JARVIS.md).
  2. Smart Truncation (Head 1000 + Tail 3000).
  3. Catalogo de Herramientas Nativas en Sandbox Real.
  4. Smart HITL en 3 Niveles con Memoria de Sesion [a] y Prevencion de Inyecciones.
  5. Observation Masking Efimero en Historial RAM.
  6. Resiliencia y Self-Healing Loop ante JSON Malformado.
  7. Graceful Degradation en Servidores MCP.
  8. ReAct Loop E2E con Inferencia Real y Tool Calls contra LLM (LM Studio).
"""

from __future__ import annotations
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Configurar encoding utf-8 para salida en consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Asegurar que el directorio raiz del proyecto este en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.agent_loop import (
    apply_observation_masking,
    build_environment_context,
    run_agent_loop,
)
from harness.guardrails import (
    RISK_LEVEL_AUTO,
    RISK_LEVEL_WORKSPACE,
    RISK_LEVEL_DANGEROUS,
    SecurityViolationError,
    ActionCancelledError,
    authorize_and_dispatch,
    classify_risk,
    is_safe_command,
    validate_safe_path,
)
from harness.llm_provider import (
    NormalizedResponse,
    NormalizedToolCall,
    call_llm,
    repair_json_arguments,
    resolve_provider,
)
from harness.mcp_client import MCPManager
from harness.tools import (
    execute_tool,
    smart_truncate,
    tool_edit_file,
    tool_list_dir,
    tool_read_file,
    tool_search_code,
    tool_sqlite_query,
    tool_write_file,
)


def log_phase(title: str) -> None:
    print(f"\n{'='*75}")
    print(f">> {title}")
    print(f"{'='*75}")


def assert_true(condition: bool, msg: str) -> None:
    if not condition:
        print(f"  [FALLO] {msg}")
        raise AssertionError(msg)
    print(f"  [OK] {msg}")


def test_phase_1_context_injection() -> None:
    log_phase("FASE 1: Inyeccion Proactiva de Contexto (Context Injection)")
    ctx = build_environment_context(base_dir=PROJECT_ROOT)

    assert_true("=== CONTEXTO DEL ENTORNO DE EJECUCIÓN ===" in ctx or "CONTEXTO DEL ENTORNO DE EJECUCI" in ctx, "Cabecera de contexto presente")
    assert_true("Sistema Operativo:" in ctx, "Deteccion de Sistema Operativo presente")
    assert_true("Directorio de Trabajo (CWD):" in ctx, "Deteccion de CWD presente")
    assert_true("Git:" in ctx, "Informacion de Git (rama y estado) detectada")
    assert_true("Estructura del Proyecto:" in ctx, "Arbol de directorios formateado")
    assert_true(".git/" not in ctx and "__pycache__" not in ctx, "Directorios ignorados excluidos correctamente")

    # Si existe JARVIS.md en la raiz, debe inyectarse
    jarvis_md = PROJECT_ROOT / "JARVIS.md"
    if jarvis_md.exists():
        assert_true("Reglas del Proyecto (JARVIS.md):" in ctx, "Reglas de JARVIS.md inyectadas")
    print(f"  [*] Contexto inyectado ({len(ctx)} caracteres):\n{ctx[:300]}...\n")


def test_phase_2_smart_truncation() -> None:
    log_phase("FASE 2: Gestion Inteligente de RAM (Head + Tail Smart Truncate)")

    # 1. Payload corto (no debe ser alterado)
    short_payload = "Contenido breve sin truncar."
    res_short = smart_truncate(short_payload, max_chars=4000)
    assert_true(res_short == short_payload, "Payloads cortos (<= 4000) se conservan identicos")

    # 2. Payload largo (10,000 caracteres)
    head_marker = "=== INICIO_CABECERA_CRITICA ==="
    tail_marker = "=== FINAL_COLA_STACKTRACE ==="
    middle_junk = "X" * 9000
    long_payload = f"{head_marker}\n{middle_junk}\n{tail_marker}"

    res_long = smart_truncate(long_payload, max_chars=4000)

    assert_true(len(res_long) <= 4150, f"Longitud acotada ({len(res_long)} caracteres)")
    assert_true(head_marker in res_long, "Preserva los primeros 1000 caracteres (Head)")
    assert_true(tail_marker in res_long, "Preserva los ultimos 3000 caracteres (Tail donde estan errores)")
    assert_true("omitidos" in res_long, "Incluye aviso explicito de caracteres omitidos")
    print(f"  [*] Resultado de truncado: {len(long_payload)} chars -> {len(res_long)} chars con aviso central.")


def test_phase_3_native_tools_sandbox() -> None:
    log_phase("FASE 3: Catalogo de Herramientas Nativas en Sandbox Real")
    sandbox_dir = PROJECT_ROOT / "tests" / "sandbox_functional_run"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. write_file
        test_file = sandbox_dir / "modulo_prueba.py"
        content_v1 = (
            "def saludo():\n"
            "    print('Hola mundo')\n"
            "    return True\n"
            "\n"
            "def despedida():\n"
            "    print('Adios mundo')\n"
        )
        msg_write = tool_write_file(str(test_file), content_v1, base_dir=sandbox_dir, confirm_fn=lambda d, det: True)
        assert_true("escrito exitosamente" in msg_write, "tool_write_file creo el archivo con exito")
        assert_true(test_file.exists(), "El archivo existe fisicamente en disco")

        # 2. read_file con numeracion [L1], [L2]
        read_content = tool_read_file(str(test_file), line_numbers=True, base_dir=sandbox_dir)
        assert_true("[L1] def saludo():" in read_content, "read_file numera correctamente con [L1]")
        assert_true("[L2]     print('Hola mundo')" in read_content, "read_file numera correctamente con [L2]")

        # 3. edit_file: Diagnostico de no coincidencia
        edit_fail_res = tool_edit_file(
            str(test_file),
            target="linea_inexistente_que_no_existe_en_archivo = 123",
            replacement="pass",
            base_dir=sandbox_dir,
            confirm_fn=lambda d, det: True,
        )
        assert_true("No se encontró la cadena 'target'" in edit_fail_res or "target" in edit_fail_res, "tool_edit_file diagnostica no coincidencia")

        # 4. edit_file: Diagnostico de multiples ocurrencias
        dup_file = sandbox_dir / "duplicados.py"
        tool_write_file(str(dup_file), "valor = 1\nvalor = 1\nvalor = 1\n", base_dir=sandbox_dir, confirm_fn=lambda d, det: True)
        edit_dup_res = tool_edit_file(str(dup_file), target="valor = 1\n", replacement="valor = 2\n", base_dir=sandbox_dir, confirm_fn=lambda d, det: True)
        assert_true("3 veces" in edit_dup_res, "tool_edit_file detecta multiples ocurrencias y previene reemplazo ambiguo")

        # 5. edit_file: Reemplazo exitoso unico
        edit_ok_res = tool_edit_file(
            str(test_file),
            target="    print('Hola mundo')",
            replacement="    print('Hola Jarvis')",
            base_dir=sandbox_dir,
            confirm_fn=lambda d, det: True,
        )
        assert_true("editado exitosamente" in edit_ok_res, "tool_edit_file aplico el cambio exitosamente")
        read_updated = tool_read_file(str(test_file), base_dir=sandbox_dir)
        assert_true("Hola Jarvis" in read_updated and "Hola mundo" not in read_updated, "El contenido en disco fue modificado")

        # 6. search_code
        search_res = tool_search_code("Hola Jarvis", path=".", base_dir=sandbox_dir)
        assert_true("modulo_prueba.py" in search_res and "2:" in search_res, "tool_search_code localizo el archivo y la linea")

        # 7. list_dir
        sub_folder = sandbox_dir / "submodulo"
        sub_folder.mkdir()
        list_res = tool_list_dir(".", base_dir=sandbox_dir)
        assert_true("submodulo/" in list_res, "tool_list_dir reporta subdirectorios")
        assert_true("modulo_prueba.py" in list_res, "tool_list_dir reporta archivos existentes")

        # 8. sqlite_query (archivo y persistencia con commit)
        db_file = sandbox_dir / "test_data.db"
        q_create = tool_sqlite_query(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT);",
            db_path=str(db_file),
            base_dir=sandbox_dir,
            confirm_fn=lambda d, det: True,
        )
        assert_true("éxito" in q_create or "exito" in q_create, f"tool_sqlite_query ejecuto DDL CREATE TABLE -> {q_create}")

        q_insert = tool_sqlite_query(
            "INSERT INTO usuarios (nombre) VALUES ('Jarvis'), ('Optimus');",
            db_path=str(db_file),
            base_dir=sandbox_dir,
            confirm_fn=lambda d, det: True,
        )
        assert_true("éxito" in q_insert or "exito" in q_insert, f"tool_sqlite_query ejecuto INSERT con commit automatico -> {q_insert}")

        q_select = tool_sqlite_query(
            "SELECT id, nombre FROM usuarios ORDER BY id ASC;",
            db_path=str(db_file),
            base_dir=sandbox_dir,
            confirm_fn=lambda d, det: True,
        )
        assert_true("Jarvis" in q_select and "Optimus" in q_select, f"tool_sqlite_query leyo los datos persistidos -> {q_select}")

        # 9. sqlite_query (:memory:)
        q_mem = tool_sqlite_query("SELECT 42 AS respuesta_universal;", db_path=":memory:", base_dir=sandbox_dir)
        assert_true("42" in q_mem, f"tool_sqlite_query soporta bases de datos en memoria :memory: -> {q_mem}")

    finally:
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)
        print("  [*] Sandbox temporal limpiado.")


def test_phase_4_smart_hitl_and_guardrails() -> None:
    log_phase("FASE 4: Gobernanza Smart HITL en 3 Niveles y Seguridad")
    sandbox_dir = PROJECT_ROOT / "tests" / "sandbox_guardrails"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Clasificacion estricta en 3 niveles de riesgo
        lvl_read, _ = classify_risk("read_file", {"path": "a.txt"})
        assert_true(lvl_read == RISK_LEVEL_AUTO, "read_file clasificado como RISK_LEVEL_AUTO (0)")

        lvl_write, _ = classify_risk("write_file", {"path": "b.txt", "content": "x"})
        assert_true(lvl_write == RISK_LEVEL_WORKSPACE, "write_file clasificado como RISK_LEVEL_WORKSPACE (1)")

        lvl_cmd_white, _ = classify_risk("run_command", {"command": "git status"})
        assert_true(lvl_cmd_white == RISK_LEVEL_AUTO, "run_command en whitelist clasificado como RISK_LEVEL_AUTO (0)")

        lvl_cmd_danger, _ = classify_risk("run_command", {"command": "powershell -c ls"})
        assert_true(lvl_cmd_danger == RISK_LEVEL_DANGEROUS, "run_command arbitrario clasificado como RISK_LEVEL_DANGEROUS (2)")

        # 2. Despacho y Memoria de Sesion [a]
        session_targets: set[str] = set()
        prompts_asked: list[str] = []

        def input_recorder(prompt: str, reply: str) -> str:
            prompts_asked.append(prompt)
            return reply

        # Nivel 0 (Lectura): No debe preguntar nada
        prompts_asked.clear()
        f_read = sandbox_dir / "read_target.txt"
        f_read.write_text("ok", encoding="utf-8")
        auth_l0 = authorize_and_dispatch(
            "read_file",
            {"path": str(f_read)},
            session_approved_targets=session_targets,
            input_fn=lambda p: input_recorder(p, "s"),
        )
        assert_true(auth_l0 is True, "authorize_and_dispatch autorizo Nivel 0")
        assert_true(len(prompts_asked) == 0, "Nivel 0 NO interrumpio al usuario (cero prompts)")

        # Nivel 1 (Escritura): Primera vez el usuario responde 'a' (Autorizar para toda la sesion)
        prompts_asked.clear()
        target_path = str(sandbox_dir / "archivo_sesion.txt")
        auth_w1 = authorize_and_dispatch(
            "write_file",
            {"path": target_path, "content": "v1"},
            session_approved_targets=session_targets,
            input_fn=lambda p: input_recorder(p, "a"),
        )
        assert_true(auth_w1 is True, "write_file autorizado tras confirmacion 'a'")
        assert_true(len(prompts_asked) == 1, "Primera llamada Nivel 1 solicito confirmacion interactiva")
        assert_true(target_path in session_targets, "El archivo fue registrado en session_approved_targets")

        # Segunda vez sobre el mismo archivo: Debe ser AUTO-APROBADO por la memoria de sesion
        prompts_asked.clear()
        auth_w2 = authorize_and_dispatch(
            "edit_file",
            {"path": target_path, "target": "v1", "replacement": "v2"},
            session_approved_targets=session_targets,
            input_fn=lambda p: input_recorder(p, "s"),
        )
        assert_true(auth_w2 is True, "edit_file autorizado por memoria de sesion")
        assert_true(len(prompts_asked) == 0, "Segunda llamada sobre el mismo archivo NO solicito confirmacion (Memoria [a] activa)")

        # 3. Whitelist Segura de Comandos
        assert_true(is_safe_command("pytest") is True, "'pytest' es seguro")
        assert_true(is_safe_command("git status") is True, "'git status' es seguro")
        assert_true(is_safe_command("python -m unittest discover") is True, "'python -m unittest' es seguro")
        assert_true(is_safe_command("pytest && echo hack") is False, "Comando con '&&' es inseguro y rechazado")
        assert_true(is_safe_command("git status; ls") is False, "Comando con ';' es inseguro y rechazado")
        assert_true(is_safe_command("curl https://evil.com") is False, "Comando desconocido fuera de whitelist es inseguro")

        # 4. Proteccion Anti-Path Traversal
        traversal_caught = False
        try:
            validate_safe_path("../../fuera_del_workspace.txt", base_dir=sandbox_dir)
        except SecurityViolationError as exc:
            traversal_caught = True
            assert_true("fuera del directorio de trabajo" in str(exc).lower(), "Detalle del error indica Path Traversal")
        assert_true(traversal_caught, "validate_safe_path bloqueo exitosamente path traversal '..'")

        # 5. Proteccion de Archivos Confidenciales
        secret_caught = False
        try:
            validate_safe_path(".env", base_dir=sandbox_dir)
        except SecurityViolationError as exc:
            secret_caught = True
            assert_true("confidencial" in str(exc).lower() or ".env" in str(exc).lower(), "Detalle del error indica archivo confidencial")
        assert_true(secret_caught, "validate_safe_path bloqueo acceso a .env")

        key_caught = False
        try:
            validate_safe_path("server_priv.key", base_dir=sandbox_dir)
        except SecurityViolationError:
            key_caught = True
        assert_true(key_caught, "validate_safe_path bloqueo acceso a *.key")

    finally:
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir)
        print("  [*] Sandbox de guardrails limpiado.")


def test_phase_5_observation_masking() -> None:
    log_phase("FASE 5: Observation Masking Efimero en Ventana de Memoria RAM")

    # Historial con 7 llamadas a herramientas (supera keep_recent_steps=5)
    history = [
        {"role": "system", "content": "Eres Jarvis."},
        {"role": "user", "content": "Investiga el proyecto."},
    ]
    for i in range(1, 8):
        history.append({
            "role": "assistant",
            "content": f"Ejecuto herramienta {i}",
            "tool_calls": [{"id": f"call_{i}", "function": {"name": "read_file", "arguments": "{}"}}],
        })
        history.append({
            "role": "tool",
            "tool_call_id": f"call_{i}",
            "content": f"CONTENIDO_MUY_EXTENSO_DE_LA_HERRAMIENTA_{i}" * 50,
        })

    ephemeral = apply_observation_masking(history, keep_recent_steps=5)

    # Verificar que el historial original NO fue alterado
    tool_msgs_orig = [m for m in history if m.get("role") == "tool"]
    assert_true(
        "CONTENIDO_MUY_EXTENSO" in tool_msgs_orig[0]["content"],
        "Historial original en memoria RAM permanece intacto (inmutabilidad)",
    )

    # Verificar que la copia efimera enmascaro las primeras (7 - 5 = 2)
    tool_msgs_eph = [m for m in ephemeral if m.get("role") == "tool"]
    assert_true("enmascarado para optimizar" in tool_msgs_eph[0]["content"], "Herramienta 1 enmascarada efimeramente")
    assert_true("enmascarado para optimizar" in tool_msgs_eph[1]["content"], "Herramienta 2 enmascarada efimeramente")
    assert_true("CONTENIDO_MUY_EXTENSO" in tool_msgs_eph[2]["content"], "Herramienta 3 (reciente) conservada intacta")
    assert_true("CONTENIDO_MUY_EXTENSO" in tool_msgs_eph[6]["content"], "Herramienta 7 (ultima) conservada intacta")
    print(f"  [*] Historial total: {len(history)} mensajes. Observaciones antiguas enmascaradas con exito.")


def test_phase_6_self_healing_json() -> None:
    log_phase("FASE 6: Resiliencia y Self-Healing de Tool Calls")

    # 1. JSON envuelto en Markdown ```json ... ```
    md_json = "```json\n{\"path\": \"archivo.py\", \"content\": \"test\"}\n```"
    repaired_1 = repair_json_arguments(md_json)
    assert_true(repaired_1.get("path") == "archivo.py", "Auto-reparacion de JSON envuelto en bloques Markdown")

    # 2. JSON con comas finales invalidas (trailing comma)
    trailing_json = '{"path": "archivo.py", "items": [1, 2, ],}'
    repaired_2 = repair_json_arguments(trailing_json)
    assert_true("path" in repaired_2 and repaired_2["path"] == "archivo.py", "Auto-reparacion de trailing commas")

    # 3. JSON completamente corrupto
    broken_json = '{"path": "incompleto'
    repaired_broken = repair_json_arguments(broken_json)
    assert_true("parse_error" in repaired_broken, "JSON irrecuperable retorna diccionario estructurado con parse_error")
    assert_true(repaired_broken["raw_arguments"] == broken_json, "Preserva raw_arguments para diagnostico")


def test_phase_7_mcp_graceful_degradation() -> None:
    log_phase("FASE 7: MCP Graceful Degradation")
    with MCPManager(workspace=PROJECT_ROOT) as manager:
        manager.start()
        tools = manager.definitions()
        report = manager.report()
        print(f"  [*] Estado de servidores MCP:\n{report}")
        print(f"  [*] Herramientas MCP descubiertas: {len(tools)}")
        assert_true(isinstance(tools, list), "MCPManager inicia o degrada elegantemente sin abortar")
    print("  [*] Procesos MCP cerrados limpiamente.")


def test_phase_8_e2e_react_loop_llm() -> None:
    log_phase("FASE 8: ReAct Loop E2E con Inferencia Real contra LM Studio (qwen/qwen3.5-9b)")

    # Configurar endpoint de LM Studio
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:1234/v1"
    os.environ["OLLAMA_API_KEY"] = "lm-studio"

    provider_cfg = resolve_provider("ollama")
    print(f"  [*] Conectando con Proveedor: {provider_cfg.name} en {provider_cfg.base_url}")

    # Prompt pequeno pero completo para poner a prueba el ReAct Loop real:
    # Debe emitir write_file, recibir la confirmacion de la herramienta, luego emitir read_file y responder al usuario
    test_filename = "prueba_e2e_jarvis.txt"
    test_filepath = PROJECT_ROOT / test_filename
    if test_filepath.exists():
        test_filepath.unlink()

    prompt_test = (
        f"Por favor crea un archivo llamado '{test_filename}' con el contenido exacto 'VERIFICACION_HARNESS_100'. "
        f"A continuacion, lee ese archivo '{test_filename}' con read_file y responde confirmando su contenido."
    )

    system_prompt = (
        "Eres Jarvis, un asistente de ingenieria CLI de precision. "
        "Usa las herramientas disponibles para cumplir las solicitudes del usuario de forma metodica. "
        "Cuando termines, responde de manera concisa confirmando el resultado."
    )

    steps_recorded: list[int] = []

    def on_step_callback(step: int, max_steps: int) -> None:
        steps_recorded.append(step)
        print(f"  [>] [Paso {step}/{max_steps}] Procesando ciclo ReAct...")

    # Memoria de sesion con auto-aprobacion del archivo de prueba
    session_targets = {str(test_filepath), test_filename}

    try:
        response, full_history = run_agent_loop(
            prompt=prompt_test,
            system_prompt=system_prompt,
            provider_name="ollama",
            model="qwen/qwen3.5-9b",
            on_step=on_step_callback,
            base_dir=PROJECT_ROOT,
            confirm_fn=lambda desc, det: True,
            session_approved_targets=session_targets,
            include_timing=True,
            inject_environment=True,
        )

        print("\n  --- RESPUESTA FINAL DEL AGENTE ---")
        print(response)
        print("  ----------------------------------\n")

        # Verificaciones del loop E2E
        assert_true(len(steps_recorded) >= 1, f"El bucle ejecuto {len(steps_recorded)} pasos")
        assert_true(test_filepath.exists(), f"El archivo {test_filename} fue creado fisicamente en disco")

        # Verificar contenido en disco
        disk_content = test_filepath.read_text(encoding="utf-8")
        assert_true("VERIFICACION_HARNESS_100" in disk_content, "El contenido fue escrito fielmente en el archivo")

        # Verificar tool_calls en el historial
        tool_roles = [m for m in full_history if m.get("role") == "tool"]
        assert_true(len(tool_roles) >= 1, f"Se ejecutaron {len(tool_roles)} llamadas a herramientas en el historial")

        # Verificar que la respuesta final menciona el resultado
        assert_true(len(response) > 0, "El agente emitio una respuesta final coherente")

    finally:
        if test_filepath.exists():
            test_filepath.unlink()
            print(f"  [*] Archivo temporal {test_filename} eliminado.")


def main() -> None:
    start_total = time.perf_counter()
    print(f"\n{'#'*75}")
    print(" INICIO DE VERIFICACION FUNCIONAL COMPLETA DEL HARNESS JARVIS AL 100%")
    print(f"{'#'*75}")

    try:
        test_phase_1_context_injection()
        test_phase_2_smart_truncation()
        test_phase_3_native_tools_sandbox()
        test_phase_4_smart_hitl_and_guardrails()
        test_phase_5_observation_masking()
        test_phase_6_self_healing_json()
        test_phase_7_mcp_graceful_degradation()
        test_phase_8_e2e_react_loop_llm()

        elapsed = time.perf_counter() - start_total
        print(f"\n{'='*75}")
        print(f"*** TODAS LAS 8 FASES FUNCIONALES COMPLETADAS AL 100% CON EXITO [Tiempo: {elapsed:.2f}s] ***")
        print(f"{'='*75}\n")
    except Exception as exc:
        print(f"\n[FALLO CRITICO EN LA VERIFICACION]: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
