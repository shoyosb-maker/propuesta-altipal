# -*- coding: utf-8 -*-
"""
CEDI 360 - Importacion de la cabina MAN TGX
===========================================
Proceso completo, idempotente, desde el glb descargado de Sketchfab:

  1. limpia restos de intentos anteriores,
  2. importa el tractocamion,
  3. quita jerarquia y aplica transformaciones,
  4. extrae una sola rueda real (islas del neumatico del tractor),
  5. recorta el trailer con un plano en Y y se queda con la cabina,
  6. escala al ancho real del camion, gira el morro hacia +y y lo apoya,
  7. integra la cabina en T05_CABINA colgando de GRP_CABINA,
  8. pinta los materiales con la paleta de ALTIPAL,
  9. replica la rueda del modelo en las seis posiciones del chasis.

Atribucion exigida por la licencia CC-BY:
    "MAN TGX 2010 V8 - High-Detail Semi-Truck" por DevPoly3D
    https://sketchfab.com/3d-models/man-tgx-2010-v8-high-detail-semi-truck-34ce748d9a4b4de7b035cfe5cb97f5d1

Uso:
    python blender\\client.py exec --file blender\\importar_cabina.py
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(PROYECTO, "assets", "modelos", "man-tgx-cabina.glb")

CORTE_Y = -1.2          # plano que separa la cabina del trailer
ANCHO = 2.52            # ancho objetivo de la cabina
MORRO_Y = 2.55          # donde queda el frente, como el blockout anterior
DIAMETRO_RUEDA = 1.15
ANCHO_RUEDA = 0.60
X_RUEDA = 1.08
Z_RUEDA = 0.575
# franja en X (unidades del glb) donde vive una sola rueda del tractor
RUEDA_X = (3.9, 6.3)

AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
GRIS = 0x4A525C
GRIS_CLARO = 0x8C97A3
NEGRO = 0x0A0A0C
AMARILLO = 0xFBC710
VIDRIO = 0x0C2C4A

PALETA = {
    "Material": (AZUL, AZUL_MEDIO, 0.35, 0.35, 1.0),
    "Back_Trailor": (AZUL, AZUL_MEDIO, 0.25, 0.5, 1.0),
    "Metalic": (GRIS_CLARO, GRIS_CLARO, 0.35, 1.0, 1.0),
    "dark": (0x12171D, 0x1B2530, 0.25, 0.5, 1.0),
    "Darker_Most": (0x0D1117, 0x161E28, 0.25, 0.5, 1.0),
    "Grey": (GRIS, GRIS, 0.30, 0.6, 1.0),
    "Glass": (VIDRIO, AZUL_MEDIO, 0.45, 0.0, 0.45),
    "Tyre_sidewalls": (NEGRO, NEGRO, 0.05, 0.0, 1.0),
    "Tyre_tread": (0x080809, 0x080809, 0.05, 0.0, 1.0),
    "Rims": (GRIS_CLARO, GRIS_CLARO, 0.40, 0.9, 1.0),
    "Hubs": (0x5A636D, 0x5A636D, 0.30, 0.8, 1.0),
    "White_Light": (0xF2F5F8, 0xF2F5F8, 1.20, 0.0, 1.0),
    "Yellow_Loght_Black": (AMARILLO, AMARILLO, 1.60, 0.0, 1.0),
}


def lin(hexa):
    c = (((hexa >> 16) & 255) / 255.0, ((hexa >> 8) & 255) / 255.0, (hexa & 255) / 255.0)
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def bbox(objetos):
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objetos:
        if o.type != "MESH":
            continue
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


def limpiar():
    for nombre in ("IMP", "CAB_TMP"):
        col = bpy.data.collections.get(nombre)
        if col:
            for o in list(col.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(col)
    cabina = bpy.data.collections.get("T05_CABINA")
    if cabina:
        for o in list(cabina.objects):
            if o.name != "GRP_CABINA":
                bpy.data.objects.remove(o, do_unlink=True)
    for o in [x for x in bpy.data.objects if x.name.startswith("RUE_")]:
        bpy.data.objects.remove(o, do_unlink=True)


def importar():
    antes = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=GLB)
    nuevos = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in antes]
    col = bpy.data.collections.new("IMP")
    bpy.context.scene.collection.children.link(col)
    for o in nuevos:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    return col


def normalizar(col):
    bpy.ops.object.select_all(action="DESELECT")
    for o in col.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = list(col.objects)[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def recortar(col):
    for o in list(col.objects):
        if o.name.startswith("RUE_"):
            continue
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-4,
                               plane_co=(0.0, CORTE_Y, 0.0),
                               plane_no=(0.0, 1.0, 0.0), clear_outer=True)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        if len(o.data.vertices) < 4 or not o.data.polygons:
            bpy.data.objects.remove(o, do_unlink=True)


def extraer_rueda(col):
    """Saca del modelo una sola rueda real (islas del neumatico del tractor).

    Los objetos del glb se llaman "Object_3*"; en el tractor cada rueda ocupa
    una franja estrecha de X, por eso se filtra por el centro de cada isla.
    """
    verts, caras, indice_mat = [], [], []
    mats = []
    piezas = [o for o in col.objects
              if o.type == "MESH" and o.name.startswith("Object_3")
              and o.name[8:9] not in (".",)]
    for o in piezas:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        mapa_isl = {}
        hechas = set()
        vistas = set()
        for v0 in bm.verts:
            if v0 in vistas:
                continue
            pila, isla = [v0], [v0]
            vistas.add(v0)
            while pila:
                v = pila.pop()
                for e in v.link_edges:
                    u = e.other_vert(v)
                    if u not in vistas:
                        vistas.add(u)
                        pila.append(u)
                        isla.append(u)
            centro = sum((q.co for q in isla), Vector()) / len(isla)
            if not (RUEDA_X[0] <= centro.x <= RUEDA_X[1]):
                continue
            for q in isla:
                mapa_isl[q] = len(verts)
                verts.append(q.co.copy())
            for q in isla:
                for f in q.link_faces:
                    if f in hechas or not all(w in mapa_isl for w in f.verts):
                        continue
                    hechas.add(f)
                    claves = tuple(mapa_isl[w] for w in f.verts)
                    caras.append(claves)
                    mat = None
                    if f.material_index < len(o.data.materials):
                        mat = o.data.materials[f.material_index]
                    if mat not in mats:
                        mats.append(mat)
                    indice_mat.append(mats.index(mat))
        bm.free()
    for o in list(piezas):
        bpy.data.objects.remove(o, do_unlink=True)
    if not caras:
        print("[CEDI360] no se encontro la rueda en el modelo")
        return None
    malla = bpy.data.meshes.new("RUE_ModeloMalla")
    malla.from_pydata(verts, [], caras)
    for m in mats:
        malla.materials.append(m)
    for i, f in enumerate(malla.polygons):
        if i < len(indice_mat):
            f.material_index = indice_mat[i]
    malla.validate()
    malla.update()
    rueda = bpy.data.objects.new("RUE_Modelo", malla)
    col.objects.link(rueda)
    mn, mx = bbox([rueda])
    print("[CEDI360] rueda extraida: %d caras, %.2f x %.2f x %.2f"
          % (len(caras), mx.x - mn.x, mx.y - mn.y, mx.z - mn.z))
    return rueda


def encajar(col):
    # la rueda extraida vive en el modelo pero no debe mandar en el encuadre
    piezas = [o for o in col.objects if not o.name.startswith("RUE_")]
    mn, mx = bbox(piezas)
    factor = ANCHO / (mx.x - mn.x)
    centro_x = (mn.x + mx.x) / 2.0
    centro_y = (mn.y + mx.y) / 2.0
    pivote = Vector((centro_x, centro_y, mn.z))
    M = (Matrix.Rotation(math.pi, 4, "Z")
         @ Matrix.Scale(factor, 4)
         @ Matrix.Translation(-pivote))
    for o in col.objects:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    mn, mx = bbox(piezas)
    # morro a MORRO_Y y base en el suelo
    dy = MORRO_Y - mx.y
    for o in col.objects:
        o.location.y += dy
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in col.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = list(col.objects)[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return bbox(piezas), factor


def integrar(col):
    cabina = bpy.data.collections.get("T05_CABINA")
    grupo = bpy.data.objects.get("GRP_CABINA")
    chasis = bpy.data.collections.get("T01_CHASIS") or cabina
    total = 0
    for o in list(col.objects):
        if o.name == "RUE_Modelo":
            # la rueda patron sobrevive al borrado de la coleccion temporal
            col.objects.unlink(o)
            chasis.objects.link(o)
            continue
        col.objects.unlink(o)
        cabina.objects.link(o)
        o.parent = grupo
        o.matrix_parent_inverse = grupo.matrix_world.inverted()
        total += 1
    bpy.data.collections.remove(col)
    return total


def unir_y_decimar(objetos, nombre, ratio):
    """Une en un solo objeto y reduce la malla para que el glb no explote."""
    mallas = [o for o in objetos if o.type == "MESH"]
    if not mallas:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    if len(mallas) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = nombre
    antes = len(obj.data.polygons)
    if antes > 4000:
        mod = obj.modifiers.new("decimar", "DECIMATE")
        mod.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
    print("[CEDI360] %s: %d caras -> %d" % (nombre, antes, len(obj.data.polygons)))
    return obj


def pintar():
    """Pinta por nombre base: al reimportar, Blender crea variantes .001."""
    for mat in bpy.data.materials:
        clave = mat.name.split(".")[0]
        if clave not in PALETA:
            continue
        base, emi, fuerza, metal, alpha = PALETA[clave]
        if not mat.use_nodes:
            mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
        bsdf.inputs["Base Color"].default_value = (*lin(base), alpha)
        bsdf.inputs["Roughness"].default_value = 0.5
        bsdf.inputs["Metallic"].default_value = metal
        # fuera texturas PBR del modelo: solo color de marca (peso del glb)
        for nodo in list(mat.node_tree.nodes):
            if nodo.type in ("TEX_IMAGE", "NORMAL_MAP", "TEX_COORD", "MAPPING"):
                mat.node_tree.nodes.remove(nodo)
        try:
            bsdf.inputs["Emission Color"].default_value = (*lin(emi), 1.0)
            bsdf.inputs["Emission Strength"].default_value = fuerza
        except KeyError:
            pass
        if alpha < 1:
            for atributo, valor in (("blend_method", "BLEND"),
                                    ("surface_render_method", "BLENDED")):
                try:
                    setattr(mat, atributo, valor)
                except (AttributeError, TypeError):
                    pass


POSICIONES_RUEDA = []
for _eje, _y in enumerate((-9.55, -10.86, -12.17)):
    POSICIONES_RUEDA.append(("RUE_Eje%d_D" % _eje, Vector((X_RUEDA, _y, Z_RUEDA))))
    POSICIONES_RUEDA.append(("RUE_Eje%d_I" % _eje, Vector((-X_RUEDA, _y, Z_RUEDA))))


def tapar_rin(rueda, centro_local, diam, ancho):
    """Disco opaco en el centro de la rueda: la viga del chasis no debe verse."""
    import bmesh
    radio = diam * 0.42
    profundidad = ancho * 0.55
    malla = bpy.data.meshes.new("RUE_Tapa")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                          radius1=radio, radius2=radio, depth=profundidad)
    bmt = bmesh.ops.rotate(bm, verts=bm.verts,
                           cent=(0, 0, 0),
                           matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bm.to_mesh(malla)
    bm.free()
    tapa = bpy.data.objects.new("RUE_Tapa", malla)
    rueda.users_collection[0].objects.link(tapa)
    tapa.location = centro_local + rueda.location
    tapa.rotation_mode = "XYZ"
    mat = bpy.data.materials.get("Hubs") or bpy.data.materials.get("Tyre_tread")
    if mat:
        tapa.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    tapa.select_set(True)
    rueda.select_set(True)
    bpy.context.view_layer.objects.active = rueda
    bpy.ops.object.join()
    return rueda


def enderezar(rueda):
    """La rueda del modelo viene acostada: el eje de giro debe quedar en X."""
    mn, mx = bbox([rueda])
    tam = mx - mn
    dims = (tam.x, tam.y, tam.z)
    # las dos dimensiones casi iguales forman el plano del neumatico;
    # la restante es el eje de giro
    pares = []
    for i in range(3):
        j, k = [n for n in range(3) if n != i]
        pares.append((abs(dims[j] - dims[k]), i))
    eje = min(pares)[1]
    giros = {1: "Z", 2: "Y"}
    if eje not in giros:
        return rueda
    centro = (mn + mx) / 2.0
    R = Matrix.Rotation(math.radians(90), 4, giros[eje])
    # se rota con matriz: el objeto importado trae rotation_mode QUATERNION
    rueda.matrix_world = (Matrix.Translation(centro) @ R
                          @ Matrix.Translation(-centro)) @ rueda.matrix_world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    rueda.select_set(True)
    bpy.context.view_layer.objects.active = rueda
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print("[CEDI360] rueda enderezada: eje %s -> X" % "XYZ"[eje])
    return rueda


def replicar(rueda):
    if not rueda:
        print("[CEDI360] sin rueda de referencia")
        return 0
    rueda = enderezar(rueda)

    mn, mx = bbox([rueda])
    tam = mx - mn
    ancho = tam.x
    diam = max(tam.y, tam.z)
    factor_x = ANCHO_RUEDA / ancho if ancho else 1.0
    factor = DIAMETRO_RUEDA / diam if diam else 1.0
    centro_local = Vector((
        ((mn.x + mx.x) / 2.0) - rueda.location.x,
        ((mn.y + mx.y) / 2.0) - rueda.location.y,
        ((mn.z + mx.z) / 2.0) - rueda.location.z,
    ))
    escala = Vector((factor_x, factor, factor))
    print("[CEDI360] rueda: diam %.3f ancho %.3f -> escala (%.3f, %.3f, %.3f)"
          % (diam, ancho, factor_x, factor, factor))

    rueda = tapar_rin(rueda, centro_local, diam, ancho)

    chasis = bpy.data.collections.get("T01_CHASIS")
    grupo = bpy.data.objects.get("GRP_CHASIS")
    for nombre, loc in POSICIONES_RUEDA:
        copia = rueda.copy()
        # malla compartida: el glb guarda una sola rueda para las seis
        copia.data = rueda.data
        copia.name = nombre
        chasis.objects.link(copia)
        copia.scale = escala
        copia.location = Vector((
            loc.x - centro_local.x * factor_x,
            loc.y - centro_local.y * factor,
            loc.z - centro_local.z * factor,
        ))
        # pegadas al grupo del chasis: si el camion se mueve, las ruedas van con el
        if grupo is not None:
            copia.parent = grupo
            copia.matrix_parent_inverse = grupo.matrix_world.inverted()
    bpy.data.objects.remove(rueda, do_unlink=True)
    return len(POSICIONES_RUEDA)


def build():
    if not os.path.isfile(GLB):
        print("[CEDI360] falta el glb:", GLB)
        return
    limpiar()
    col = importar()
    normalizar(col)
    rueda = extraer_rueda(col)
    recortar(col)
    (mn, mx), factor = encajar(col)
    print("[CEDI360] cabina encajada: %.2f x %.2f x %.2f (escala %.4f)"
          % (mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, factor))
    integrar(col)
    pintar()
    cabina = bpy.data.collections.get("T05_CABINA")
    if cabina:
        unir_y_decimar(list(cabina.objects), "CAB_Man_TGX", 0.45)
    n = replicar(rueda)
    for _ in range(3):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    print("[CEDI360] cabina integrada y %d ruedas replicadas" % n)
    print("[CEDI360] credito: MAN TGX 2010 V8 por DevPoly3D, CC-BY")


build()
