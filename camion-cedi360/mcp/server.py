"""
CEDI 360 · Servidor MCP para supervisar Blender
==============================================
Habla con el puente que corre dentro de Blender (bridge_addon.py, puerto
9876) y expone herramientas para que el asistente pueda ver la escena,
ejecutar Python, renderizar y abrir el programa.

Configuración en .vscode/mcp.json:
    uv run --no-project --with mcp python camion-cedi360/mcp/server.py
"""

import json
import os
import socket
import subprocess
import time

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except Exception:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

HOST = "127.0.0.1"
PORT = 9876
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER_DIR = os.path.join(PROJECT_DIR, "blender")
RENDER_DIR = os.path.join(PROJECT_DIR, "render")
BLEND_FILE = os.path.join(BLENDER_DIR, "cedi360.blend")
BRIDGE = os.path.join(BLENDER_DIR, "bridge_addon.py")
ESTADO = os.path.join(PROJECT_DIR, "estado.txt")

BLENDER_CANDIDATES = [
    os.environ.get("BLENDER_EXE", ""),
    r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
]


def _blender_exe():
    for path in BLENDER_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError("No se encontró blender.exe. Define BLENDER_EXE.")


def _call(payload, timeout=120.0):
    payload = dict(payload)
    payload.setdefault("timeout", timeout)
    try:
        with socket.create_connection((HOST, PORT), timeout=3) as sock:
            sock.settimeout(timeout)
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            buffer = b""
            while b"\n" not in buffer:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buffer += chunk
    except (ConnectionRefusedError, socket.timeout, OSError) as exc:
        return {
            "ok": False,
            "error": "Sin conexión con Blender (%s). Abre Blender con blender_launch." % exc,
        }
    try:
        return json.loads(buffer.split(b"\n", 1)[0].decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": "Respuesta inválida del puente: %s (%r)" % (exc, buffer[:200])}


server = _Server(
    name="blender-cedi360",
    instructions=(
        "Supervisión del despiece isométrico del camión CEDI 360 en Blender 5.3. "
        "Usa blender_status para ver la escena, blender_exec para modelar o "
        "consultar, blender_render para imágenes de revisión y blender_launch si "
        "Blender no está abierto."
    ),
)


# --------------------------------------------------------------------------
# herramientas
# --------------------------------------------------------------------------
@server.tool()
def blender_status() -> dict:
    """Estado del puente y resumen de la escena abierta en Blender."""
    ping = _call({"cmd": "ping"}, timeout=10)
    if not ping.get("ok"):
        return ping
    scene = _call({"cmd": "scene"}, timeout=20)
    return {"ok": True, "ping": ping.get("result"), "scene": scene.get("result", scene)}


@server.tool()
def blender_exec(code: str, timeout: float = 120.0) -> dict:
    """Ejecuta Python dentro de Blender y devuelve resultado y stdout.

    Ejemplo: "bpy.data.objects.keys()" o un bloque con import/save.
    """
    return _call({"cmd": "exec", "code": code}, timeout=timeout)


@server.tool()
def blender_phase(fase: int) -> dict:
    """Aplica una fase de despiece (0 a 4) sobre MASTER_DESPIECE."""
    return _call({"cmd": "phase", "fase": int(fase)}, timeout=30)


@server.tool()
def blender_render(
    filepath: str = "",
    camera: str = "",
    width: int = 1600,
    height: int = 900,
    samples: int = 32,
    engine: str = "",
    freestyle: bool = True,
) -> dict:
    """Renderiza la cámara activa a PNG dentro de camion-cedi360/render."""
    if not filepath:
        filepath = os.path.join(RENDER_DIR, "render_%s.png" % time.strftime("%Y%m%d_%H%M%S"))
    payload = {
        "cmd": "render",
        "filepath": filepath,
        "width": width,
        "height": height,
        "samples": samples,
        "freestyle": bool(freestyle),
    }
    if camera:
        payload["camera"] = camera
    if engine:
        payload["engine"] = engine
    return _call(payload, timeout=600)


@server.tool()
def blender_viewport(filepath: str = "", width: int = 1600, height: int = 900) -> dict:
    """Captura rápida del viewport (sin render completo), útil para supervisar."""
    if not filepath:
        filepath = os.path.join(RENDER_DIR, "viewport_%s.png" % time.strftime("%Y%m%d_%H%M%S"))
    return _call({"cmd": "viewport", "filepath": filepath, "width": width, "height": height}, timeout=120)


@server.tool()
def blender_import(filepath: str) -> dict:
    """Importa un modelo glb/gltf/fbx/obj al proyecto (por ejemplo de Sketchfab)."""
    return _call({"cmd": "import", "filepath": filepath}, timeout=300)


@server.tool()
def blender_save(filepath: str = "") -> dict:
    """Guarda el archivo .blend del proyecto."""
    return _call({"cmd": "save", "filepath": filepath or BLEND_FILE}, timeout=120)


@server.tool()
def blender_launch(wait: float = 25.0) -> dict:
    """Abre Blender 5.3 con el puente cargado y espera a que responda."""
    exe = _blender_exe()
    args = [exe]
    if os.path.isfile(BLEND_FILE):
        args.append(BLEND_FILE)
    else:
        args.append("--factory-startup")
    args += ["--python", BRIDGE]
    subprocess.Popen(args, cwd=PROJECT_DIR, close_fds=True)
    deadline = time.time() + max(wait, 5)
    while time.time() < deadline:
        ping = _call({"cmd": "ping"}, timeout=3)
        if ping.get("ok"):
            size = os.path.getsize(BLEND_FILE) if os.path.isfile(BLEND_FILE) else 0
            return {"ok": True, "exe": exe, "file": BLEND_FILE if size else None, "ping": ping.get("result")}
        time.sleep(1.5)
    return {"ok": False, "error": "Blender se abrió pero el puente no respondió en %.0f s." % wait}


@server.tool()
def estado_leer() -> str:
    """Devuelve el contenido de estado.txt del proyecto."""
    if not os.path.isfile(ESTADO):
        return "No existe estado.txt"
    with open(ESTADO, "r", encoding="utf-8") as handle:
        return handle.read()


@server.tool()
def estado_bitacora(texto: str) -> dict:
    """Agrega una línea fechada a la bitácora de estado.txt."""
    if not os.path.isfile(ESTADO):
        return {"ok": False, "error": "No existe estado.txt"}
    stamp = time.strftime("%Y-%m-%d %H:%M")
    with open(ESTADO, "a", encoding="utf-8") as handle:
        handle.write("%s  %s\n" % (stamp, texto.strip()))
    return {"ok": True, "linea": "%s  %s" % (stamp, texto.strip())}


if __name__ == "__main__":
    server.run()
