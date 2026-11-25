# -*- coding: utf-8 -*-
"""
CEDI 360 - Identidad de marca ALTIPAL
=====================================
Pinta el modelo con la paleta real de ALTIPAL, tomada de altipal.co:

    azul       #00274B   fondo de marca y carroceria
    azul medio #0072B2   botones y acentos de la web
    azul nave  #07466E   paredes del contenedor
    verde      #9FC55A   acento de marca
    turquesa   #5CDACE   acento de datos
    amarillo   #FBC710   senalizacion y faros
    gris       #69727D   texto secundario

Ademas coloca los logos como textura sobre el modelo:
  - ALTIPAL en el lateral del contenedor y en la puerta de la cabina,
  - FUNDASERINCO en el letrero de la nave del CEDI.

Los colores van en sRGB y se convierten a lineal antes de entrar en
Blender, que es lo que espera el shader.

Modulo autocontenido. Idempotente: se puede ejecutar varias veces.

Uso:
    python blender\\client.py exec --file blender\\marca_altipal.py
"""

import math
import os

import bpy
from mathutils import Vector

PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCAS = os.path.join(PROYECTO, "assets", "marca")

COLECCION = "T06_BRANDING"

AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
AZUL_NAVE = 0x07466E
VERDE = 0x9FC55A
TURQUESA = 0x5CDACE
AMARILLO = 0xFBC710
GRIS = 0x69727D
BLANCO = 0xF2F5F8

CONT_W = 2.438
CONT_CY = -6.30
CONT_Z0 = 1.30
CONT_H = 2.896


# ------------------------------------------------------------- utilidades
def lin(hexa):
    """sRGB a lineal, que es lo que espera el shader."""
    canales = (((hexa >> 16) & 255) / 255.0, ((hexa >> 8) & 255) / 255.0, (hexa & 255) / 255.0)
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canales)


def pintar(nombre, hexa, emision=None, fuerza=0.22, rugosidad=0.55, metal=0.05, alpha=1.0):
    """Repinta un material existente; si no existe, lo crea."""
    mat = bpy.data.materials.get(nombre)
    if not mat:
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
    if not mat.use_nodes:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        return mat
    color = lin(hexa)
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = metal
    emi = lin(emision if emision is not None else hexa)
    try:
        bsdf.inputs["Emission Color"].default_value = (*emi, 1.0)
        bsdf.inputs["Emission Strength"].default_value = fuerza
    except KeyError:
        pass
    if alpha < 1.0:
        try:
            mat.blend_method = "BLEND"
        except AttributeError:
            pass
    return mat


def coleccion():
    col = bpy.data.collections.get(COLECCION)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(COLECCION)
        bpy.context.scene.collection.children.link(col)
    return col


def caja(nombre, tam, loc, col, mat, rot=(0.0, 0.0, 0.0), parent=None):
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
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def mat_logo(nombre, ruta, fuerza=1.4):
    """Logo con transparencia real: Mix Shader con Transparent BSDF."""
    imagen = bpy.data.images.load(ruta, check_existing=True)
    mat = bpy.data.materials.get(nombre)
    if not mat:
        mat = bpy.data.materials.new(nombre)
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
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    try:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = fuerza
    except KeyError:
        pass
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Metallic"].default_value = 0.0
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


def placa(nombre, ruta, ancho, loc, col, rot=(0.0, 0.0, 0.0), parent=None,
          mat_nombre=None):
    """Plano con el logo como textura, con UVs 0-1."""
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
    obj.data.materials.append(mat_logo(mat_nombre or ("M_Logo_" + nombre), ruta))
    if parent:
        obj.parent = parent
    return obj


