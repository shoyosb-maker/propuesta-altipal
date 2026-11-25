# -*- coding: utf-8 -*-
"""
CEDI 360 - Centro de acopio ALTIPAL (ampliacion del modelo)
===========================================================
Convierte la nave del entorno en el centro de acopio de gran formato que
sostiene la propuesta: 2.000 m2 de piso operativo, seis pasillos de
estanteria selectiva con el catalogo de ALTIPAL repartido por familia de
producto, centro de seguridad electronica con cuarto de monitoreo y una
capa de puntos de automatizacion.

Colecciones:
  T81_CEDI            estructura: losa, muros, columnas, cerchas, luces
  T82_RACKS           estanterias, pallets y cajas de producto
  T83_SEGURIDAD       cuarto de monitoreo, CCTV, control de acceso
  T84_AUTOMATIZACION  transportadores, sorter, AMR, RFID, envolvedora

Las capas de seguridad y automatizacion cuelgan de los empties GRP_CCTV y
GRP_AUTOMATIZACION, con drivers sobre MASTER_DESPIECE:

  p5 = capa de seguridad electronica   (aparece en Fase 1)
  p6 = capa de automatizacion          (aparece en Fase 2)

Apagadas, las capas bajan 60 m bajo la losa, igual que el holograma sale
de cuadro: no hay que tocar visibilidad desde el visor.

Coordenadas: la losa del CEDI esta a 1,25 m (nivel de anden del muelle que
ya existe en entorno.py). El muro este va en x = -12,42, sobre el anden, y
las tres puertas de carga coinciden con las del muelle (y = -16, -8 y 0).

Modulo autocontenido e idempotente.

Uso:
    python blender\\client.py exec --file blender\\almacen.py
"""

import math
import random

import bpy
from mathutils import Euler, Vector

# --------------------------------------------------------------- geometria
SLAB = 1.25                 # cota del piso operativo (nivel de anden)
HX0, HX1 = -56.0, -12.42    # muros oeste y este
HY0, HY1 = -30.0, 16.0      # muros sur y norte
MURO = 0.30
Z_ALERO = 12.0              # cordon inferior de cerchas
Z_CUMBRE = 13.20
BANDA = 3.60                # banda de fachada sobre el piso
Z_BANDA = SLAB + BANDA
PUERTAS = (-16.0, -8.0, 0.0)
PUERTA_ANCHO = 3.40
PUERTA_ALTO = 3.10

# estanteria selectiva
PARES = (-52.2, -46.4, -40.6, -34.8, -29.0, -23.2)
PASILLOS = ((-49.3, "PASILLO 1"), (-43.5, "PASILLO 2"), (-37.7, "PASILLO 3"),
            (-31.9, "PASILLO 4"), (-26.1, "PASILLO 5"))
RACK_PROF = 1.10
RACK_ALTO = 9.60
BAY = 3.00
BAYS = 10
RACK_Y0 = -19.0
NIVELES = tuple(SLAB + 0.16 + i * 2.41 for i in range(4))
PASILLO_ANCHO = 4.66
PASILLO_CORREDOR = -20.3

# ------------------------------------------------------------- paleta sRGB
AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
AZUL_NAVE = 0x07466E
VERDE = 0x9FC55A
TURQUESA = 0x5CDACE
AMARILLO = 0xFBC710
GRIS = 0x69727D
BLANCO = 0xF2F5F8


def lin(hexa):
    canales = (((hexa >> 16) & 255) / 255.0, ((hexa >> 8) & 255) / 255.0,
               (hexa & 255) / 255.0)
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                 for c in canales)


def material(nombre, hexa, emision=None, fuerza=0.0, rugosidad=0.65,
             metal=0.0, alpha=1.0, una_cara=False):
    mat = bpy.data.materials.get(nombre)
    if mat is None:
        mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color = lin(hexa)
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = metal
    try:
        bsdf.inputs["Alpha"].default_value = alpha
    except KeyError:
        pass
    try:
        emi = lin(emision if emision is not None else hexa)
        bsdf.inputs["Emission Color"].default_value = (*emi, 1.0)
        bsdf.inputs["Emission Strength"].default_value = fuerza
    except KeyError:
        pass
    # los rotulos llevan una copia por cara: si se pintan las dos caras, la
    # de atras se ve en espejo encima de la de adelante y no se lee nada
    mat.use_backface_culling = bool(una_cara)
    if alpha < 1.0:
        try:
            mat.blend_method = "BLEND"
        except Exception:
            pass
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
        mat.use_backface_culling = False
    return mat


# ------------------------------------------------------------- catalogo
# Una familia por rack: es el catalogo que ALTIPAL publica en altipal.co
FAMILIAS = (
    ("BEBIDAS Y GASEOSAS", "POSTOBON · COCA-COLA · LUX", 0x1E6FA8,
     (0.52, 0.46, 0.30)),
    ("CERVEZAS Y LICORES", "DIAGEO · FOUR LOKO · ORENDAIN", 0x8A5A1E,
     (0.34, 0.36, 0.32)),
    ("ALIMENTOS SECOS", "DIANA · LEVAPAN · HARINERA", 0xB08A3C,
     (0.50, 0.42, 0.26)),
    ("LACTEOS Y REFRIGERADOS", "ALPINA · LACTALIS · NESTLE", 0xC9D3DA,
     (0.44, 0.40, 0.24)),
    ("SNACKS Y CONFITERIA", "KELLOGG'S · NISSIN · MAYAGUEZ", 0xA4472E,
     (0.48, 0.40, 0.22)),
    ("ASEO DEL HOGAR", "SCJ · RECKITT · BRINSA", 0x2E8C8C,
     (0.46, 0.44, 0.34)),
    ("CUIDADO PERSONAL", "UNILEVER · COLGATE · KIMBERLY", 0x6E8F3F,
     (0.38, 0.36, 0.26)),
    ("SALUD Y FARMACIA", "ABBOTT · KENVUE · 3M", 0x3F7FA8,
     (0.30, 0.30, 0.20)),
    ("TABACO", "COLTABACO", 0x5A4632, (0.36, 0.34, 0.22)),
    ("LUBRICANTES SHELL", "PESADOS · MOTOS · VEHICULOS", 0xC9A227,
     (0.44, 0.34, 0.30)),
    ("ILUMINACION Y ELECTRICOS", "SIGNIFY · PHILIPS", 0x4A5F8A,
     (0.34, 0.34, 0.40)),
    ("EMPAQUES E INSUMOS", "MULTIDIMENSIONALES · AZUL K", 0x7A7F86,
     (0.52, 0.44, 0.30)),
)

CENEFA_ALTO = 10.35
_CENEFA = "M_Alm_Cenefa"


