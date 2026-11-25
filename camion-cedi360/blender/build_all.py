# -*- coding: utf-8 -*-
"""Reconstruye todo el despiece: escena, entorno, detalles, cotas y holograma."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
for nombre in ("build_scene.py", "entorno.py", "almacen.py", "muelle.py",
               "programa.py", "detalles.py", "annotations.py", "hologram.py",
               "marca_altipal.py", "importar_cabina.py", "importar_furgon.py",
               "importar_muelle.py", "ubicar_camion.py"):
    ruta = os.path.join(BASE, nombre)
    with open(ruta, "r", encoding="utf-8-sig") as fh:
        codigo = fh.read()
    g = {"__name__": "__main__", "__file__": ruta}
    exec(compile(codigo, ruta, "exec"), g)
    print("[CEDI360] ejecutado %s" % nombre)
print("[CEDI360] escena completa lista")
