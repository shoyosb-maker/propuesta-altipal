"""
CEDI 360 · Puente de supervisión dentro de Blender
==================================================
Escucha en 127.0.0.1:9876 y ejecuta comandos que llegan del servidor MCP
(o de cualquier cliente que hable el mismo protocolo: una línea JSON por
petición y una línea JSON por respuesta).

Uso:
    blender.exe --python bridge_addon.py

No depende de addons instalados: se puede lanzar con -P/--python o instalar
como addon y activarlo. Las peticiones se ejecutan en el hilo principal con
bpy.app.timers, que es el único lugar seguro para tocar la escena.
"""

import bpy
import contextlib
import io
import json
import os
import queue
import socket
import threading
import traceback

HOST = "127.0.0.1"
PORT = 9876
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_DIR = os.path.join(PROJECT_DIR, "render")

_QUEUE = queue.Queue()
_STATE = {"server": None, "timer": None, "port": None}


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------
def _jsonable(value):
    try:
        json.dumps(value)
        return value
    except Exception:
        return repr(value)


def _scene_summary():
    scene = bpy.context.scene
    objs = list(bpy.data.objects)
    return {
        "blender": bpy.app.version_string,
        "file": bpy.data.filepath,
        "scene": scene.name,
        "frame": scene.frame_current,
        "engine": scene.render.engine,
        "camera": scene.camera.name if scene.camera else None,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
        "objects": len(objs),
        "meshes": sum(1 for o in objs if o.type == "MESH"),
        "empties": sum(1 for o in objs if o.type == "EMPTY"),
        "collections": [c.name for c in bpy.data.collections],
        "materials": [m.name for m in bpy.data.materials],
        "master": _master_state(),
    }


def _master_state():
    master = bpy.data.objects.get("MASTER_DESPIECE")
    if not master:
        return None
    return {
        "fase": master.get("fase", None),
        "props": {f"p{i}": master.get(f"p{i}", None) for i in range(8)},
    }


def _exec_code(code, filename=None):
    """Ejecuta código en el contexto de Blender y captura stdout."""
    scene = bpy.context.scene
    namespace = {
        "__name__": "__main__" if filename else "__blender_bridge__",
        "__file__": filename or os.path.join(PROJECT_DIR, "blender", "<mcp>"),
        "bpy": bpy,
        "scene": scene,
        "C": bpy.context,
        "D": bpy.data,
        "PROJECT_DIR": PROJECT_DIR,
        "RENDER_DIR": RENDER_DIR,
    }
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            try:
                value = eval(code, namespace)
                result = _jsonable(value)
            except SyntaxError:
                exec(compile(code, "<mcp>", "exec"), namespace)
                result = None
        except Exception:
            return {
                "ok": False,
                "error": traceback.format_exc(),
                "stdout": buffer.getvalue(),
            }
    return {"ok": True, "result": result, "stdout": buffer.getvalue()}


def _ensure_dir(path):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)


def _set_engine(scene):
    """Blender 5.x usa BLENDER_EEVEE; versiones anteriores usan BLENDER_EEVEE_NEXT."""
    for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = candidate
            return candidate
        except Exception:
            continue
    return scene.render.engine


def _render(params):
    scene = bpy.context.scene
    filepath = params.get("filepath") or os.path.join(RENDER_DIR, "preview.png")
    filepath = os.path.abspath(filepath)
    _ensure_dir(filepath)

    camera = params.get("camera")
    if camera:
        cam = bpy.data.objects.get(camera)
        if cam:
            scene.camera = cam

    engine = params.get("engine")
    if engine:
        try:
            scene.render.engine = engine
        except Exception:
            _set_engine(scene)
    else:
        _set_engine(scene)

    scene.render.resolution_x = int(params.get("width", scene.render.resolution_x))
    scene.render.resolution_y = int(params.get("height", scene.render.resolution_y))
    scene.render.resolution_percentage = int(params.get("percentage", 100))
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = bool(params.get("transparent", False))

    if "samples" in params and hasattr(scene, "eevee"):
        try:
            scene.eevee.taa_render_samples = int(params["samples"])
        except Exception:
            pass

    if params.get("freestyle") and hasattr(scene.render, "use_freestyle"):
        scene.render.use_freestyle = True

    bpy.ops.render.render(write_still=True)
    return {"ok": True, "filepath": filepath}


def _viewport(params):
    """Captura del viewport (rápida, útil para supervisar mientras se modela)."""
    filepath = os.path.abspath(params.get("filepath") or os.path.join(RENDER_DIR, "viewport.png"))
    _ensure_dir(filepath)
    scene = bpy.context.scene
    if "width" in params:
        scene.render.resolution_x = int(params["width"])
    if "height" in params:
        scene.render.resolution_y = int(params["height"])
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = "PNG"

    window = bpy.context.window
    screen = window.screen if window else None
    area = None
    if screen:
        for candidate in screen.areas:
            if candidate.type == "VIEW_3D":
                area = candidate
                break
    if area is None:
        return {"ok": False, "error": "No hay viewport 3D disponible (¿Blender en modo background?)"}

    with bpy.context.temp_override(window=window, screen=screen, area=area):
        bpy.ops.render.opengl(write_still=True, view_context=True)
    return {"ok": True, "filepath": filepath}