# ------------------------------------------------------------- paleta
def pintar_camion():
    # chasis, cabina, techo, piso y llantas: azul corporativo
    pintar("M_Acero", AZUL, emision=AZUL_MEDIO, fuerza=0.30, rugosidad=0.45, metal=0.2)
    # paredes, puertas y frente del contenedor
    pintar("M_AmbarSuave", AZUL_NAVE, emision=AZUL_MEDIO, fuerza=0.26, rugosidad=0.55)
    # cajas de mercancia: verde de marca atenuado
    pintar("M_Carga", 0x6E8F3F, emision=VERDE, fuerza=0.22, rugosidad=0.6, alpha=0.95)
    # vidrios
    pintar("M_Vidrio", 0x0C2C4A, emision=AZUL_MEDIO, fuerza=0.35, rugosidad=0.15, alpha=0.55)
    # faros y acentos
    pintar("M_Ambar", AMARILLO, emision=AMARILLO, fuerza=2.2, rugosidad=0.35)
    pintar("M_Cian", TURQUESA, emision=TURQUESA, fuerza=1.2, rugosidad=0.4)
    pintar("M_MarcaBlanca", BLANCO, emision=BLANCO, fuerza=1.1, rugosidad=0.5)
    pintar("M_MarcaAmbar", AMARILLO, emision=AMARILLO, fuerza=1.8, rugosidad=0.45)
    pintar("M_MarcaCian", TURQUESA, emision=TURQUESA, fuerza=1.2, rugosidad=0.45)
    pintar("M_Tinta", 0x0A1018, emision=0x14202E, fuerza=0.15, rugosidad=0.85)


def pintar_entorno():
    pintar("M_Patio", 0x14181D, emision=0x1B2330, fuerza=0.18, rugosidad=0.9)
    pintar("M_Via", 0x11151A, emision=0x18202B, fuerza=0.18, rugosidad=0.9)
    pintar("M_Junta", 0x3A3423, emision=AMARILLO, fuerza=0.16, rugosidad=0.8)
    pintar("M_Bordillo", 0xC99B0C, emision=AMARILLO, fuerza=0.55, rugosidad=0.6)
    pintar("M_Eje_Via", AMARILLO, emision=AMARILLO, fuerza=0.7, rugosidad=0.6)
    pintar("M_Anden_Borde", AMARILLO, emision=AMARILLO, fuerza=0.8, rugosidad=0.55)
    pintar("M_Hormigon", 0x2A323B, emision=0x374252, fuerza=0.22, rugosidad=0.88)
    pintar("M_Puerta_Nave", 0x0A3556, emision=AZUL_MEDIO, fuerza=0.28, rugosidad=0.6)
    pintar("M_Nave", AZUL, emision=AZUL_MEDIO, fuerza=0.24, rugosidad=0.6)
    pintar("M_Cubierta", 0x001C36, emision=AZUL, fuerza=0.2, rugosidad=0.65)
    pintar("M_Poste", 0x3A4048, emision=0x4A525C, fuerza=0.2, rugosidad=0.7)
    pintar("M_Luz_Torre", 0xFFF2CC, emision=0xFFE9A8, fuerza=2.6, rugosidad=0.4)
    # la flota de reparto va en blanco con cabina azul
    pintar("M_Flota_Caja", BLANCO, emision=0xDCE4EC, fuerza=0.35, rugosidad=0.6)
    pintar("M_Flota_Cab", AZUL_MEDIO, emision=AZUL_MEDIO, fuerza=0.35, rugosidad=0.5)
    pintar("M_TextoCian", TURQUESA, emision=TURQUESA, fuerza=0.9)
    pintar("M_Texto", BLANCO, emision=BLANCO, fuerza=0.9)


