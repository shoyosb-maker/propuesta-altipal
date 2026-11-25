# -*- coding: utf-8 -*-
"""
CEDI 360 - Entorno operativo
============================
Modela lo que rodea al camion para que el recorrido no sea una pieza
flotando en el vacio: patio de maniobras, muelle con tres puertas,
nave del CEDI, torres de luz, fila de despacho, caseta y ruta de salida.

Todo va a la coleccion T80_ENTORNO, que si se exporta al glb (a
diferencia de T90_ANOTACIONES, que vive en espacio de camara).

Coordenadas heredadas de build_scene.py:
  el camion ocupa y de -13 a 1 y x de -1.9 a 1.9
  el morro mira hacia +y, asi que la salida a ruta tambien va hacia +y

Modulo autocontenido: no depende de los ayudantes de build_scene.py.

Uso:
    python blender\\client.py exec --file blender\\entorno.py
"""

import math

import bmesh
import bpy

COLECCION = "T80_ENTORNO"

AMARILLO = (0.965, 0.745, 0.055)
TINTA = (0.012, 0.020, 0.031)

PATIO_X0, PATIO_X1 = -7.0, 26.0
PATIO_Y0, PATIO_Y1 = -26.0, 18.0
ANDEN_X = -5.4
ANDEN_ALTO = 1.25
MURO_E = -12.12          # cara exterior del muro este de la nave (almacen.py)


# ------------------------------------------------------------- ayudantes
def coleccion(nombre):
    col = bpy.data.collections.get(nombre)
    if not col:
        col = bpy.data.collections.new(nombre)
        bpy.context.scene.collection.children.link(col)
    return col


def material(nombre, color, emision=None, fuerza=0.0, rugosidad=0.8, metal=0.0, alpha=1.0):
    """Reutiliza el material si ya existe (los del camion) o lo crea."""
    mat = bpy.data.materials.get(nombre)
    if mat:
        return mat
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = metal
    if emision is not None:
        try:
            bsdf.inputs["Emission Color"].default_value = (*emision, 1.0)
            bsdf.inputs["Emission Strength"].default_value = fuerza
        except KeyError:
            pass
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        mat.use_backface_culling = False
    return mat