def mats_base():
    material("M_Alm_Losa", 0x1C2229, emision=0x27303A, fuerza=0.10, rugosidad=0.94)
    material("M_Alm_Muro", AZUL, emision=AZUL_MEDIO, fuerza=0.20, rugosidad=0.80)
    material("M_Alm_Banda", AZUL_NAVE, emision=AZUL_MEDIO, fuerza=0.24, rugosidad=0.70)
    material("M_Alm_Estructura", 0x39424D, emision=0x4A5764, fuerza=0.18, rugosidad=0.60, metal=0.35)
    material("M_Alm_Rack", 0x1B5C8C, emision=AZUL_MEDIO, fuerza=0.30, rugosidad=0.55, metal=0.25)
    material("M_Alm_Madera", 0x8A7147, emision=0x9A7F50, fuerza=0.12, rugosidad=0.88)
    material("M_Alm_Kraft", 0xB09A72, emision=0x9C855F, fuerza=0.18, rugosidad=0.85)
    material("M_Alm_Piso", AMARILLO, emision=AMARILLO, fuerza=0.85, rugosidad=0.60)
    material("M_Alm_Luz", 0xFFF2CC, emision=0xFFE9A8, fuerza=1.5, rugosidad=0.40)
    material("M_Alm_Vidrio", 0x0C2C4A, emision=AZUL_MEDIO, fuerza=0.30, rugosidad=0.12, alpha=0.32)
    material("M_Alm_Acero", 0x9AA6B2, emision=0x8C97A3, fuerza=0.40, rugosidad=0.40, metal=0.45)
    material("M_Alm_Pantalla", TURQUESA, emision=TURQUESA, fuerza=1.6, rugosidad=0.30)
    material("M_Alm_PantallaAlt", 0x7FB0FF, emision=0x7FB0FF, fuerza=1.2, rugosidad=0.30)
    material("M_Alm_Cam", 0x11171E, emision=0x1B2530, fuerza=0.15, rugosidad=0.55, metal=0.3)
    material("M_Alm_Lente", TURQUESA, emision=TURQUESA, fuerza=2.4, rugosidad=0.20)
    material("M_Alm_Cobertura", TURQUESA, rugosidad=0.90, alpha=0.10)
    material("M_Alm_Banda_Trans", 0x1A1F26, emision=0x232C36, fuerza=0.18, rugosidad=0.75)
    material("M_Alm_Ambar", AMARILLO, emision=AMARILLO, fuerza=1.4, rugosidad=0.45)
    material("M_Alm_Texto", BLANCO, emision=BLANCO, fuerza=1.0, rugosidad=0.50,
             una_cara=True)
    material("M_Alm_TextoAzul", 0x9DC6EC, emision=0x7FB0FF, fuerza=0.95,
             rugosidad=0.50, una_cara=True)
    material(_CENEFA, 0x0B2439, emision=AZUL_MEDIO, fuerza=0.35, rugosidad=0.65)


def mats_familias():
    for nombre, _marcas, hexa, _dims in FAMILIAS:
        clave = nombre.split()[0]
        material("M_Alm_Lab_" + clave, hexa, emision=hexa, fuerza=0.85, rugosidad=0.55)
        material("M_Alm_Fam_" + clave, hexa, emision=hexa, fuerza=1.6, rugosidad=0.50,
                 una_cara=True)


def mat_familia(nombre, prefijo):
    return bpy.data.materials["M_Alm_%s_%s" % (prefijo, nombre.split()[0])]


# ------------------------------------------------------------- constructor
CARAS = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))
ESQUINAS = ((-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5),
            (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5))


