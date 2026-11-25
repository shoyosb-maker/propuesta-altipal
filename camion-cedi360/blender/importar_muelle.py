# -*- coding: utf-8 -*-
"""
CEDI 360 - Vehiculos y equipo de la plataforma de descargue
==========================================================
Sustituye los modelos procedurales de muelle.py por modelos de Sketchfab:

  delivery-truck.glb   "DELIVERY TRUCK" de jasmin.daniel (CC-BY)
                       -> camion de reparto atracado en el muelle 01
  forklift.glb         "Forklift low poly" de 380660711785 (CC-BY)
                       -> dos montacargas sobre la plataforma

La camioneta en espera es una copia de la Sprinter de importar_furgon.py
(malla compartida, sin coste extra en el glb) y conserva su logo de
FUNDASERINCO. El camion de reparto lleva el logo de ALTIPAL en las dos caras.

Los glb se bajan con blender/sketchfab.py; el token vive en
camion-cedi360/.sketchfab_token y no entra en la entrega.

Coleccion: T86_VEHICULOS. Modulo autocontenido e idempotente.

Uso:
    python blender\\client.py exec --file blender\\importar_muelle.py
"""

import math
import os

import bpy
from mathutils import Matrix, Vector

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELOS = os.path.join(BASE, "assets", "modelos")
MARCA = os.path.join(BASE, "assets", "marca")
CAMION = os.path.join(MODELOS, "delivery-truck.glb")
MONTACARGAS = os.path.join(MODELOS, "forklift.glb")

COLECCION = "T86_VEHICULOS"
APRON = 0.03
SLAB = 1.25             # cota del anden: el equipo de plataforma va aqui
BORDE = -5.4

ANCHO_CAMION = 2.30
ANCHO_MONTACARGAS = 1.20


# ------------------------------------------------------------- ayudantes
def coleccion(nombre):
    col = bpy.data.collections.get(nombre)
    if not col:
        col = bpy.data.collections.new(nombre)
        bpy.context.scene.collection.children.link(col)
    return col


def vaciar(col):
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def bbox(objetos):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objetos:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


def importar(ruta):
    antes = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=ruta)
    return [bpy.data.objects[n]
            for n in sorted(set(bpy.data.objects.keys()) - antes)]


def unir(nuevos, nombre, col):
    """Deja una sola malla con las transformadas aplicadas, en T86."""
    mallas = [o for o in nuevos if o.type == "MESH"]
    for o in mallas:
        matriz = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = matriz
    for o in nuevos:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = nombre
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # algunos glb traen normales invertidas: se recalculan hacia afuera
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def imagen_base(mat):
    """Busca la textura de color, aunque el glb la meta en un grupo de nodos."""
    bsdf = None
    for nodo in mat.node_tree.nodes:
        if nodo.type == "BSDF_PRINCIPLED":
            bsdf = nodo
            break
    if bsdf is None or not bsdf.inputs["Base Color"].is_linked:
        return None
    vistos = set()

    def buscar(nodo):
        if nodo.type == "TEX_IMAGE":
            return nodo.image
        if nodo.type == "GROUP" and nodo.node_tree is not None:
            nombre = nodo.node_tree.name
            if nombre in vistos:
                return None
            vistos.add(nombre)
            for interno in nodo.node_tree.nodes:
                hallada = buscar(interno)
                if hallada is not None:
                    return hallada
        return None

    return buscar(bsdf.inputs["Base Color"].links[0].from_node)


