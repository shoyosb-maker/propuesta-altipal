# -*- coding: utf-8 -*-
"""
CEDI 360 - Posicion del tracto camion sobre el patio
====================================================
Corre el camion del despiece (chasis, contenedor, carga, cabina, detalles y
marca) como un solo bloque hacia el sur, para centrarlo frente a la
plataforma de descargue sin tocar ninguna de sus piezas.

Se aplica al final del build: las piezas ya estan colgadas de los empties
GRP_*, asi que basta con colgar esos grupos de un empty raiz desplazado.
No se toca la location de los grupos porque GRP_FRONTAL y GRP_CABINA tienen
driver sobre y: la raiz compone el desplazamiento sin pelearse con ellos.

El valor es absoluto, de modo que repetir build_all no acumula corrimientos.

DY = -2.90 m (sur): centro del camion en y = -8, la mitad del anden
(-23 a 7). El camion de reparto del muelle 01 se corre 1,20 m al sur para
dejarle holgura (antes quedaba a 0,24 m y se cruzaban).

DX = +8,00 m (este): el camion sale de los muelles y queda en linea con el
eje de la calzada de salida (x = 8, de y 16 a 50), como si arrancara derecho
hacia la carretera. Cam_Isometrica y las cotas de annotations.py acompanan
con el mismo valor (CAMION_X), y el holograma del visor con HOLO_CENTRO_X.

Uso:
    python blender\\client.py exec --file blender\\ubicar_camion.py
"""

import bpy

DY = -2.90
DX = 8.00           # al este, en linea con el eje de la calzada de salida
RAIZ = "GRP_CAMION"
COLECCION = "T01_CHASIS"

GRUPOS = ("GRP_CHASIS", "GRP_CONTENEDOR", "GRP_TECHO", "GRP_CARGA",
          "GRP_PARED_IZQ", "GRP_PARED_DER", "GRP_FRONTAL",
          "GRP_PUERTA_IZQ", "GRP_PUERTA_DER", "GRP_CABINA")


def build():
    col = bpy.data.collections.get(COLECCION)
    if col is None:
        col = bpy.data.collections.new(COLECCION)
        bpy.context.scene.collection.children.link(col)

    raiz = bpy.data.objects.get(RAIZ)
    if raiz is None:
        raiz = bpy.data.objects.new(RAIZ, None)
        raiz.empty_display_type = "PLAIN_AXES"
        raiz.empty_display_size = 1.5
        col.objects.link(raiz)
    raiz.parent = None
    raiz.location = (DX, DY, 0.0)
    raiz.rotation_euler = (0.0, 0.0, 0.0)

    n = 0
    for nombre in GRUPOS:
        obj = bpy.data.objects.get(nombre)
        if obj is None:
            continue
        obj.parent = raiz
        # sin inversa: el grupo hereda el desplazamiento de la raiz
        obj.matrix_parent_inverse.identity()
        n += 1

    bpy.context.view_layer.update()
    print("[CEDI360] camion: %d grupos colgados de %s en (%.2f, %.2f)"
          % (n, RAIZ, DX, DY))


build()