def _save(params):
    filepath = os.path.abspath(params.get("filepath") or bpy.data.filepath or
                               os.path.join(PROJECT_DIR, "blender", "cedi360.blend"))
    _ensure_dir(filepath)
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    return {"ok": True, "filepath": filepath}


def _open_file(params):
    filepath = os.path.abspath(params["filepath"])
    if not os.path.exists(filepath):
        return {"ok": False, "error": "No existe: %s" % filepath}
    bpy.ops.wm.open_mainfile(filepath=filepath)
    return {"ok": True, "filepath": filepath}


def _import_model(params):
    filepath = os.path.abspath(params["filepath"])
    if not os.path.exists(filepath):
        return {"ok": False, "error": "No existe: %s" % filepath}
    ext = os.path.splitext(filepath)[1].lower()
    before = set(bpy.data.objects.keys())
    if ext == ".glb" or ext == ".gltf":
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext in (".fbx",):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext in (".obj",):
        bpy.ops.wm.obj_import(filepath=filepath)
    else:
        return {"ok": False, "error": "Formato no soportado: %s" % ext}
    new = sorted(set(bpy.data.objects.keys()) - before)
    return {"ok": True, "filepath": filepath, "imported": new}


def _set_phase(params):
    fase = int(params.get("fase", 0))
    master = bpy.data.objects.get("MASTER_DESPIECE")
    if not master:
        return {"ok": False, "error": "No existe MASTER_DESPIECE"}
    for i in range(5):
        master["p%d" % i] = 1 if i <= fase else 0
    # capas del centro de acopio y del muelle: seguridad en Fase 1,
    # automatizacion y plataforma de descargue en Fase 2
    master["p5"] = 1 if fase >= 1 else 0
    master["p6"] = 1 if fase >= 2 else 0
    master["p7"] = 1 if fase >= 2 else 0
    master["fase"] = fase
    master.update_tag()
    bpy.context.view_layer.update()
    return {"ok": True, "fase": fase, "props": _master_state()["props"]}


def _handle(request):
    action = request.get("cmd", "ping")
    try:
        if action == "ping":
            return {"ok": True, "result": {"pong": True, "blender": bpy.app.version_string,
                                           "pid": os.getpid()}}
        if action == "scene":
            return {"ok": True, "result": _scene_summary()}
        if action == "exec":
            code = request.get("code", "")
            if code.startswith("\ufeff"):
                code = code.lstrip("\ufeff")
            return _exec_code(code, request.get("file"))
        if action == "render":
            return _render(request)
        if action == "viewport":
            return _viewport(request)
        if action == "save":
            return _save(request)
        if action == "open_file":
            return _open_file(request)
        if action == "import":
            return _import_model(request)
        if action == "phase":
            return _set_phase(request)
        return {"ok": False, "error": "Comando desconocido: %s" % action}
    except Exception:
        return {"ok": False, "error": traceback.format_exc()}


# --------------------------------------------------------------------------
# hilo del socket
# --------------------------------------------------------------------------
def _serve_connection(conn):
    with conn:
        buffer = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                return
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    request = json.loads(line.decode("utf-8"))
                except Exception as exc:
                    conn.sendall((json.dumps({"ok": False, "error": "JSON inválido: %s" % exc}) + "\n").encode("utf-8"))
                    continue
                item = {"request": request, "event": threading.Event(), "response": None}
                _QUEUE.put(item)
                if not item["event"].wait(timeout=float(request.get("timeout", 120))):
                    response = {"ok": False, "error": "Tiempo de espera agotado"}
                else:
                    response = item["response"]
                conn.sendall((json.dumps(response, default=str) + "\n").encode("utf-8"))


def _listen():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
    except OSError as exc:
        print("[CEDI360] No se pudo abrir el puerto %s: %s" % (PORT, exc))
        return
    server.listen(8)
    _STATE["server"] = server
    _STATE["port"] = PORT
    print("[CEDI360] Puente escuchando en %s:%s" % (HOST, PORT))
    while True:
        try:
            conn, _addr = server.accept()
        except OSError:
            return
        threading.Thread(target=_serve_connection, args=(conn,), daemon=True).start()


def _drain_queue():
    try:
        while True:
            item = _QUEUE.get_nowait()
            item["response"] = _handle(item["request"])
            item["event"].set()
    except queue.Empty:
        pass
    except Exception:
        print("[CEDI360] Error drenando la cola:\n%s" % traceback.format_exc())
    return 0.05


def start():
    if _STATE["server"] is not None:
        return
    threading.Thread(target=_listen, daemon=True).start()
    if _STATE["timer"] is None:
        _STATE["timer"] = bpy.app.timers.register(_drain_queue, first_interval=0.1, persistent=True)


def _on_load(*_args):
    # Al abrir otro archivo, el timer se mantiene; solo se re-registra si hizo falta.
    _STATE["timer"] = bpy.app.timers.register(_drain_queue, first_interval=0.1, persistent=True)


try:
    bpy.app.handlers.load_post.append(_on_load)
except Exception:
    pass

start()
print("[CEDI360] puente listo (proyecto: %s)" % PROJECT_DIR)