def box(nombre, tam, loc, col, mat=None, rot=(0.0, 0.0, 0.0)):
    sx, sy, sz = tam
    malla = bpy.data.meshes.new(nombre)
    verts = [
        (-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
        (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
        (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
        (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2),
    ]
    caras = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    malla.from_pydata(verts, [], caras)
    malla.update()
    obj = bpy.data.objects.new(nombre, malla)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def cylinder(nombre, radio, largo, loc, col, mat=None, segments=20, rot=(0.0, 0.0, 0.0)):
    malla = bpy.data.meshes.new(nombre)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=radio, radius2=radio, depth=largo)
    except TypeError:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              diameter1=radio * 2, diameter2=radio * 2, depth=largo)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def texto(nombre, cuerpo, loc, tam, col, mat, rot=(math.radians(90), 0.0, 0.0)):
    cur = bpy.data.curves.new(nombre, type="FONT")
    cur.body = cuerpo
    cur.size = tam
    cur.align_x = "CENTER"
    obj = bpy.data.objects.new(nombre, cur)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


# ------------------------------------------------------------- piezas
def build_patio(col):
    losa = material("M_Patio", (0.016, 0.021, 0.028), rugosidad=0.92)
    junta = material("M_Junta", (0.05, 0.045, 0.03), emision=(0.20, 0.15, 0.03), fuerza=0.08)
    box("Patio_Losa", (PATIO_X1 - PATIO_X0, PATIO_Y1 - PATIO_Y0, 0.06),
        ((PATIO_X0 + PATIO_X1) / 2, (PATIO_Y0 + PATIO_Y1) / 2, 0.0), col, losa)

    z = 0.012
    for x in range(int(PATIO_X0), int(PATIO_X1) + 1, 5):
        box("Junta_X_%d" % x, (0.04, PATIO_Y1 - PATIO_Y0, 0.004),
            (x, (PATIO_Y0 + PATIO_Y1) / 2, z), col, junta)
    for y in range(int(PATIO_Y0), int(PATIO_Y1) + 1, 5):
        box("Junta_Y_%d" % y, (PATIO_X1 - PATIO_X0, 0.04, 0.004),
            ((PATIO_X0 + PATIO_X1) / 2, y, z), col, junta)

    via = material("M_Via", (0.020, 0.024, 0.030), rugosidad=0.9)
    box("Via_Calzada", (9.0, 34.0, 0.05), (8.0, 33.0, 0.02), col, via)
    eje = material("M_Eje_Via", (0.06, 0.05, 0.02), emision=AMARILLO, fuerza=0.35)
    for i in range(12):
        box("Via_Eje_%02d" % i, (0.28, 1.6, 0.012), (8.0, 18.0 + i * 2.6, 0.05), col, eje)

    borde = material("M_Bordillo", (0.07, 0.06, 0.03), emision=(0.35, 0.27, 0.04), fuerza=0.22)
    for lado in (-1, 1):
        box("Via_Borde_%d" % lado, (0.22, 34.0, 0.10), (8.0 + lado * 4.6, 33.0, 0.05), col, borde)


def build_muelle(col):
    """Plataforma de descargue: anden, vanos de recibo y cubierta.

    Los marcos quedan sobre la cara exterior del muro este (x = -12,12):
    antes estaban a 6 m, flotando en mitad de la plataforma, y una columna
    de la cubierta caia justo en la boca del muelle 02. La demarcacion, el
    equipo y la tecnologia los pone muelle.py.
    """
    hormigon = material("M_Hormigon", (0.035, 0.038, 0.044), rugosidad=0.9)
    borde = material("M_Anden_Borde", (0.08, 0.065, 0.02), emision=AMARILLO, fuerza=0.45)
    cortina = material("M_Muelle_Cortina", (0.02, 0.07, 0.11), emision=(0.06, 0.24, 0.34),
                       fuerza=0.30, rugosidad=0.35, alpha=0.45)

    box("Muelle_Anden", (7.0, 30.0, ANDEN_ALTO), (ANDEN_X - 3.5, -8.0, ANDEN_ALTO / 2), col, hormigon)
    box("Muelle_Borde", (0.30, 30.0, 0.12), (ANDEN_X, -8.0, ANDEN_ALTO), col, borde)

    for i, y in enumerate((-16.0, -8.0, 0.0)):
        # marco del vano sobre la cara exterior del muro
        for lado in (-1, 1):
            box("Muelle_Jamba_%d_%d" % (i, lado), (0.16, 0.14, 3.30),
                (MURO_E + 0.08, y + lado * 1.77, ANDEN_ALTO + 1.65), col, borde)
        box("Muelle_Dintel_%d" % i, (0.16, 3.68, 0.16),
            (MURO_E + 0.08, y, ANDEN_ALTO + 3.24), col, borde)
        # cortina de tiras: el vano queda abierto y se ve el paso de carga
        for k in range(9):
            alto = 2.86 - 0.06 * (k % 3)
            box("Muelle_Tira_%d_%d" % (i, k), (0.03, 0.34, alto),
                (MURO_E + 0.04, y - 1.44 + k * 0.36, ANDEN_ALTO + 3.05 - alto / 2),
                col, cortina)
        # topes de atraque en el borde del anden
        for lado in (-1, 1):
            box("Muelle_Tope_%d_%s" % (i, "A" if lado < 0 else "B"), (0.55, 0.35, 0.55),
                (ANDEN_X + 0.15, y + lado * 1.5, ANDEN_ALTO - 0.3), col, borde)

    # plataforma abierta: sin cubierta. Una losa (o una pergola) de 1,5 a 2,6 m
    # tapaba el anden en todas las vistas aereas del recorrido, y el dibujo
    # gana mas con la plataforma despejada que con la marquesina
    box("Muelle_Rampa", (3.2, 3.0, 0.18), (ANDEN_X + 2.2, -21.5, 0.34), col, hormigon,
        rot=(0.0, math.radians(-9.0), 0.0))

    box("Muelle_Rampa", (3.2, 3.0, 0.18), (ANDEN_X + 2.2, -21.5, 0.34), col, hormigon,
        rot=(0.0, math.radians(-9.0), 0.0))


def build_nave(col):
    """Fachada del CEDI: la nave de gran formato la construye almacen.py.

    Aqui solo queda lo exterior: franjas de marca sobre la banda de carga,
    el rotulo de la fachada y la caseta de vigilancia. El cuerpo, los muros,
    las cerchas y las estanterias viven en la coleccion T81_CEDI.
    """
    borde = material("M_Anden_Borde", (0.08, 0.065, 0.02), emision=AMARILLO, fuerza=0.45)
    muro = material("M_Nave", (0.022, 0.027, 0.036), emision=(0.02, 0.026, 0.036), fuerza=0.12)
    rotulo = material("M_MarcaAmbar", (0.10, 0.08, 0.01), emision=AMARILLO, fuerza=2.2)

    # franja de marca y zocalo sobre la banda de fachada (x = -12,42)
    box("Nave_Zocalo", (0.10, 44.0, 0.30), (-12.06, -7.0, 1.55), col, borde)
    box("Nave_Franja", (0.10, 44.0, 0.24), (-12.06, -7.0, 3.34), col,
        material("M_MarcaVerde", (0.35, 0.55, 0.12), emision=(0.62, 0.77, 0.35), fuerza=0.55))
    texto("Nave_Rotulo", "CEDI 360", (-12.00, 3.6, 2.28), 0.82, col, rotulo,
          rot=(math.radians(90), 0.0, math.radians(90)))

    box("Caseta", (4.0, 4.0, 3.2), (2.0, -24.0, 1.6), col, muro)
    box("Caseta_Cubierta", (4.6, 4.6, 0.25), (2.0, -24.0, 3.3), col, muro)
    box("Caseta_Vidrio", (0.12, 3.0, 1.1), (4.05, -24.0, 2.2), col,
        material("M_Vidrio", (0.015, 0.025, 0.045), emision=(0.18, 0.26, 0.38), fuerza=0.35, alpha=0.5))
    box("Caseta_Barrera", (0.18, 0.18, 1.1), (6.4, -22.0, 0.55), col, borde)
    box("Caseta_Pluma", (4.6, 0.16, 0.16), (4.2, -22.0, 1.05), col, borde)


def build_torres(col):
    poste = material("M_Poste", (0.05, 0.05, 0.055), emision=(0.06, 0.055, 0.04), fuerza=0.25)
    luz = material("M_Luz_Torre", (0.10, 0.09, 0.03), emision=(1.0, 0.87, 0.55), fuerza=3.2)
    sitios = ((20.0, -20.0), (20.0, 8.0), (-2.0, 12.0), (16.0, 30.0))
    for i, (x, y) in enumerate(sitios):
        box("Torre_Poste_%d" % i, (0.32, 0.32, 12.0), (x, y, 6.0), col, poste)
        box("Torre_Cabeza_%d" % i, (2.4, 0.7, 0.22), (x, y, 12.1), col, poste)
        for j, dx in enumerate((-0.9, 0.0, 0.9)):
            box("Torre_Foco_%d_%d" % (i, j), (0.42, 0.5, 0.16), (x + dx, y, 11.85), col, luz)


def build_cercado(col):
    poste = material("M_Poste", (0.05, 0.05, 0.055), emision=(0.06, 0.055, 0.04), fuerza=0.25)
    for i in range(10):
        box("Cerca_Poste_%d" % i, (0.14, 0.14, 1.9),
            (PATIO_X1 - 0.5, PATIO_Y0 + 2.0 + i * 4.6, 0.95), col, poste)
    for i in range(10):
        box("Cerca_Malla_%d" % i, (0.06, 4.4, 1.7),
            (PATIO_X1 - 0.5, PATIO_Y0 + 4.3 + i * 4.6, 0.95), col, poste)


def _limpia(col):
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def build_camara():
    """Cámara ortográfica de control para ver la escena ampliada completa."""
    col = bpy.data.collections.get("T99_RIG") or coleccion("T99_RIG")
    for nombre in ("Cam_Entorno", "Cam_Entorno_Target"):
        viejo = bpy.data.objects.get(nombre)
        if viejo:
            bpy.data.objects.remove(viejo, do_unlink=True)
    tgt = bpy.data.objects.new("Cam_Entorno_Target", None)
    tgt.location = (-14.0, -5.0, 5.0)
    col.objects.link(tgt)
    datos = bpy.data.cameras.new("Cam_Entorno")
    datos.type = "ORTHO"
    datos.ortho_scale = 104.0
    cam = bpy.data.objects.new("Cam_Entorno", datos)
    cam.location = (52.0, 48.0, 44.0)
    col.objects.link(cam)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    isometrica = bpy.data.objects.get("Cam_Isometrica")
    if isometrica:
        bpy.context.scene.camera = isometrica
    return cam


def build():
    col = coleccion(COLECCION)
    _limpia(col)
    build_patio(col)
    build_muelle(col)
    build_nave(col)
    build_torres(col)
    # la fila de despacho la pone importar_furgon.py con el modelo real
    build_cercado(col)
    build_camara()
    print("[CEDI360] entorno: %d objetos" % len(col.objects))
    return col


build()
