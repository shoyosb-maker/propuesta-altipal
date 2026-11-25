# -*- coding: utf-8 -*-
"""
CEDI 360 - Exportacion del modelo para el visor web
===================================================
Exporta una copia limpia a glTF binario (.glb) con el despiece horneado en
keyframes reales, porque glTF no entiende drivers de Blender.

El horneado aplica las mismas formulas que build_scene.py (los drivers no se
re-evaluan de forma fiable desde script, asi que se replican aqui):

  GRP_TECHO      z = p1*1.15 + p3*1.45
  GRP_CARGA      z = p1*0.85
  GRP_PARED_IZQ  x = p2*-2.05      GRP_PARED_DER  x = p2*2.05
  GRP_FRONTAL    y = p2*1.30
  GRP_PUERTA_IZQ rz = p2*-2.36      GRP_PUERTA_DER rz = p2*2.36
  GRP_CABINA     y = p4*1.20

Uso:
    python blender\\client.py exec --file blender\\web_export.py
"""

import bpy
import os
from mathutils import Vector

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(PROJECT, "export")
TARGET = os.path.join(EXPORT_DIR, "cedi360.glb")
BLEND = os.path.join(PROJECT, "blender", "cedi360.blend")

GRUPOS = ["GRP_TECHO", "GRP_CARGA", "GRP_PARED_IZQ", "GRP_PARED_DER",
          "GRP_FRONTAL", "GRP_PUERTA_IZQ", "GRP_PUERTA_DER", "GRP_CABINA",
          "GRP_CCTV", "GRP_AUTOMATIZACION", "GRP_MUELLE"]
LAYERS = {"GRP_CCTV": "p5", "GRP_AUTOMATIZACION": "p6", "GRP_MUELLE": "p7"}
F0, F1 = 1, 121
PASO = 4


def limitar(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def props(fase):
    p = {"p0": 1.0}
    for i in range(1, 5):
        p["p%d" % i] = limitar(fase - (i - 1))
    # capas nuevas: seguridad en Fase 1, automatizacion y muelle en Fase 2
    p["p5"] = limitar(fase)
    p["p6"] = limitar(fase - 1.0)
    p["p7"] = limitar(fase - 1.0)
    return p


def delta(nombre, p):
    if nombre == "GRP_TECHO":
        return "z", p["p1"] * 1.15 + p["p3"] * 1.45
    if nombre == "GRP_CARGA":
        return "z", p["p1"] * 0.85
    if nombre == "GRP_PARED_IZQ":
        return "x", p["p2"] * -2.05
    if nombre == "GRP_PARED_DER":
        return "x", p["p2"] * 2.05
    if nombre == "GRP_FRONTAL":
        return "y", p["p2"] * 1.30
    if nombre == "GRP_PUERTA_IZQ":
        return "rz", p["p2"] * -2.36
    if nombre == "GRP_PUERTA_DER":
        return "rz", p["p2"] * 2.36
    if nombre == "GRP_CABINA":
        return "y", p["p4"] * 1.20
    if nombre in LAYERS:
        # las capas no se deslizan: entran de golpe al empezar su fase
        return "z", 0.0 if p[LAYERS[nombre]] >= 0.5 else -60.0
    return None, 0.0


def textos_a_malla():
    n = 0
    for obj in list(bpy.data.objects):
        if obj.type != "FONT":
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.convert(target="MESH")
            n += 1
        except Exception as exc:
            print("  texto no convertido %s: %s" % (obj.name, exc))
    return n


def hornear():
    """Crea keyframes recorriendo la fase de 0 a 4 de forma continua."""
    # los drivers escriben en location: hay que limpiarlos ANTES de leer la
    # base. Si no, un archivo guardado con la capa apagada (z = -60) se
    # hornea corrido otros 60 m y la capa no aparece nunca en el visor.
    for nombre in GRUPOS:
        obj = bpy.data.objects.get(nombre)
        if obj:
            obj.animation_data_clear()

    bases = {}
    for nombre in GRUPOS:
        obj = bpy.data.objects.get(nombre)
        if obj:
            # las capas nacen en el origen: su base es 0, no lo que dejo el driver
            loc0 = Vector((0.0, 0.0, 0.0)) if nombre in LAYERS else obj.location.copy()
            bases[nombre] = (loc0, obj.rotation_euler.copy())

    for nombre in GRUPOS:
        obj = bpy.data.objects.get(nombre)
        if obj:
            obj.animation_data_clear()

    for frame in range(F0, F1 + 1, PASO):
        t = (frame - F0) / float(F1 - F0)
        p = props(t * 4.0)
        for nombre, (loc0, rot0) in bases.items():
            obj = bpy.data.objects.get(nombre)
            if not obj:
                continue
            canal, valor = delta(nombre, p)
            loc = loc0.copy()
            rot = rot0.copy()
            if canal == "x":
                loc.x = loc0.x + valor
            elif canal == "y":
                loc.y = loc0.y + valor
            elif canal == "z":
                loc.z = loc0.z + valor
            elif canal == "rz":
                rot.z = rot0.z + valor
            obj.location = loc
            obj.rotation_euler = rot
            obj.keyframe_insert("location", frame=frame)
            obj.keyframe_insert("rotation_euler", frame=frame)

    escena = bpy.context.scene
    escena.frame_start = F0
    escena.frame_end = F1
    escena.frame_set(F0)


def seleccionar():
    bpy.ops.object.select_all(action="DESELECT")
    excluidas = {"T90_ANOTACIONES", "T07_HOLOGRAMA", "Collection"}
    vista = bpy.context.view_layer.objects
    total = 0
    for obj in bpy.data.objects:
        if obj.type not in ("MESH", "EMPTY"):
            continue
        if obj.name not in vista:
            continue
        if any(col.name in excluidas for col in obj.users_collection):
            continue
        obj.select_set(True)
        total += 1
    return total


def exportar():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    try:
        bpy.ops.export_scene.gltf(
            filepath=TARGET, export_format="GLB", use_selection=True,
            export_apply=True, export_animations=True, export_frame_range=True,
            export_force_sampling=True, export_optimize_animation_size=False,
            export_yup=True,
        )
    except TypeError as exc:
        print("  opciones no disponibles (%s); export basico" % exc)
        bpy.ops.export_scene.gltf(filepath=TARGET, export_format="GLB",
                                  use_selection=True, export_animations=True)
    return TARGET


def main():
    print("[CEDI360] textos convertidos:", textos_a_malla())
    hornear()
    print("[CEDI360] horneado de %d a %d cada %d frames" % (F0, F1, PASO))
    print("[CEDI360] objetos:", seleccionar())
    ruta = exportar()
    print("[CEDI360] exportado %.2f MB" % (os.path.getsize(ruta) / (1024 * 1024)))
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        print("[CEDI360] escena restaurada desde el .blend")


if __name__ == "__main__":
    main()