# ------------------------------------------------------------- franjas y logos
def franjas(col, col_entorno=None):
    verde = pintar("M_MarcaVerde", VERDE, emision=VERDE, fuerza=0.55, rugosidad=0.5)
    x = CONT_W / 2 + 0.03
    z_franja = CONT_Z0 + 0.22
    for lado, nombre in ((1, "Der"), (-1, "Izq")):
        padre = bpy.data.objects.get("GRP_PARED_%s" % ("DER" if lado > 0 else "IZQ"))
        caja("BRD_Franja_%s" % nombre, (0.05, 11.6, 0.14),
             (lado * x, CONT_CY, z_franja), col, verde, parent=padre)

    # franja de marca sobre el letrero de la nave (viaja con el entorno)
    caja("BRD_Franja_Nave", (0.14, 44.0, 0.40), (-12.02, -7.0, 3.34),
         col_entorno or col, verde)


def acomodar_textos():
    """El logo ocupa el centro del lateral; el lema se corre al frente."""
    for nombre, dy in (("DET_LemaA", 4.20), ("DET_LemaB", 4.20)):
        obj = bpy.data.objects.get(nombre)
        if not obj:
            continue
        obj.location.y = CONT_CY + dy
        # tras un export los textos ya son malla: no tienen .size
        if obj.type == "FONT":
            obj.data.size = 0.30
        else:
            factor = 0.30 / 0.37
            obj.scale = (factor, factor, factor)
    # el rotulo de la nave se corre al frente para dejar el frente al logo
    rotulo = bpy.data.objects.get("Nave_Rotulo")
    if rotulo:
        rotulo.location = (-12.00, 3.6, 2.28)


def limpiar_textos():
    """El contenedor se queda solo con el logo y el lema de ALTIPAL."""
    for nombre in ("DET_Marca", "DET_Firma"):
        obj = bpy.data.objects.get(nombre)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def logos(col, col_entorno=None):
    pared = bpy.data.objects.get("GRP_PARED_DER")
    cabina = bpy.data.objects.get("GRP_CABINA")
    x_cara = CONT_W / 2 + 0.20

    # ALTIPAL centrado y grande en el lateral del contenedor
    ruta_alt = os.path.join(MARCAS, "altipal-blanco.png")
    if os.path.isfile(ruta_alt):
        placa("BRD_Logo_Altipal", ruta_alt, 3.10,
              (x_cara, CONT_CY, CONT_Z0 + 1.45), col,
              rot=(math.radians(90), 0.0, math.radians(90)),
              parent=pared, mat_nombre="M_LogoAltipal")

    # ALTIPAL en la puerta de la cabina
    ruta_cab = os.path.join(MARCAS, "altipal-blanco.png")
    if cabina and os.path.isfile(ruta_cab):
        placa("BRD_Logo_Cabina", ruta_cab, 0.78,
              (1.27, 1.60, 2.02), col,
              rot=(math.radians(90), 0.0, math.radians(90)),
              parent=cabina, mat_nombre="M_LogoAltipalCab")

    # FUNDASERINCO en el letrero de la nave: reemplaza el texto suelto
    viejo = bpy.data.objects.get("Nave_Rotulo2")
    if viejo:
        bpy.data.objects.remove(viejo, do_unlink=True)
    ruta_fun = os.path.join(MARCAS, "fundaserinco-blanco.png")
    if os.path.isfile(ruta_fun):
        placa("BRD_Logo_Fundaserinco", ruta_fun, 4.6,
              (-12.00, 10.4, 2.52), col_entorno or col,
              rot=(math.radians(90), 0.0, math.radians(90)),
              mat_nombre="M_LogoFundaserinco")


def build():
    col = coleccion()
    entorno = bpy.data.collections.get("T80_ENTORNO")
    for nombre in ("BRD_Franja_Nave", "BRD_Logo_Fundaserinco"):
        viejo = bpy.data.objects.get(nombre)
        if viejo:
            bpy.data.objects.remove(viejo, do_unlink=True)
    pintar_camion()
    pintar_entorno()
    franjas(col, entorno)
    acomodar_textos()
    limpiar_textos()
    logos(col, entorno)
    print("[CEDI360] branding: %d objetos, paleta ALTIPAL aplicada" % len(col.objects))
    return col


build()