def un_material_plano(obj, nombre, base=0xA8B2BC, emision=0x8C97A3, fuerza=0.45):
    """Equipo menor: color plano de la paleta, sin textura ni entintado.
    Un montacargas de 4.400 caras con Freestyle encima es un garabato."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    def lin(hexa):
        canales = (((hexa >> 16) & 255) / 255.0, ((hexa >> 8) & 255) / 255.0,
                   (hexa & 255) / 255.0)
        return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                     for c in canales)
    bsdf.inputs["Base Color"].default_value = (*lin(base), 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Metallic"].default_value = 0.40
    try:
        bsdf.inputs["Emission Color"].default_value = (*lin(emision), 1.0)
        bsdf.inputs["Emission Strength"].default_value = fuerza
    except KeyError:
        pass
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poli in obj.data.polygons:
        poli.material_index = 0


def un_material(obj, nombre, fuerza=0.75):
    """Deja un material limpio con la textura del modelo como color y como
    emision. Los glb traen grupos de nodos (normal, ORM) que el visor no
    entiende y que dejaban el vehiculo como una silueta negra."""
    imagen = None
    for mat in obj.data.materials:
        if mat is not None:
            imagen = imagen_base(mat)
            if imagen is not None:
                break
    if imagen is None:
        return
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = imagen
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    try:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = fuerza
    except KeyError:
        pass
    bsdf.inputs["Roughness"].default_value = 0.70
    bsdf.inputs["Metallic"].default_value = 0.10
    nt.links.new(bsdf.outputs["BSDF"], salida.inputs["Surface"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poli in obj.data.polygons:
        poli.material_index = 0


def colocar(obj, ancho, giro, x_min=None, centro=(0.0, 0.0), z=APRON):
    """Escala por ancho real, gira, apoya en el suelo y centra."""
    mn, mx = bbox([obj])
    factor = ancho / (mx.x - mn.x)
    obj.matrix_world = (Matrix.Rotation(giro, 4, "Z")
                        @ Matrix.Scale(factor, 4) @ obj.matrix_world)
    bpy.context.view_layer.update()
    mn, mx = bbox([obj])
    dx = (x_min - mn.x) if x_min is not None else (centro[0] - (mn.x + mx.x) / 2.0)
    dy = centro[1] - (mn.y + mx.y) / 2.0
    obj.location.x += dx
    obj.location.y += dy
    obj.location.z += z - mn.z
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return bbox([obj])


# ------------------------------------------------------------------- logos
def placa(nombre, ruta, ancho, loc, col, rot, mat_nombre):
    imagen = bpy.data.images.load(ruta, check_existing=True)
    alto = ancho * imagen.size[1] / float(imagen.size[0])
    hw, hh = ancho / 2.0, alto / 2.0
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)],
                      [], [(0, 1, 2, 3)])
    malla.update()
    uv = malla.uv_layers.new(name="UVMap")
    for i, (u, v) in enumerate(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
        uv.data[i].uv = (u, v)
    obj = bpy.data.objects.new(nombre, malla)
    obj.location = loc
    obj.rotation_euler = rot
    try:
        obj.visible_shadow = False
    except AttributeError:
        pass
    col.objects.link(obj)
    obj.data.materials.append(mat_logo(mat_nombre, ruta))
    return obj


def mat_logo(nombre, ruta):
    """Logo con transparencia real: Mix Shader con Transparent BSDF."""
    imagen = bpy.data.images.load(ruta, check_existing=True)
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = imagen
    tex.extension = "CLIP"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    try:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.3
    except KeyError:
        pass
    bsdf.inputs["Roughness"].default_value = 0.6
    nt.links.new(tex.outputs["Alpha"], mezcla.inputs["Fac"])
    nt.links.new(transp.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(bsdf.outputs["BSDF"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    for atributo, valor in (("surface_render_method", "BLENDED"),
                            ("blend_method", "BLEND")):
        try:
            setattr(mat, atributo, valor)
        except (AttributeError, TypeError):
            pass
    return mat


# ------------------------------------------------------------- camioneta
def copiar_furgon(col, x, y, giro):
    """Copia la Sprinter de FUNDASERINCO de la fila de despacho."""
    unidad = bpy.data.objects.get("FUR_Unidad_1")
    if unidad is None:
        print("[CEDI360] falta FUR_Unidad_1: correr importar_furgon.py antes")
        return 0
    piezas = [unidad]
    for lado in ("I", "D"):
        logo = bpy.data.objects.get("FUR_Logo_1_%s" % lado)
        if logo:
            piezas.append(logo)
    pivote = Vector(unidad.location)
    M = (Matrix.Translation(Vector((x, y, 0.0)))
         @ Matrix.Rotation(giro, 4, "Z")
         @ Matrix.Translation(-pivote))
    for o in piezas:
        copia = o.copy()
        # malla y material compartidos: el glb no duplica geometria
        copia.data = o.data
        copia.name = "MUE_" + o.name
        col.objects.link(copia)
        copia.matrix_world = M @ o.matrix_world
    return len(piezas)


# --------------------------------------------------------------------- build
def build():
    col = coleccion(COLECCION)
    vaciar(col)

    if not os.path.isfile(CAMION) or not os.path.isfile(MONTACARGAS):
        print("[CEDI360] faltan glb en assets/modelos: usar blender\\sketchfab.py")
        return

    # camion de reparto atracado en el muelle 01 (cola sobre el borde del anden)
    nuevos = importar(CAMION)
    camion = unir(nuevos, "Mue_Camion_Reparto", col)
    un_material(camion, "M_Mue_Truck")
    mn, mx = colocar(camion, ANCHO_CAMION, math.radians(-90.0),
                     x_min=BORDE + 0.20, centro=(0.0, -17.2))
    # logo de ALTIPAL en las dos caras de la caja
    ancho_caja = (mx.x - mn.x) * 0.38
    x_logo = mn.x + (mx.x - mn.x) * 0.34
    for lado, rot in ((-1, (math.radians(90.0), 0.0, 0.0)),
                      (1, (math.radians(90.0), 0.0, math.pi))):
        placa("Mue_Logo_Camion_%s" % ("S" if lado < 0 else "N"),
              os.path.join(MARCA, "altipal-blanco.png"), ancho_caja,
              (x_logo, -17.2 + lado * ((mx.y - mn.y) / 2.0 + 0.02), 1.65),
              col, rot, "M_LogoAltipalCamion")

    # dos montacargas sobre la plataforma, en acero plano y sin entintado
    filtro = bpy.data.collections.get("T91_SIN_LINEAS")
    if filtro is None:
        filtro = bpy.data.collections.new("T91_SIN_LINEAS")
        bpy.context.scene.collection.children.link(filtro)
    for i, (x, y, g) in enumerate(((-8.2, -12.6, 90.0), (-8.4, 4.6, -90.0))):
        nuevos = importar(MONTACARGAS)
        mt = unir(nuevos, "Mue_Montacargas_%d" % i, col)
        un_material_plano(mt, "M_Mue_Fork" if i == 0 else "M_Mue_Fork.001")
        # sobre el anden, no sobre el patio: antes quedaban enterrados 1,22 m
        colocar(mt, ANCHO_MONTACARGAS, math.radians(g), centro=(x, y), z=SLAB)
        if filtro not in mt.users_collection:
            filtro.objects.link(mt)

    # camioneta en espera de turno, al norte
    n = copiar_furgon(col, 1.6, 9.0, math.pi)

    for _ in range(2):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
                               do_recursive=True)

    print("[CEDI360] plataforma: %d objetos, camion + %d montacargas + copia de furgon (%d piezas)"
          % (len(col.objects), 2, n))


build()
