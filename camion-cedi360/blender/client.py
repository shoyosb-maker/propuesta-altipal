"""
CEDI 360 · Cliente de línea de comandos del puente de Blender
============================================================
Permite supervisar o ejecutar comandos sin pasar por el MCP.

    python client.py ping
    python client.py scene
    python client.py exec "bpy.data.objects.keys()[:10]"
    python client.py exec --file script.py
    python client.py phase 2
    python client.py render --out render/fase2.png --camera Cam_Isometrica
    python client.py viewport
"""

import argparse
import io
import json
import os
import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 9876
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(payload, timeout=180):
    payload = dict(payload)
    payload.setdefault("timeout", timeout)
    with socket.create_connection((HOST, PORT), timeout=3) as sock:
        sock.settimeout(timeout)
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buffer = b""
        while b"\n" not in buffer:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
    return json.loads(buffer.split(b"\n", 1)[0].decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Cliente del puente CEDI 360 en Blender")
    parser.add_argument("cmd", choices=["ping", "scene", "exec", "render", "viewport", "phase", "save", "import"])
    parser.add_argument("value", nargs="?", default=None, help="código, fase o ruta según el comando")
    parser.add_argument("--file", default=None, help="archivo .py para el comando exec")
    parser.add_argument("--out", default=None, help="ruta PNG de salida")
    parser.add_argument("--camera", default=None)
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()

    if args.cmd == "exec":
        code = io.open(args.file, "r", encoding="utf-8-sig").read() if args.file else (args.value or "")
        payload = {"cmd": "exec", "code": code}
        if args.file:
            payload["file"] = os.path.abspath(args.file)
    elif args.cmd == "phase":
        payload = {"cmd": "phase", "fase": int(args.value or 0)}
    elif args.cmd in ("render", "viewport"):
        out = args.out or os.path.join(PROJECT_DIR, "render", "%s_%s.png" % (args.cmd, time.strftime("%Y%m%d_%H%M%S")))
        payload = {"cmd": args.cmd, "filepath": out, "width": args.width, "height": args.height}
        if args.camera:
            payload["camera"] = args.camera
    elif args.cmd == "save":
        payload = {"cmd": "save", "filepath": args.value or ""}
    elif args.cmd == "import":
        payload = {"cmd": "import", "filepath": args.value or ""}
    else:
        payload = {"cmd": args.cmd}

    try:
        result = call(payload, timeout=600 if args.cmd in ("render", "exec", "import") else 30)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    out = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    sys.stdout.buffer.write(out.encode("utf-8", "replace") + b"\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
