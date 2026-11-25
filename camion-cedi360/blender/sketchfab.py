# -*- coding: utf-8 -*-
"""
CEDI 360 - Ayudante de Sketchfab
================================
Busca modelos y descarga los glb al proyecto sin volver a pedir credenciales.

El token se lee de camion-cedi360/.sketchfab_token (una linea) o de la
variable de entorno SKETCHFAB_TOKEN. Ese archivo queda fuera de
propuesta-altipal: lo que se entrega al cliente no lleva la credencial.

Uso:
    python blender\\sketchfab.py buscar "forklift" 8
    python blender\\sketchfab.py bajar <uid> [nombre.glb]

Los glb quedan en camion-cedi360/assets/modelos/.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.path.join(BASE, ".sketchfab_token")
DESTINO = os.path.join(BASE, "assets", "modelos")
API = "https://api.sketchfab.com/v3"


def leer_token():
    token = os.environ.get("SKETCHFAB_TOKEN", "").strip()
    if token:
        return token
    if os.path.isfile(TOKEN):
        with open(TOKEN, "r", encoding="ascii", errors="ignore") as fh:
            return fh.read().strip()
    return ""


def pedir(url, auth=False):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    if auth:
        req.add_header("Authorization", "Token " + leer_token())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def buscar(texto, cuantos=8):
    consulta = urllib.parse.urlencode({"type": "models", "downloadable": "true",
                                       "count": cuantos, "q": texto})
    datos = pedir("%s/search?%s" % (API, consulta))
    for m in datos.get("results", []):
        print("%s | %-38s | %7d caras | %-28s | %s"
              % (m["uid"], m["name"][:38], m.get("faceCount", 0),
                 m["license"]["label"], m["user"]["username"]))


def bajar(uid, nombre=None):
    info = pedir("%s/models/%s" % (API, uid))
    nombre = nombre or (info["name"].lower().replace(" ", "-") + ".glb")
    if not nombre.endswith(".glb"):
        nombre += ".glb"
    datos = pedir("%s/models/%s/download" % (API, uid), auth=True)
    enlace = (datos.get("glb") or {}).get("url")
    if not enlace:
        print("sin glb en la respuesta:", ", ".join(sorted(datos.keys())))
        return 1
    os.makedirs(DESTINO, exist_ok=True)
    ruta = os.path.join(DESTINO, nombre)
    urllib.request.urlretrieve(enlace, ruta)
    tam = os.path.getsize(ruta) / (1024.0 * 1024.0)
    print("ok %s  %.2f MB  %s  CC" % (nombre, tam, info["name"]))
    print("   autor:", info["user"]["username"], "·", info["license"]["label"])
    print("   ficha:", info["viewerUrl"])
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "buscar":
        buscar(" ".join(argv[2:]) or "forklift")
        return 0
    if argv[1] == "bajar" and len(argv) >= 3:
        return bajar(argv[2], argv[3] if len(argv) > 3 else None)
    print("comando no reconocido")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
