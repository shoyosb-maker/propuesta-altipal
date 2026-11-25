# -*- coding: utf-8 -*-
"""
CEDI 360 - Laminas del recorrido 2D
===================================
Renderiza las cinco fases del despiece a 2048 x 1152 para el visor de
laminas (recorrido.html), con la paleta de marca ya aplicada.

Diferencias con el render de control:
  - excluye T80_ENTORNO: la lamina habla del camion, no del patio,
  - apaga Freestyle: las lineas de contorno tapaban el color de marca,
  - deja las anotaciones (cotas y rotulos) porque son parte del lenguaje.

Uso:
    python blender\\client.py exec --file blender\\pliegos.py
"""

import os

import bpy

PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(PROYECTO, "render", "web")
FASES = 5
# la lamina habla del camion: el patio, el acopio, el muelle y los vehiculos
# del muelle (T86) quedan fuera. T91_SIN_LINEAS tambien: sin Freestyle no hace
# falta, y por ahi seguian asomando los montacargas y las estibas enlazadas a
# ese filtro. Las anotaciones se quedan porque viven en T90.
FUERA = ("T80_ENTORNO", "T81_CEDI", "T82_RACKS", "T83_SEGURIDAD",
         "T84_AUTOMATIZACION", "T85_MUELLE", "T86_VEHICULOS",
         "T87_FRIO", "T88_ADMIN", "T89_ENERGIA", "T90_ANEXO", "T92_REDES",
         "T93_SIM", "T91_SIN_LINEAS", "FUR_FLOTA")


def props(fase):
    master = bpy.data.objects.get("MASTER_DESPIECE")
    if not master:
        return
    master["p0"] = 1.0
    for i in range(1, 5):
        master["p%d" % i] = max(0.0, min(1.0, fase - (i - 1)))
    master["p5"] = 1.0 if fase >= 1 else 0.0
    master["p6"] = 1.0 if fase >= 2 else 0.0
    master["p7"] = 1.0 if fase >= 2 else 0.0
    master.update_tag()
    bpy.context.view_layer.update()


def preparar():
    escena = bpy.context.scene
    escena.render.resolution_x = 2048
    escena.render.resolution_y = 1152
    escena.render.resolution_percentage = 100
    escena.render.image_settings.file_format = "PNG"
    escena.render.use_freestyle = False
    try:
        escena.eevee.taa_render_samples = 32
    except AttributeError:
        pass

    isometrica = bpy.data.objects.get("Cam_Isometrica")
    if isometrica:
        escena.camera = isometrica

    capas = []
    for nombre in FUERA:
        capa = bpy.context.view_layer.layer_collection.children.get(nombre)
        if capa:
            capa.exclude = True
            capas.append(capa)
    return capas


def main():
    os.makedirs(SALIDA, exist_ok=True)
    capas = preparar()
    try:
        for fase in range(FASES):
            props(fase)
            ruta = os.path.join(SALIDA, "fase%d.png" % fase)
            bpy.context.scene.render.filepath = ruta
            bpy.ops.render.render(write_still=True)
            print("[CEDI360] lamina fase %d -> %s" % (fase, os.path.basename(ruta)))
    finally:
        for capa in capas:
            capa.exclude = False
        props(0)
    print("[CEDI360] laminas listas en render/web")


main()
