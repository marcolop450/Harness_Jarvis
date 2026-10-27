"""Demostración opt-in con Ollama y comprobación de tool_calls reales.

Ejecutar desde la raíz: python -X utf8 -m scripts.mcp_demo --model qwen3.5:4b
Solo autoriza automáticamente la escritura del archivo demo-saludo.txt de esta
ejecución. No habilita autorización general ni modifica la política de la CLI.
"""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import tempfile

from harness.mcp_client import MCPManager, PROJECT_ROOT
from main import run_turn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:4b")
    args = parser.parse_args()
    demo = PROJECT_ROOT / ".mcp-demo"
    demo.mkdir(exist_ok=True)
    evidence = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "modelo": args.model,
                "versiones": {name: version(name) for name in ("mcp", "mcp-server-fetch", "mcp-server-git")}, "turnos": []}
    with tempfile.TemporaryDirectory(prefix="ollama-", dir=demo) as folder:
        target = Path(folder) / "demo-saludo.txt"
        approvals = []
        def approve(description, details):
            allowed = details == f"Ruta: {target}"
            approvals.append({"accion": description, "permitido": allowed})
            print(f"[DEMO autorización limitada] {'s' if allowed else 'n'}", flush=True)
            return allowed
        events = []
        def event(server, tool, state):
            events.append({"servidor": server, "herramienta": tool, "estado": state})
            print(f"[MCP {server}/{tool}] {state}", flush=True)
        with MCPManager(PROJECT_ROOT, confirm_fn=approve, on_event=event) as manager:
            evidence["estado_inicial"] = manager.report()
            print(evidence["estado_inicial"], flush=True)
            assert all(conn.status == "conectado" for conn in manager.connections.values())
            prompts = [
                ("fetch", "Usa obligatoriamente mcp_fetch__fetch para consultar https://example.com con max_length 1000. Resume su contenido en una oración. No uses otras herramientas."),
                ("git", f"Usa obligatoriamente mcp_git__git_log con repo_path {PROJECT_ROOT} y max_count 3. Resume los tres últimos commits brevemente. No uses otras herramientas."),
                ("filesystem", f"Usa mcp_filesystem__write_file para crear {target} con el contenido exacto Hola MCP. Después usa mcp_filesystem__read_text_file para leerlo y confirma su contenido. No uses herramientas nativas ni comandos.")]
            for server, prompt in prompts:
                events.clear()
                print(f"\n[DEMO turno {server}]", flush=True)
                reply, history = run_turn(manager, prompt=prompt,
                    system_prompt=f"Eres Jarvis. Ejecuta las herramientas solicitadas antes de responder. CWD: {PROJECT_ROOT}.",
                    provider_name="ollama", model=args.model, base_dir=PROJECT_ROOT)
                print(reply, flush=True)
                record = {"servidor": server, "eventos": list(events), "respuesta": reply,
                          "tool_calls": [c['function']['name'] for m in history for c in m.get('tool_calls', [])],
                          "resultados": [m['content'] for m in history if m.get('role') == 'tool']}
                evidence["turnos"].append(record)
                assert any(e['servidor'] == server and e['estado'] == 'ok' for e in events), record
                if server == "filesystem":
                    assert target.read_text(encoding="utf-8").strip() == "Hola MCP"
                    assert any(e['herramienta'] == 'read_text_file' and e['estado'] == 'ok' for e in events)
        evidence["autorizaciones"] = approvals
        evidence["hilos_cerrados"] = all(not c.thread.is_alive() for c in manager.connections.values())
        assert evidence["hilos_cerrados"]
    path = demo / "resultado-ollama.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidencia guardada: {path}", flush=True)


if __name__ == "__main__":
    main()