class Geo(object):
    """Acumula primitivas en una sola malla con varios materiales."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.v = []
        self.f = []
        self.m = []
        self.mats = []

    def _mat(self, mat):
        if mat.name not in self.mats:
            self.mats.append(mat.name)
        return self.mats.index(mat.name)

    def caja(self, centro, tam, mat, rot=(0.0, 0.0, 0.0)):
        m = Euler(rot, "XYZ").to_matrix()
        base = len(self.v)
        for ex, ey, ez in ESQUINAS:
            p = m @ Vector((ex * tam[0], ey * tam[1], ez * tam[2]))
            self.v.append((centro[0] + p.x, centro[1] + p.y, centro[2] + p.z))
        idx = self._mat(mat)
        for cara in CARAS:
            self.f.append(tuple(base + i for i in cara))
            self.m.append(idx)

    def cilindro(self, centro, radio, alto, mat, rot=(0.0, 0.0, 0.0), seg=12):
        m = Euler(rot, "XYZ").to_matrix()
        base = len(self.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            for z in (-alto / 2.0, alto / 2.0):
                p = m @ Vector((math.cos(a) * radio, math.sin(a) * radio, z))
                self.v.append((centro[0] + p.x, centro[1] + p.y, centro[2] + p.z))
        idx = self._mat(mat)
        for k in range(seg):
            n = (k + 1) % seg
            self.f.append((base + k * 2, base + n * 2, base + n * 2 + 1, base + k * 2 + 1))
            self.m.append(idx)
        self.f.append(tuple(base + k * 2 + 1 for k in range(seg)))
        self.m.append(idx)
        self.f.append(tuple(base + k * 2 for k in range(seg - 1, -1, -1)))
        self.m.append(idx)

    def cono(self, centro, r0, r1, alto, mat, rot=(0.0, 0.0, 0.0), seg=12):
        """Tronco de cono util para las areas de cobertura de las camaras."""
        m = Euler(rot, "XYZ").to_matrix()
        base = len(self.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            for radio, z in ((r0, -alto / 2.0), (r1, alto / 2.0)):
                p = m @ Vector((math.cos(a) * radio, math.sin(a) * radio, z))
                self.v.append((centro[0] + p.x, centro[1] + p.y, centro[2] + p.z))
        idx = self._mat(mat)
        for k in range(seg):
            n = (k + 1) % seg
            self.f.append((base + k * 2, base + n * 2, base + n * 2 + 1, base + k * 2 + 1))
            self.m.append(idx)

    def quad(self, p0, p1, p2, p3, mat):
        base = len(self.v)
        self.v.extend((p0, p1, p2, p3))
        self.f.append((base, base + 1, base + 2, base + 3))
        self.m.append(self._mat(mat))

    def objeto(self, col, nombre=None, parent=None):
        nombre = nombre or self.nombre
        malla = bpy.data.meshes.new(nombre)
        malla.from_pydata(self.v, [], self.f)
        malla.update()
        for clave in self.mats:
            malla.materials.append(bpy.data.materials[clave])
        for i, poli in enumerate(malla.polygons):
            poli.material_index = self.m[i]
        obj = bpy.data.objects.new(nombre, malla)
        col.objects.link(obj)
        if parent is not None:
            obj.parent = parent
        return obj


def texto(nombre, cuerpo, loc, tam, col, mat, rot=(math.radians(90), 0.0, 0.0),
          alinear="CENTER", parent=None):
    cur = bpy.data.curves.new(nombre, type="FONT")
    cur.body = cuerpo
    cur.size = tam
    cur.align_x = alinear
    cur.space_line = 0.92
    obj = bpy.data.objects.new(nombre, cur)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
    return obj


def coleccion(nombre):
    col = bpy.data.collections.get(nombre)
    if not col:
        col = bpy.data.collections.new(nombre)
        bpy.context.scene.collection.children.link(col)
    return col


def vaciar(col):
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


FILTRO = "T91_SIN_LINEAS"


def sin_lineas(objetos):
    """Enlaza piezas menudas al filtro de Freestyle (siguen en su coleccion)."""
    col = bpy.data.collections.get(FILTRO)
    if col is None:
        col = bpy.data.collections.new(FILTRO)
        bpy.context.scene.collection.children.link(col)
    for obj in objetos:
        if col not in obj.users_collection:
            col.objects.link(obj)


# ------------------------------------------------------------- estructura
def build_estructura(col):
    mats_base()
    geo = Geo("CEDI_Estructura")

    losa = bpy.data.materials["M_Alm_Losa"]
    muro = bpy.data.materials["M_Alm_Muro"]
    banda = bpy.data.materials["M_Alm_Banda"]
    acero = bpy.data.materials["M_Alm_Estructura"]
    piso = bpy.data.materials["M_Alm_Piso"]
    luz = bpy.data.materials["M_Alm_Luz"]

    ancho = HX1 - HX0
    largo = HY1 - HY0
    cx = (HX0 + HX1) / 2.0
    cy = (HY0 + HY1) / 2.0

    # losa y juntas de colado
    geo.caja((cx, cy, SLAB - 0.15), (ancho, largo, 0.30), losa)
    for j in range(8):
        y = HY0 + 6.0 * (j + 1)
        if y < HY1:
            geo.caja((cx, y, SLAB + 0.004), (ancho, 0.05, 0.006), piso)

    # muros de fondo: oeste y sur, a toda altura
    geo.caja((HX0 - MURO / 2, cy, (Z_CUMBRE) / 2), (MURO, largo + MURO, Z_CUMBRE), muro)
    geo.caja((cx, HY0 - MURO / 2, Z_CUMBRE / 2), (ancho + 2 * MURO, MURO, Z_CUMBRE), muro)

    # fachada este: banda de carga con tres vanos de muelle
    tramos = ((HY0, PUERTAS[0] - PUERTA_ANCHO / 2),
              (PUERTAS[0] + PUERTA_ANCHO / 2, PUERTAS[1] - PUERTA_ANCHO / 2),
              (PUERTAS[1] + PUERTA_ANCHO / 2, PUERTAS[2] - PUERTA_ANCHO / 2),
              (PUERTAS[2] + PUERTA_ANCHO / 2, HY1))
    for y0, y1 in tramos:
        geo.caja((HX1 + MURO / 2, (y0 + y1) / 2, Z_BANDA / 2),
                 (MURO, y1 - y0, Z_BANDA), banda)
    for y in PUERTAS:
        geo.caja((HX1 + MURO / 2, y, (Z_BANDA + PUERTA_ALTO) / 2),
                 (MURO, PUERTA_ANCHO, Z_BANDA - PUERTA_ALTO), banda)
        # marco y niveladora
        geo.caja((HX1 - 0.10, y, PUERTA_ALTO / 2), (0.16, 0.14, PUERTA_ALTO), acero)
        for lado in (-1, 1):
            geo.caja((HX1 - 0.10, y + lado * (PUERTA_ANCHO / 2 - 0.07),
                      PUERTA_ALTO / 2), (0.16, 0.14, PUERTA_ALTO), acero)
        geo.caja((HX1 - 0.55, y, SLAB - 0.10), (1.30, 3.20, 0.12), acero)
        geo.caja((HX1 - 0.12, y, PUERTA_ALTO + 0.16), (0.34, PUERTA_ANCHO + 0.3, 0.20), piso)

    # fachada norte: solo banda baja (el resto abierto: corte isometrico)
    geo.caja((cx, HY1 + MURO / 2, Z_BANDA / 2), (ancho, MURO, Z_BANDA), banda)

    # franja de marca sobre la banda de fachada
    geo.caja((HX1 + MURO + 0.05, cy, Z_BANDA - 0.28), (0.10, largo, 0.30),
             bpy.data.materials["M_Alm_Ambar"])

    # columnas y cerchas (retícula 12 x 6 m)
    xs = (HX0 + 0.4, HX1 - 0.4)
    ys = [HY0 + 6.0 * k for k in range(8)] + [HY1 - 0.6]
    for y in ys:
        for x in xs:
            geo.caja((x, y, Z_CUMBRE / 2), (0.42, 0.42, Z_CUMBRE), acero)
            geo.caja((x, y, SLAB + 0.55), (0.62, 0.62, 0.30), acero)
            geo.caja((x, y, Z_ALERO - 0.30), (0.70, 0.70, 0.35), acero)
    for y in ys:
        # cercha: cordones y montantes en cada vano
        geo.caja((cx, y, Z_ALERO), (ancho, 0.14, 0.20), acero)
        geo.caja((cx, y, Z_CUMBRE), (ancho, 0.14, 0.20), acero)
        vanos = (HX0, -45.0, -34.8, -23.0, HX1)
        for xa, xb in zip(vanos, vanos[1:]):
            for k in range(1, 4):
                x = xa + (xb - xa) * k / 4.0
                geo.caja((x, y, (Z_ALERO + Z_CUMBRE) / 2), (0.10, 0.10, Z_CUMBRE - Z_ALERO), acero)
            geo.caja(((xa + xb) / 2, y, (Z_ALERO + Z_CUMBRE) / 2),
                     (abs(xb - xa) * 0.94, 0.07, 0.07), acero,
                     rot=(0.0, math.atan2(Z_CUMBRE - Z_ALERO, abs(xb - xa)), 0.0))
    for x in (-49.0, -43.0, -37.0, -31.0, -25.0, -19.0):
        geo.caja((x, cy, Z_CUMBRE + 0.14), (0.10, largo, 0.12), acero)

    # luminarias de alta bahia colgadas de la cercha
    for x in (-50.0, -44.0, -38.0, -32.0, -26.0, -19.5):
        for y in (-24.0, -16.0, -8.0, 0.0, 8.0):
            geo.caja((x, y, Z_ALERO - 0.62), (2.60, 0.34, 0.10), luz)
            geo.caja((x, y, Z_ALERO - 0.30), (0.04, 0.04, 0.62), acero)

    # demarcacion de seguridad
    for x_ais, _n in PASILLOS:
        for lado in (-1, 1):
            geo.caja((x_ais + lado * 2.06, RACK_Y0 + BAYS * BAY / 2, SLAB + 0.012),
                     (0.10, BAYS * BAY, 0.008), piso)
    geo.caja((PASILLO_CORREDOR, cy, SLAB + 0.012), (0.10, largo - 2, 0.008), piso)
    geo.caja((HX1 - 3.4, cy, SLAB + 0.012), (0.10, largo - 2, 0.008), piso)

    geo.objeto(col, "CEDI_Estructura")

    # rotulos de fachada interior (se ven a traves del corte)
    texto("CEDI_Rotulo_Oeste", "CENTRO DE ACOPIO", (HX0 + 0.20, -7.0, SLAB + 6.4), 2.10,
          col, bpy.data.materials["M_Alm_TextoAzul"],
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("CEDI_Rotulo_Oeste2", "ALTIPAL · 47.300 m² DE FULFILLMENT",
          (HX0 + 0.20, -7.0, SLAB + 4.6), 0.95, col,
          bpy.data.materials["M_Alm_Texto"],
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("CEDI_Rotulo_Sur", "64.000+ POSICIONES DE ALMACENAMIENTO",
          ((HX0 + HX1) / 2, HY0 + 0.20, SLAB + 6.2), 1.25, col,
          bpy.data.materials["M_Alm_TextoAzul"],
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("CEDI_Rotulo_Recibo", "RECIBO", ((HX0 + HX1) / 2, HY0 + 0.20, SLAB + 3.0), 1.9,
          col, bpy.data.materials["M_Alm_Texto"],
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("CEDI_Rotulo_Despacho", "DESPACHO", ((HX0 + HX1) / 2, HY1 - 0.20, SLAB + 1.9), 1.7,
          col, bpy.data.materials["M_Alm_Texto"])

    # los rotulos son de una cara: la fachada sur, que es la que mira la
    # camara isometrica, lleva su propia copia hacia afuera
    for nombre, cuerpo, alto, tam, mat in (
            ("CEDI_Rotulo_Sur_Ext", "64.000+ POSICIONES DE ALMACENAMIENTO",
             SLAB + 6.2, 1.25, "M_Alm_TextoAzul"),
            ("CEDI_Rotulo_Recibo_Ext", "RECIBO", SLAB + 3.0, 1.9, "M_Alm_Texto")):
        texto(nombre, cuerpo, ((HX0 + HX1) / 2, HY0 - MURO - 0.16, alto), tam, col,
              bpy.data.materials[mat], rot=(math.radians(90), 0.0, 0.0))


# ------------------------------------------------------------- estanterias
def caja_producto(geo, x, y, z, dims, familia, etiqueta, lado):
    """Caja de carton con etiqueta de familia sobre la cara del pasillo."""
    dx, dy, dz = dims
    geo.caja((x, y, z + dz / 2), (dx, dy, dz), bpy.data.materials["M_Alm_Kraft"])
    if etiqueta:
        xl = x + lado * (dx / 2 + 0.004)
        wz, wy = dz * 0.30, dy * 0.52
        geo.quad((xl, y - wy, z + dz * 0.62), (xl, y + wy, z + dz * 0.62),
                 (xl, y + wy, z + dz * 0.62 + wz), (xl, y - wy, z + dz * 0.62 + wz),
                 mat_familia(familia, "Lab"))


# densidad por altura: las repisas bajas van llenas (picking) y las altas
# son reserva, como en un CEDI real
PESOS = ((46, 20, 24, 8, 2),
         (40, 15, 20, 15, 10),
         (25, 10, 20, 20, 25),
         (15, 5, 15, 20, 45))


def carga_pallet(geo, x, y, z, familia, dims, rnd, lado, nivel=0, etiqueta=True):
    madera = bpy.data.materials["M_Alm_Madera"]
    geo.caja((x, y, z + 0.07), (1.04, 0.96, 0.14), madera)
    patron = rnd.choices(("completo", "completo", "medio", "suelto", "vacio"),
                        weights=PESOS[min(nivel, len(PESOS) - 1)])[0]
    if patron == "vacio":
        return
    dx, dy, dz = dims
    dx = min(dx, 0.50)
    dy = min(dy, 0.44)
    capas = 3 if patron == "completo" else 2
    zz = z + 0.14
    for capa in range(capas):
        for ix in (-1, 1):
            for iy in (-1, 1):
                if patron == "medio" and capa == 1 and ix > 0 and iy > 0:
                    continue
                if patron == "suelto" and capa > 0:
                    continue
                if patron == "suelto" and (ix * iy) < 0:
                    continue
                px = x + ix * dx / 2
                py = y + iy * dy / 2
                # una etiqueta por estiba: a la vista del pasillo y abajo
                visible = etiqueta and capa == 0 and ix * lado > 0 and iy > 0
                caja_producto(geo, px, py, zz, (dx, dy, dz), familia, visible, lado)
        zz += dz


def carga_escenario(geo, rnd):
    """Estibas en recibo, despacho y el pasillo principal."""
    sitios = (
        (0, -14.4, 4.0), (1, -14.4, 6.0), (6, -14.4, 12.6), (7, -14.4, 14.4),
        (4, -30.0, -27.0), (5, -33.2, -27.0), (9, -36.4, -27.0),
        (2, -39.6, -27.0), (3, -24.0, 14.4), (8, -27.5, 14.4),
    )
    for indice, x, y in sitios:
        familia = FAMILIAS[indice]
        carga_pallet(geo, x, y, SLAB, familia[0], familia[3], rnd, 1, nivel=0,
                     etiqueta=True)


def build_racks(col, geo_cajas):
    acero = bpy.data.materials["M_Alm_Rack"]
    rnd = random.Random(360)
    largo = BAYS * BAY
    y_centro = RACK_Y0 + largo / 2

    for r in range(len(PARES) * 2):
        par = r // 2
        lado = -1 if r % 2 == 0 else 1
        xc = PARES[par] + lado * 0.57
        familia = FAMILIAS[r]
        geo = Geo("CEDI_Rack_%02d" % r)

        for b in range(BAYS + 1):
            y = RACK_Y0 + b * BAY
            for dx in (-RACK_PROF / 2 + 0.05, RACK_PROF / 2 - 0.05):
                geo.caja((xc + dx, y, SLAB + RACK_ALTO / 2), (0.10, 0.10, RACK_ALTO), acero)
        for nivel in NIVELES:
            for b in range(BAYS):
                y = RACK_Y0 + (b + 0.5) * BAY
                for dx in (-RACK_PROF / 2 + 0.05, RACK_PROF / 2 - 0.05):
                    geo.caja((xc + dx, y, nivel - 0.06), (0.06, BAY - 0.10, 0.12), acero)
        # arriostramiento de las cabezas
        for y in (RACK_Y0 + 0.05, RACK_Y0 + largo - 0.05):
            geo.caja((xc, y, SLAB + RACK_ALTO / 2), (RACK_PROF - 0.10, 0.05, 0.05), acero,
                     rot=(math.radians(28), 0.0, 0.0))

        # carga palletizada por posicion: la madera y el carton van a la malla
        # de producto, asi el entintado solo dibuja la estructura del rack
        for b in range(BAYS):
            y = RACK_Y0 + (b + 0.5) * BAY
            for n, nivel in enumerate(NIVELES):
                carga_pallet(geo_cajas, xc, y, nivel, familia[0], familia[3],
                             rnd, lado, nivel=n)
        geo.objeto(col, "CEDI_Rack_%02d" % r)

        # cenefa con la familia, en las dos caras del pasillo
        x_cara = xc + lado * (RACK_PROF / 2 + 0.02)
        geo.caja((x_cara, y_centro, CENEFA_ALTO), (0.05, largo, 0.62),
                 bpy.data.materials[_CENEFA])
        for lado_txt in (-1, 1):
            x_txt = x_cara + lado_txt * 0.035
            rot_cenefa = (math.radians(90), 0.0,
                          math.radians(90) + (0.0 if lado_txt > 0 else math.pi))
            # dos etiquetas por banda: el rack mide 30 m y una sola centrada
            # solo se lee si el operario pasa justo por el medio
            for k, dy in enumerate((-largo / 4.0, largo / 4.0)):
                texto("CEDI_Cenefa_%02d_%d_%d" % (r, lado_txt, k), familia[0],
                      (x_txt, y_centro + dy, CENEFA_ALTO - 0.13), 0.34, col,
                      mat_familia(familia[0], "Fam"), rot=rot_cenefa)

        # banderola de cabecera en los dos extremos del rack
        for lado_cab, y_cab in ((-1, RACK_Y0 - 0.05), (1, RACK_Y0 + largo + 0.05)):
            geo_cab = Geo("CEDI_Cabecera_%02d_%d" % (r, lado_cab))
            geo_cab.caja((xc, y_cab, CENEFA_ALTO), (RACK_PROF + 0.10, 0.05, 0.56),
                         bpy.data.materials[_CENEFA])
            geo_cab.objeto(col, "CEDI_Cabecera_%02d_%d" % (r, lado_cab))

    # rotulos de pasillo en el piso
    for x_ais, nombre in PASILLOS:
        texto("CEDI_Pasillo_%s" % nombre[-1], nombre, (x_ais, RACK_Y0 - 1.6, SLAB + 0.02),
              0.85, col, bpy.data.materials["M_Alm_Piso"], rot=(0.0, 0.0, 0.0))

    # banderolas colgadas sobre la boca de cada pasillo
    for i, (x_ais, nombre) in enumerate(PASILLOS):
        oeste = FAMILIAS[2 * i + 1][0]
        este = FAMILIAS[2 * i + 2][0]
        geo_ban = Geo("CEDI_Banderola_%d" % (i + 1))
        geo_ban.caja((x_ais, RACK_Y0 - 1.2, CENEFA_ALTO + 0.1),
                     (PASILLO_ANCHO, 0.06, 1.06), bpy.data.materials[_CENEFA])
        geo_ban.objeto(col, "CEDI_Banderola_%d" % (i + 1))
        for sentido in (1, -1):
            giro = math.pi if sentido > 0 else 0.0
            texto("CEDI_BanderolaTxt_%d_%d" % (i + 1, sentido),
                  "%s\n%s · %s" % (nombre, oeste, este),
                  (x_ais, RACK_Y0 - 1.2 + sentido * 0.04, CENEFA_ALTO - 0.28), 0.19, col,
                  bpy.data.materials["M_Alm_Texto"],
                  rot=(math.radians(90), 0.0, giro))


# ------------------------------------------------------------- seguridad
def uv_frente(obj):
    """UV 0-1 en el plano YZ.

    Las pantallas del muro de video se miran de frente (+x) y el visor les
    pinta encima la senal de una camara. Sin capa UV el glTF no exporta
    TEXCOORD_0 y la textura cae en un solo punto.
    """
    malla = obj.data
    ys = [v.co.y for v in malla.vertices]
    zs = [v.co.z for v in malla.vertices]
    y0, y1 = min(ys), max(ys)
    z0, z1 = min(zs), max(zs)
    ancho = (y1 - y0) or 1.0
    alto = (z1 - z0) or 1.0
    uv = malla.uv_layers.new(name="UVMap")
    for poli in malla.polygons:
        for k in range(poli.loop_start, poli.loop_start + poli.loop_total):
            co = malla.vertices[malla.loops[k].vertex_index].co
            # el exportador glTF invierte la v: se guarda 1 - v para que no
            # salga cabeza abajo en el visor
            uv.data[k].uv = ((co.y - y0) / ancho, 1.0 - (co.z - z0) / alto)


def camara_domo(geo, x, y, z, lado=1):
    cuerpo = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    geo.cilindro((x, y, z), 0.11, 0.05, cuerpo, seg=12)
    geo.cilindro((x, y, z - 0.09), 0.085, 0.10, cuerpo, seg=12)
    geo.cilindro((x, y, z - 0.15), 0.062, 0.045, lente, seg=12)


def camara_bala(geo, x, y, z, lado=1):
    cuerpo = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    geo.caja((x - lado * 0.22, y, z), (0.44, 0.12, 0.12), cuerpo)
    geo.cilindro((x + lado * 0.06, y, z), 0.055, 0.16, cuerpo,
                 rot=(0.0, math.radians(90), 0.0), seg=10)
    geo.cilindro((x + lado * 0.15, y, z), 0.045, 0.04, lente,
                 rot=(0.0, math.radians(90), 0.0), seg=10)


def camara_ptz(geo, x, y, z):
    cuerpo = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    acero = bpy.data.materials["M_Alm_Acero"]
    geo.caja((x, y, z), (0.10, 0.10, 0.34), acero)
    geo.cilindro((x, y, z - 0.28), 0.17, 0.26, cuerpo, seg=14)
    geo.cilindro((x, y, z - 0.46), 0.09, 0.10, lente, seg=12)


def build_seguridad(col, gp_cctv):
    booth_x0, booth_x1 = -20.9, -13.5
    booth_y0, booth_y1 = 7.2, 15.4
    piso = SLAB + 4.35
    alto = 4.00                 # 3,20 dejaba el muro de video fuera del techo
    bx = (booth_x0 + booth_x1) / 2
    by = (booth_y0 + booth_y1) / 2

    # acceso: descanso al sur del cuarto, puerta en el muro sur y escalera
    # que baja hacia el este por el corredor (antes arrancaba fuera de la nave)
    puerta_x0, puerta_x1 = -20.40, -19.40
    puerta_alto = 2.10
    desc_y0, desc_y1 = 5.85, booth_y0
    esc_x_top, esc_x_bot = -19.15, -13.95
    esc_y, esc_ancho = 6.52, 1.20
    esc_pelda = 16
    paso = (esc_x_top - esc_x_bot) / esc_pelda
    alza = (piso - SLAB) / esc_pelda
    angulo = math.atan2(piso - SLAB, esc_x_bot - esc_x_top)

    acero = bpy.data.materials["M_Alm_Acero"]
    vidrio = bpy.data.materials["M_Alm_Vidrio"]
    estructura = bpy.data.materials["M_Alm_Estructura"]
    pantalla = bpy.data.materials["M_Alm_Pantalla"]
    pantalla2 = bpy.data.materials["M_Alm_PantallaAlt"]
    cam = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    cober = bpy.data.materials["M_Alm_Cobertura"]
    ambar = bpy.data.materials["M_Alm_Ambar"]
    banda = bpy.data.materials["M_Alm_Banda"]

    geo = Geo("CEDI_Cuarto_Control")
    # entrepiso, descanso de la escalera, columnas y cubierta
    geo.caja((bx, by, piso), (booth_x1 - booth_x0, booth_y1 - booth_y0, 0.22), acero)
    geo.caja(((booth_x0 + esc_x_top) / 2, (desc_y0 + desc_y1) / 2, piso),
             (esc_x_top - booth_x0, desc_y1 - desc_y0, 0.22), acero)
    for x in (booth_x0 + 0.3, booth_x1 - 0.3):
        for y in (booth_y0 + 0.3, booth_y1 - 0.3):
            geo.caja((x, y, (SLAB + piso) / 2), (0.22, 0.22, piso - SLAB), estructura)
    for x_ap, y_ap in ((booth_x0 + 0.25, desc_y0 + 0.20), (esc_x_top - 0.15, desc_y0 + 0.35)):
        geo.caja((x_ap, y_ap, (SLAB + piso) / 2), (0.20, 0.20, piso - SLAB), estructura)
    geo.caja((bx, by, piso + alto + 0.10),
             (booth_x1 - booth_x0 + 0.5, booth_y1 - booth_y0 + 0.5, 0.20), estructura)

    # muro oeste ciego; muro sur ciego con el hueco de la puerta
    geo.caja((booth_x0 - 0.06, by, piso + alto / 2),
             (0.12, booth_y1 - booth_y0, alto), banda)
    for x0, x1 in ((booth_x0, puerta_x0), (puerta_x1, booth_x1)):
        geo.caja(((x0 + x1) / 2, booth_y0 - 0.06, piso + alto / 2),
                 (x1 - x0, 0.12, alto), banda)
    geo.caja(((puerta_x0 + puerta_x1) / 2, booth_y0 - 0.06,
              piso + puerta_alto + (alto - puerta_alto) / 2),
             (puerta_x1 - puerta_x0, 0.12, alto - puerta_alto), banda)
    # vidrio al este y al norte
    geo.caja((booth_x1, by, piso + alto / 2), (0.05, booth_y1 - booth_y0, alto), vidrio)
    geo.caja((bx, booth_y1, piso + alto / 2), (booth_x1 - booth_x0, 0.05, alto), vidrio)
    for y in (booth_y0 + 0.05, by, booth_y1 - 0.05):
        geo.caja((booth_x1, y, piso + alto / 2), (0.14, 0.14, alto), acero)
    for x in (booth_x0 + 0.05, bx, booth_x1 - 0.05):
        geo.caja((x, booth_y1, piso + alto / 2), (0.14, 0.14, alto), acero)

    # puerta: marco, hoja abierta hacia adentro, visor, manija y lampara
    for x in (puerta_x0, puerta_x1):
        geo.caja((x, booth_y0 - 0.06, piso + puerta_alto / 2),
                 (0.09, 0.22, puerta_alto), acero)
    geo.caja(((puerta_x0 + puerta_x1) / 2, booth_y0 - 0.06, piso + puerta_alto),
             (puerta_x1 - puerta_x0, 0.22, 0.09), acero)
    giro_puerta = 0.95
    hoja_ancho = puerta_x1 - puerta_x0 - 0.08
    hx = puerta_x0 + math.cos(giro_puerta) * hoja_ancho / 2
    hy = booth_y0 - 0.06 + math.sin(giro_puerta) * hoja_ancho / 2
    geo.caja((hx, hy, piso + puerta_alto / 2 - 0.03),
             (hoja_ancho, 0.05, puerta_alto - 0.06), banda,
             rot=(0.0, 0.0, giro_puerta))
    geo.caja((hx + math.cos(giro_puerta) * 0.10, hy + math.sin(giro_puerta) * 0.10,
              piso + 1.52), (0.52, 0.03, 0.40), vidrio, rot=(0.0, 0.0, giro_puerta))
    geo.caja((hx + math.cos(giro_puerta) * 0.34, hy + math.sin(giro_puerta) * 0.34,
              piso + 1.02), (0.05, 0.05, 0.24), acero, rot=(0.0, 0.0, giro_puerta))
    geo.caja(((puerta_x0 + puerta_x1) / 2, booth_y0 - 0.24, piso + puerta_alto + 0.26),
             (0.46, 0.18, 0.09), ambar)

    # escalera: peldaños, zancas, pasamanos y baranda del descanso
    for k in range(esc_pelda):
        x = esc_x_bot + (k + 0.5) * paso
        z = SLAB + (k + 1) * alza
        geo.caja((x, esc_y, z - 0.025), (paso + 0.02, esc_ancho, 0.05), acero)
        geo.caja((x + paso * 0.40, esc_y + 0.0, z + 0.006),
                 (0.05, esc_ancho, 0.012), ambar)
    largo_esc = math.hypot(esc_x_top - esc_x_bot, piso - SLAB)
    for y in (esc_y - esc_ancho / 2 - 0.04, esc_y + esc_ancho / 2 + 0.04):
        geo.caja(((esc_x_top + esc_x_bot) / 2, y, (SLAB + piso) / 2 - 0.20),
                 (largo_esc + 0.25, 0.07, 0.26), estructura, rot=(0.0, angulo, 0.0))
        geo.caja(((esc_x_top + esc_x_bot) / 2, y, (SLAB + piso) / 2 + 0.82),
                 (largo_esc + 0.20, 0.05, 0.05), acero, rot=(0.0, angulo, 0.0))
        for t in (0.10, 0.34, 0.58, 0.82, 0.98):
            x = esc_x_bot + (esc_x_top - esc_x_bot) * t
            z = SLAB + (piso - SLAB) * t
            geo.caja((x, y, z + 0.44), (0.045, 0.045, 0.88), acero)

    def baranda(x0, y0, x1, y1, z):
        largo = math.hypot(x1 - x0, y1 - y0)
        giro = math.atan2(y1 - y0, x1 - x0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        geo.caja((cx, cy, z + 1.05), (largo, 0.05, 0.05), acero, rot=(0.0, 0.0, giro))
        geo.caja((cx, cy, z + 0.55), (largo, 0.04, 0.04), acero, rot=(0.0, 0.0, giro))
        n = max(1, int(largo / 0.65))
        for k in range(n + 1):
            px = x0 + (x1 - x0) * k / n
            py = y0 + (y1 - y0) * k / n
            geo.caja((px, py, z + 0.53), (0.05, 0.05, 1.06), acero)

    # el borde este del descanso es la llegada de la escalera: va sin baranda
    baranda(booth_x0 + 0.04, desc_y0 + 0.04, esc_x_top, desc_y0 + 0.04, piso)
    baranda(booth_x0 + 0.04, desc_y0 + 0.04, booth_x0 + 0.04, desc_y1, piso)

    geo.objeto(col, "CEDI_Cuarto_Control", parent=gp_cctv)

    texto("CEDI_Rotulo_Control", "CENTRO DE SEGURIDAD ELECTRONICA",
          (booth_x1 + 0.06, by, piso + alto - 0.42), 0.30, col,
          bpy.data.materials["M_Alm_TextoAzul"],
          rot=(math.radians(90), 0.0, math.radians(90)), parent=gp_cctv)
    texto("CEDI_Rotulo_Acceso", "ACCESO · SALA DE MONITOREO",
          ((puerta_x0 + puerta_x1) / 2, booth_y0 - 0.20, piso + puerta_alto + 0.54),
          0.17, col, bpy.data.materials["M_Alm_TextoAzul"],
          rot=(math.radians(90), 0.0, 0.0), parent=gp_cctv)
    # ---------------- equipos (capa que enciende la Fase 1)
    eq = Geo("CEDI_Seguridad_Equipos")
    # muro de video 4 x 3, dentro de los 4 m de altura del cuarto. Los marcos
    # van con el resto del equipo, pero cada pantalla sale como objeto suelto:
    # el visor le pone a cada una la senal de una camara distinta
    for i in range(4):
        for j in range(3):
            px = booth_x0 + 0.10
            py = booth_y0 + 1.90 + i * 1.55
            pz = piso + 1.15 + j * 0.86
            eq.caja((px - 0.04, py, pz), (0.10, 1.32, 0.78), cam)
            nombre = "CEDI_VideoWall_%d_%d" % (i, j)
            vid = Geo(nombre)
            vid.caja((px + 0.02, py, pz), (0.02, 1.22, 0.68),
                     pantalla if (i + j) % 2 == 0 else pantalla2)
            uv_frente(vid.objeto(col, nombre, parent=gp_cctv))
    # mesas de operacion y sillas
    for i, py in enumerate((booth_y0 + 2.2, booth_y0 + 4.2, booth_y0 + 6.2)):
        eq.caja((bx - 0.55, py, piso + 0.85), (1.50, 1.30, 0.08), acero)
        for dx in (-0.65, 0.65):
            eq.caja((bx - 0.55 + dx, py, piso + 0.42), (0.08, 1.10, 0.84), acero)
        eq.caja((bx - 1.05, py, piso + 1.22), (0.06, 0.86, 0.50), cam)
        eq.caja((bx - 1.00, py, piso + 1.22), (0.02, 0.78, 0.42), pantalla2)
        eq.cilindro((bx - 0.10, py, piso + 0.50), 0.26, 0.10, cam, seg=10)
        eq.caja((bx + 0.02, py, piso + 0.80), (0.10, 0.44, 0.44), cam)
    # gabinetes de grabacion y respaldo
    for i, py in enumerate((booth_y1 - 1.0, booth_y1 - 1.9)):
        eq.caja((booth_x0 + 0.62, py, piso + 1.05), (0.72, 0.80, 2.10), cam)
        for k in range(7):
            eq.caja((booth_x0 + 1.00, py, piso + 0.35 + k * 0.25), (0.03, 0.56, 0.06), lente)
    eq.caja((booth_x0 + 1.75, booth_y1 - 1.9, piso + 0.75), (0.80, 0.70, 1.50),
            bpy.data.materials["M_Alm_Banda"])
    eq.caja((booth_x0 + 2.20, booth_y1 - 1.9, piso + 1.30), (0.03, 0.30, 0.20), lente)

    # camaras interiores y exteriores
    domos = [(x, y) for x in (-49.3, -43.5, -37.7, -31.9, -26.1, PASS_Y_CORR)
             for y in (-12.0, 0.0, 8.0)]
    for x, y in domos:
        camara_domo(eq, x, y, Z_ALERO - 1.1)
        eq.cilindro((x, y, SLAB + 0.03), 2.60, 0.02, cober, seg=18)
    for y in PUERTAS:
        camara_bala(eq, HX1 - 1.5, y, Z_BANDA - 0.55, lado=1)
        camara_bala(eq, HX1 - 1.6, y + 2.2, Z_BANDA - 0.80, lado=1)
    for x, y in ((HX0 + 1.2, HY0 + 1.2), (HX1 - 1.2, HY0 + 1.2),
                 (HX0 + 1.2, HY1 - 1.2), (HX1 - 1.4, HY1 - 1.4)):
        camara_ptz(eq, x, y, Z_ALERO - 0.8)
    camara_bala(eq, booth_x1 + 0.4, booth_y0 + 2.0, piso + 2.6, lado=-1)
    camara_bala(eq, booth_x1 + 0.4, booth_y1 - 2.0, piso + 2.6, lado=-1)

    # control de acceso: torniquete y lectores
    for k in range(3):
        eq.caja((-19.6, -24.0 + k * 1.05, SLAB + 0.50), (0.18, 0.90, 1.00), acero)
    eq.caja((-19.6, -25.6, SLAB + 0.95), (0.20, 0.24, 0.30), cam)
    eq.caja((-19.6, -25.6, SLAB + 1.02), (0.16, 0.06, 0.06), lente)
    eq.caja((HX1 - 0.9, -13.9, Z_BANDA - 1.2), (0.10, 0.18, 0.28), cam)
    eq.objeto(col, "CEDI_Seguridad_Equipos", parent=gp_cctv)

    texto("CEDI_Rotulo_VideoWall", "CCTV · 24 CAMARAS · ANALITICA DE VIDEO",
          (booth_x0 + 0.14, by, piso + 0.55), 0.26, col,
          bpy.data.materials["M_Alm_Texto"], parent=gp_cctv)


PASS_Y_CORR = -20.3


# ------------------------------------------------------------- automatizacion
def transportador(geo, x, y0, y1, z, ancho=1.20):
    estructura = bpy.data.materials["M_Alm_Estructura"]
    banda = bpy.data.materials["M_Alm_Banda_Trans"]
    acero = bpy.data.materials["M_Alm_Acero"]
    lente = bpy.data.materials["M_Alm_Lente"]
    largo = y1 - y0
    cy = (y0 + y1) / 2
    geo.caja((x, cy, z), (ancho, largo, 0.05), banda)
    for lado in (-1, 1):
        geo.caja((x + lado * (ancho / 2 + 0.03), cy, z + 0.09),
                 (0.06, largo, 0.14), acero)
        geo.caja((x + lado * (ancho / 2 + 0.06), cy, z + 0.17),
                 (0.02, largo, 0.03), lente)
    pasos = max(2, int(largo / 0.62))
    for k in range(pasos + 1):
        y = y0 + largo * k / pasos
        geo.cilindro((x, y, z + 0.035), 0.045, ancho - 0.06, banda,
                     rot=(0.0, math.radians(90), 0.0), seg=8)
    for k in range(int(largo / 2.4) + 1):
        y = y0 + k * 2.4
        if y > y1:
            break
        for lado in (-1, 1):
            geo.caja((x + lado * (ancho / 2 - 0.06), y, SLAB + 0.36), (0.08, 0.08, 0.72),
                     estructura)


def rueda(geo, x, y, z, ancho=0.10):
    llanta = bpy.data.materials["M_Alm_Cam"]
    geo.cilindro((x, y, z), 0.10, ancho, llanta, rot=(0.0, math.radians(90), 0.0), seg=10)


def amr(geo, x, y, giro=0.0):
    cuerpo = bpy.data.materials["M_Alm_Banda"]
    lente = bpy.data.materials["M_Alm_Lente"]
    acero = bpy.data.materials["M_Alm_Acero"]
    rot = (0.0, 0.0, giro)
    geo.caja((x, y, SLAB + 0.18), (1.15, 0.76, 0.24), cuerpo, rot=rot)
    geo.caja((x, y, SLAB + 0.32), (1.00, 0.62, 0.04), acero, rot=rot)
    geo.caja((x, y, SLAB + 0.36), (0.42, 0.32, 0.10), lente, rot=rot)
    geo.cilindro((x - 0.40, y, SLAB + 0.42), 0.07, 0.14, acero, seg=10)
    for dx in (-0.38, 0.38):
        for dy in (-0.32, 0.32):
            rueda(geo, x + dx, y + dy, SLAB + 0.10, 0.12)


def build_automatizacion(col, gp_auto):
    acero = bpy.data.materials["M_Alm_Acero"]
    estructura = bpy.data.materials["M_Alm_Estructura"]
    ambar = bpy.data.materials["M_Alm_Ambar"]
    lente = bpy.data.materials["M_Alm_Lente"]
    cuerpo = bpy.data.materials["M_Alm_Banda"]
    z_belt = SLAB + 0.82

    geo = Geo("CEDI_Automatizacion_Transporte")

    # linea troncal de recibo hasta el sorter
    transportador(geo, -16.6, -26.0, 8.6, z_belt)
    # curva de enlace al sorter (segmentos girados)
    cx, cy, radio = -20.6, 8.6, 4.0
    for k in range(10):
        a0 = math.pi * k / 20.0
        px = cx + radio * math.cos(a0)
        py = cy + radio * math.sin(a0)
        geo.caja((px, py, z_belt), (1.20, 1.30, 0.05), bpy.data.materials["M_Alm_Banda_Trans"],
                 rot=(0.0, 0.0, a0 + math.pi / 2))
        for lado in (-1, 1):
            geo.caja((px + lado * 0.63 * math.cos(a0 + math.pi / 2),
                      py + lado * 0.63 * math.sin(a0 + math.pi / 2), z_belt + 0.09),
                     (0.06, 1.30, 0.14), acero, rot=(0.0, 0.0, a0 + math.pi / 2))
        if k % 3 == 0:
            geo.caja((px, py, SLAB + 0.36), (1.20, 0.10, 0.72), estructura)

    # sorter de bandejas cruzadas con diez salidas
    sx0, sx1 = -47.0, -20.6
    transportador(geo, (sx0 + sx1) / 2, 11.4, 12.6, z_belt + 0.30, ancho=(sx1 - sx0))
    for k in range(11):
        x = sx0 + 1.0 + k * 2.45
        geo.caja((x, 12.0, z_belt + 0.42), (1.10, 1.10, 0.08), acero)
        geo.caja((x, 11.1, z_belt + 0.42), (1.10, 1.30, 0.05), acero,
                 rot=(math.radians(-18), 0.0, 0.0))
        geo.caja((x, 10.45, z_belt + 0.30), (1.06, 0.10, 0.06), ambar)
        geo.caja((x, 10.4, SLAB + 0.55), (0.10, 0.10, 1.10), estructura)
        geo.caja((x, 10.35, SLAB + 1.12), (0.44, 0.30, 0.06), lente)

    # envuelvedora de estiba
    wx, wy = -21.4, 13.6
    geo.cilindro((wx, wy, SLAB + 0.06), 0.95, 0.12, estructura, seg=18)
    geo.cilindro((wx, wy, SLAB + 0.13), 0.98, 0.03, lente, seg=18)
    geo.cilindro((wx, wy, SLAB + 0.85), 0.80, 1.40, bpy.data.materials["M_Alm_Kraft"], seg=14)
    geo.caja((wx + 1.30, wy, SLAB + 1.30), (0.14, 0.14, 2.60), acero)
    geo.caja((wx + 1.00, wy, SLAB + 2.45), (0.60, 0.16, 0.16), acero)
    geo.cilindro((wx + 0.78, wy, SLAB + 2.30), 0.16, 0.24, cuerpo,
                 rot=(math.radians(90), 0.0, 0.0), seg=12)

    # portales de lectura RFID en cada puerta de muelle
    for y in PUERTAS:
        for lado in (-1, 1):
            geo.caja((HX1 - 2.2, y + lado * 1.85, SLAB + 2.10), (0.16, 0.16, 4.20), acero)
            geo.caja((HX1 - 2.12, y + lado * 1.85, SLAB + 3.20), (0.10, 0.44, 1.30), lente)
        geo.caja((HX1 - 2.2, y, SLAB + 4.24), (0.16, 3.90, 0.16), acero)

    # robots moviles en los pasillos
    for x, y, g in ((-31.9, -9.0, 0.0), (-37.7, 2.5, math.radians(180)),
                    (-43.5, -14.0, 0.0), (-49.3, 4.0, math.radians(90)),
                    (-20.3, -18.0, 0.0)):
        amr(geo, x, y, g)

    # puntos de automatizacion: balizas con rotulo
    puntos = (
        ("A1", "LECTOR RFID", HX1 - 2.2, -12.0, SLAB),
        ("A2", "SORTER", -30.0, 12.0, SLAB + 1.4),
        ("A3", "AMR / AGV", -37.7, 2.5, SLAB + 0.9),
        ("A4", "ENVOLVEDORA", -21.4, 13.6, SLAB + 2.8),
        ("A5", "SENSOR IoT", -40.6, 4.0, SLAB + 1.2),
        ("A6", "CONTROL DE ACCESO", -19.6, -24.0, SLAB + 1.2),
        ("A7", "VIDEOANALITICA", -17.0, 11.5, SLAB + 8.62),
        ("A8", "ILUMINACION", -25.0, -6.0, SLAB + 1.2),
    )
    for clave, nombre, x, y, z in puntos:
        geo.cilindro((x, y, z + 0.55), 0.09, 1.10, acero, seg=8)
        geo.cilindro((x, y, z + 1.16), 0.13, 0.14, lente, seg=10)
        for sentido in (1, -1):
            giro = math.pi if sentido > 0 else 0.0
            texto("CEDI_Punto_%s_%d" % (clave, sentido), "%s · %s" % (clave, nombre),
                  (x + 0.9, y + sentido * 0.03, z + 1.30), 0.26, col,
                  bpy.data.materials["M_Alm_TextoAzul"],
                  rot=(math.radians(90), 0.0, giro), parent=gp_auto)

    geo.objeto(col, "CEDI_Automatizacion", parent=gp_auto)

    # sensores IoT sobre las estanterias
    iot = Geo("CEDI_Sensores_IoT")
    for x_ais, _n in PASILLOS:
        for k in range(5):
            y = RACK_Y0 + 2.0 + k * 6.4
            iot.caja((x_ais + 2.2, y, SLAB + RACK_ALTO + 0.06), (0.16, 0.16, 0.12), lente)
    iot.objeto(col, "CEDI_Sensores_IoT", parent=gp_auto)


# ------------------------------------------------------------- capas
def capa(nombre, col, prop, expresion):
    obj = bpy.data.objects.get(nombre)
    if obj is None:
        obj = bpy.data.objects.new(nombre, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 1.0
        col.objects.link(obj)
    master = bpy.data.objects.get("MASTER_DESPIECE")
    if master is None:
        return obj
    # el driver solo queda valido si MASTER_DESPIECE ya tiene la propiedad
    # en la copia evaluada; se reintenta una vez tras refrescar el depsgraph
    for intento in range(3):
        obj.animation_data_clear()
        # la base de la capa es el origen: si se deja el ultimo valor que
        # escribio el driver (-60), el horneado del glb queda corrido
        obj.location = (0.0, 0.0, 0.0)
        fc = obj.driver_add("location", 2)
        drv = fc.driver
        drv.type = "SCRIPTED"
        var = drv.variables.new()
        var.name = prop
        var.type = "SINGLE_PROP"
        var.targets[0].id = master
        var.targets[0].data_path = '["%s"]' % prop
        drv.expression = expresion
        master.update_tag()
        bpy.context.view_layer.update()
        if drv.is_valid or intento == 2:
            if not drv.is_valid:
                print("[CEDI360] driver %s de %s no valido" % (prop, nombre))
            return obj
    return obj


def build_rig():
    rig = coleccion("T99_RIG")
    prefijos = ("Cam_CEDI", "Cam_Pasillo", "Cam_Control", "Cam_Despacho",
                "Cam_Fachada", "Cam_Sorter")
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefijos):
            bpy.data.objects.remove(obj, do_unlink=True)

    def camara(nombre, loc, objetivo, escala=78.0, ortho=True, lente=35.0):
        tgt = bpy.data.objects.new(nombre + "_Target", None)
        tgt.location = objetivo
        rig.objects.link(tgt)
        datos = bpy.data.cameras.new(nombre)
        if ortho:
            datos.type = "ORTHO"
            datos.ortho_scale = escala
        else:
            datos.lens = lente
            datos.clip_start = 0.1
            datos.clip_end = 400.0
        cam = bpy.data.objects.new(nombre, datos)
        cam.location = loc
        rig.objects.link(cam)
        c = cam.constraints.new("TRACK_TO")
        c.target = tgt
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        return cam

    centro = ((HX0 + HX1) / 2, (HY0 + HY1) / 2, 0.0)
    camara("Cam_CEDI", (centro[0] + 52.0, centro[1] + 50.0, 42.0),
           (centro[0] + 7.0, centro[1] + 5.0, 4.6), escala=96.0)
    camara("Cam_Pasillo", (-43.5, -24.0, SLAB + 2.10), (-40.0, 12.0, SLAB + 2.60),
           ortho=False, lente=30.0)
    camara("Cam_Control", (-2.4, -3.4, 13.8), (-18.0, 10.4, 6.8),
           ortho=False, lente=30.0)
    camara("Cam_Despacho", (-23.0, 12.2, 3.1), (-43.0, 12.6, 2.4),
           ortho=False, lente=30.0)
    camara("Cam_Fachada", (2.0, 6.0, 6.5), (-12.6, 4.0, 2.6),
           ortho=False, lente=30.0)

    isometrica = bpy.data.objects.get("Cam_Isometrica")
    if isometrica:
        bpy.context.scene.camera = isometrica


def build():
    for nombre in ("T81_CEDI", "T82_RACKS", "T83_SEGURIDAD", "T84_AUTOMATIZACION"):
        col = bpy.data.collections.get(nombre)
        if col:
            vaciar(col)
    for nombre in ("GRP_CCTV", "GRP_AUTOMATIZACION"):
        viejo = bpy.data.objects.get(nombre)
        if viejo:
            bpy.data.objects.remove(viejo, do_unlink=True)

    col_cedi = coleccion("T81_CEDI")
    col_racks = coleccion("T82_RACKS")
    col_seg = coleccion("T83_SEGURIDAD")
    col_auto = coleccion("T84_AUTOMATIZACION")

    mats_base()
    mats_familias()

    master = bpy.data.objects.get("MASTER_DESPIECE")
    for prop in ("p5", "p6"):
        if master is not None and prop not in master.keys():
            master[prop] = 0
    if master is not None:
        master.update_tag()
        bpy.context.view_layer.update()

    gp_cctv = capa("GRP_CCTV", col_seg, "p5", "-60 * (1 - p5)")
    gp_auto = capa("GRP_AUTOMATIZACION", col_auto, "p6", "-60 * (1 - p6)")

    # las capas siguen la fase vigente para que un rebuild no las apague
    if master is not None:
        fase = master.get("fase", 0)
        master["p5"] = 1 if fase >= 1 else 0
        master["p6"] = 1 if fase >= 2 else 0
        master.update_tag()
        bpy.context.view_layer.update()

    build_estructura(col_cedi)

    geo_cajas = Geo("CEDI_Producto")
    build_racks(col_racks, geo_cajas)
    carga_escenario(geo_cajas, random.Random(3600))
    geo_cajas.objeto(col_racks, "CEDI_Producto")

    build_seguridad(col_seg, gp_cctv)
    build_automatizacion(col_auto, gp_auto)
    build_rig()

    # las cajas de producto son miles de aristas: fuera del entintado
    menudos = [o for o in col_racks.objects if o.name.startswith("CEDI_Producto")]
    menudos += [o for o in col_auto.objects if o.name.startswith("CEDI_Sensores")]
    sin_lineas(menudos)

    print("[CEDI360] almacen: %d estructura, %d racks, %d seguridad, %d automatizacion"
          % (len(col_cedi.objects), len(col_racks.objects), len(col_seg.objects),
             len(col_auto.objects)))
    return col_cedi


build()
