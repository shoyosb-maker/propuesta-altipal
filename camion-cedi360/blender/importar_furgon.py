# -*- coding: utf-8 -*-
"""
CEDI 360 - Furgonetas de reparto de la fila de despacho
======================================================
Sustituye las dos unidades blockout de T80_ENTORNO por una furgoneta
blanca de paqueteria importada de Sketchfab, con el logo de la marca en
la puerta del conductor.

  1. limpia los restos de intentos anteriores y el blockout de la flota,
  2. importa el glb y aplica transformaciones,
  3. pinta los materiales con la paleta de reparto,
  4. une y decima,
  5. escala al ancho real y la apoya en el suelo con el morro hacia +y,
  6. la replica en las dos posiciones de la fila de despacho y
  7. pone el logo de ALTIPAL en una y el de FUNDASERINCO en la otra.

Atribucion exigida por la licencia CC-BY:
    "Mercedes-Benz Sprinter" por Savelliy 07
    https://sketchfab.com/3d-models/152f62800be34652af0545487129ca2e

Uso:
    python blender\\client.py exec --file blender\\importar_furgon.py
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(PROYECTO, "assets", "modelos", "sprinter-furgon.glb")
MARCA = os.path.join(PROYECTO, "assets", "marca")

ANCHO = 2.02            # ancho con espejos, como la Sprinter real
MORRO_Y = 1.20          # donde queda el frente de cada unidad
SITIOS = ((18.4, 5.60), (18.4, 11.20))   # junto a la torre de luz (20, 8)
DECIMAR = 0.32

BLANCO = 0xF7FAFC
GRIS = 0x8C97A3
NEGRO = 0x0A0A0C
MOLDURA = 0x2B313A
VIDRIO = 0x14314C

# material del modelo -> color de reparto
PALETA = {
    "Translucent_Glass_Gray": "vidrio",
    "Color_B02": "llanta",
    "Color_A25": "llanta",
    "Color_A11": "moldura",
    "Color_A01": "rin",
    "Color_A01_1": "rin",
}
COLORES = {
    "carroceria": (BLANCO, BLANCO, 0.12, 0.15),
    "vidrio": (VIDRIO, 0x2A5B84, 0.0, 0.55),
    "llanta": (NEGRO, NEGRO, 0.0, 1.0),
    "moldura": (MOLDURA, MOLDURA, 0.10, 1.0),
    "rin": (GRIS, GRIS, 0.70, 1.0),
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
    for nombre in ("IMP", "FUR", "FUR_FLOTA"):
        col = bpy.data.collections.get(nombre)
        if col:
            for o in list(col.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(col)
    for o in list(bpy.data.objects):
        if o.name.startswith(("FUR_", "Flota_")):
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


def pintar(col):
    """Pinta solo los materiales de la furgoneta, no los del resto de la escena."""
    usados = []
    for o in col.objects:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if m and m not in usados:
                usados.append(m)
    for mat in usados:
        if not mat.use_nodes:
            mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
        clave = PALETA.get(mat.name.split(".")[0].replace("_1", ""), "carroceria")
        if clave == "carroceria" and "Glass" in mat.name:
            clave = "vidrio"
        # nombre semantico: el visor pinta la furgoneta por prefijo M_Fur_
        mat.name = "M_Fur_" + clave
        base, emi, metal, alpha = COLORES[clave]
        bsdf.inputs["Base Color"].default_value = (*lin(base), 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
        bsdf.inputs["Metallic"].default_value = metal
        try:
            bsdf.inputs["Emission Color"].default_value = (*lin(emi), 1.0)
            bsdf.inputs["Emission Strength"].default_value = 0.62 if clave == "carroceria" else (
                0.1 if clave == "vidrio" else 0.28)
        except KeyError:
            pass
        if alpha < 1.0:
            for atributo, valor in (("blend_method", "BLEND"),
                                    ("surface_render_method", "BLENDED")):
                try:
                    setattr(mat, atributo, valor)
                except (AttributeError, TypeError):
                    pass


def unir_decimar(col, ratio):
    objetos = [o for o in col.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    if len(objetos) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = "FUR_Modelo"
    caras = len(obj.data.polygons)
    # fusiona costuras entre las piezas del glb antes de decimar
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    if ratio < 1.0:
        mod = obj.modifiers.new("Dec", "DECIMATE")
        mod.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.shade_smooth()
    print("[CEDI360] furgon: %d caras -> %d" % (caras, len(obj.data.polygons)))
    return obj


def encajar(col):
    mn, mx = bbox([o for o in col.objects if o.name == "FUR_Modelo"])
    factor = ANCHO / (mx.x - mn.x)
    centro_x = (mn.x + mx.x) / 2.0
    centro_y = (mn.y + mx.y) / 2.0
    pivote = Vector((centro_x, centro_y, mn.z))
    # el modelo trae el morro hacia -y: se gira para que mire a +y como el camion
    M = (Matrix.Rotation(math.pi, 4, "Z")
         @ Matrix.Scale(factor, 4)
         @ Matrix.Translation(-pivote))
    for o in col.objects:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    mn, mx = bbox([o for o in col.objects if o.name == "FUR_Modelo"])
    dy = MORRO_Y - mx.y
    for o in col.objects:
        o.location.y += dy
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in col.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = list(col.objects)[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mn, mx = bbox([o for o in col.objects if o.name == "FUR_Modelo"])
    print("[CEDI360] furgon encajada: %.2f x %.2f x %.2f (escala %.4f)"
          % (mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, factor))
    return mn, mx


def lateral(obj, y0, y1, z0, z1):
    """Mitad del ancho de la carroceria en una franja (sin espejos)."""
    valores = []
    for v in obj.data.vertices:
        p = obj.matrix_world @ v.co
        if y0 <= p.y <= y1 and z0 <= p.z <= z1:
            valores.append(abs(p.x))
    if not valores:
        return 0.0
    valores.sort()
    return valores[int(len(valores) * 0.9)]


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
    for atributo, valor in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(mat, atributo, valor)
        except (AttributeError, TypeError):
            pass
    return mat


def colocar(col, modelo, mn, mx, logos):
    alto = mx.z - mn.z
    largo = mx.y - mn.y
    # el logo va en el panel ciego de carga, detras de la puerta del piloto
    y_logo = mn.y + largo * 0.40
    z_logo = alto * 0.55
    dy_logo = mx.y - y_logo
    mitad = lateral(modelo, y_logo - 0.6, y_logo + 0.6, z_logo - 0.25, z_logo + 0.25)
    print("[CEDI360] costado del fardo: %.3f m" % mitad)
    col_fur = bpy.data.collections.get("FUR_FLOTA")
    if col_fur is None:
        col_fur = bpy.data.collections.new("FUR_FLOTA")
        padre = bpy.data.collections.get("T80_ENTORNO")
        (padre.children if padre else bpy.context.scene.collection.children).link(col_fur)
    for i, (x, y) in enumerate(SITIOS):
        copia = modelo.copy()
        copia.data = modelo.data
        copia.name = "FUR_Unidad_%d" % i
        # (x, y) es la posicion del morro de la unidad
        copia.location = Vector((x, y - mx.y, 0.0))
        col_fur.objects.link(copia)
        ruta, mat_nombre = logos[i]
        for lado in (-1, 1):
            placa("FUR_Logo_%d_%s" % (i, "D" if lado > 0 else "I"),
                  ruta, 1.55,
                  Vector((x + lado * (mitad + 0.02),
                          y - dy_logo,
                          z_logo)),
                  col_fur,
                  (math.radians(90), 0.0, math.radians(90 * lado)),
                  mat_nombre)
    bpy.data.objects.remove(modelo, do_unlink=True)
    return len(SITIOS)


def build():
    if not os.path.isfile(GLB):
        print("[CEDI360] falta el glb:", GLB)
        return
    limpiar()
    col = importar()
    normalizar(col)
    pintar(col)
    modelo = unir_decimar(col, DECIMAR)
    mn, mx = encajar(col)
    logos = ((os.path.join(MARCA, "altipal-azul.png"), "M_LogoAltipalFur"),
             (os.path.join(MARCA, "fundaserinco-azul.png"), "M_LogoFundaserincoFur"))
    n = colocar(col, modelo, mn, mx, logos)
    for _ in range(2):
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    print("[CEDI360] %d furgonetas en la fila de despacho" % n)
    print("[CEDI360] credito: Mercedes-Benz Sprinter por Savelliy 07, CC-BY")


build()
