# -*- coding: utf-8 -*-
"""
CEDI 360 - Plataforma de descargue (muelle de recibo)
=====================================================
Pone a operar el anden de 7 x 30 m que ya existe en entorno.py: demarcacion
de piso, senalizacion de vanos, equipo de carga, vehiculos atracados y la
capa de tecnologia que se enciende en Fase 2.

Coleccion:
  T85_MUELLE    demarcacion, senalizacion y equipo de piso (siempre visibles)
  T86_VEHICULOS camion de reparto, montacargas y camioneta (importar_muelle.py)

Capa:
  GRP_MUELLE    tecnologia de muelle, con driver sobre MASTER_DESPIECE:
                p7 = niveladoras, luces de muelle, LED de anden, LPR,
                camaras por muelle, intercomunicador, sensores y gabinete
                (aparece en Fase 2)

Apagada, la capa baja 60 m bajo la losa, igual que GRP_CCTV y GRP_AUTOMATIZACION.

Coordenadas: el anden va de x = -12,12 (cara exterior del muro este de la
nave) a x = -5,40 (borde donde atraca el camion), con los tres vanos en
y = -16, -8 y 0. El patio esta a 0,03 m.

Modulo autocontenido e idempotente.

Uso:
    python blender\\client.py exec --file blender\\muelle.py
"""

import math

import bpy
from mathutils import Euler, Vector

# --------------------------------------------------------------- geometria
SLAB = 1.25                 # cota del piso operativo y del anden
MURO = -12.12               # cara exterior del muro este
BORDE = -5.4                # borde del anden: linea de atraque
FONDO = -23.0               # extremo sur del anden
FRENTE = 7.0                # extremo norte del anden
PUERTAS = (-16.0, -8.0, 0.0)
ANCHO_PUERTA = 3.4
ALTO_PUERTA = 3.1           # el vano arranca en el piso del anden
CANOPIA = SLAB + 4.6        # cara inferior de la cubierta
COL_X = -4.55               # columnas de la cubierta (entorno.py)
COLUMNAS = (-19.5, -12.3, -4.0, 4.6)
APRON = 0.03                # cota del patio de maniobras

# ------------------------------------------------------------- paleta sRGB
AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
AZUL_NAVE = 0x07466E
TURQUESA = 0x5CDACE
AMARILLO = 0xFBC710
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
    mat.use_backface_culling = bool(una_cara)
    if alpha < 1.0:
        try:
            mat.blend_method = "BLEND"
        except Exception:
            pass
        mat.use_backface_culling = False
    return mat


def mats():
    """Materiales del acopio (mismos valores) y los propios del muelle."""
    material("M_Alm_Estructura", 0x39424D, emision=0x4A5764, fuerza=0.18, rugosidad=0.60, metal=0.35)
    material("M_Alm_Acero", 0x9AA6B2, emision=0x8C97A3, fuerza=0.40, rugosidad=0.40, metal=0.45)
    material("M_Alm_Ambar", AMARILLO, emision=AMARILLO, fuerza=1.4, rugosidad=0.45)
    material("M_Alm_Piso", AMARILLO, emision=AMARILLO, fuerza=0.85, rugosidad=0.60)
    material("M_Alm_Kraft", 0xB09A72, emision=0x9C855F, fuerza=0.18, rugosidad=0.85)
    material("M_Alm_Madera", 0x8A7147, emision=0x9A7F50, fuerza=0.12, rugosidad=0.88)
    material("M_Alm_Cam", 0x11171E, emision=0x1B2530, fuerza=0.15, rugosidad=0.55, metal=0.3)
    material("M_Alm_Lente", TURQUESA, emision=TURQUESA, fuerza=2.4, rugosidad=0.20)
    material("M_Alm_Luz", 0xFFF2CC, emision=0xFFE9A8, fuerza=1.5, rugosidad=0.40)
    material("M_Alm_Vidrio", 0x0C2C4A, emision=AZUL_MEDIO, fuerza=0.30, rugosidad=0.12, alpha=0.32)
    material("M_Alm_Texto", BLANCO, emision=BLANCO, fuerza=1.0, rugosidad=0.50, una_cara=True)
    material("M_Alm_TextoAzul", 0x9DC6EC, emision=0x7FB0FF, fuerza=0.95, rugosidad=0.50, una_cara=True)
    material("M_Alm_Banda", AZUL_NAVE, emision=AZUL_MEDIO, fuerza=0.24, rugosidad=0.70)
    # demarcacion de piso: prefijo M_Alm_Piso para que no se entinte
    material("M_Alm_PisoVerde", 0x1E6B3A, emision=0x2FA84F, fuerza=0.55, rugosidad=0.70)
    material("M_Alm_PisoBlanco", 0xE8EDF2, emision=0xE8EDF2, fuerza=0.75, rugosidad=0.60)
    # vehiculos y senalizacion propia de la plataforma
    material("M_Mue_Caja", 0xDDE4EA, emision=0xDCE4EC, fuerza=0.20, rugosidad=0.55, metal=0.10)
    material("M_Mue_Chasis", 0x1A1F26, emision=0x232C36, fuerza=0.15, rugosidad=0.70, metal=0.30)
    material("M_Mue_Llanta", 0x0A0E13, emision=0x121820, fuerza=0.10, rugosidad=0.90)
    material("M_Mue_Panel", 0x0B2439, emision=AZUL_MEDIO, fuerza=0.35, rugosidad=0.65)
    material("M_Mue_Rojo", 0x3A0F0C, emision=0xD2463C, fuerza=1.6, rugosidad=0.45)
    material("M_Mue_VerdeLuz", 0x2C5A18, emision=0x8FE04A, fuerza=2.6, rugosidad=0.35)
    material("M_Mue_Naranja", 0x7A3E0C, emision=0xF08A24, fuerza=1.0, rugosidad=0.55)


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
          parent=None):
    cur = bpy.data.curves.new(nombre, type="FONT")
    cur.body = cuerpo
    cur.size = tam
    cur.align_x = "CENTER"
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
    # en la copia evaluada; se reintenta tras refrescar el depsgraph
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


def pose(x, y, giro):
    """Devuelve una funcion local (lx, ly) -> mundo para piezas orientadas."""
    c, s = math.cos(giro), math.sin(giro)
    return lambda lx, ly: (x + lx * c - ly * s, y + lx * s + ly * c)


# --------------------------------------------------------------- demarcacion
def build_demarcacion(col):
    piso = bpy.data.materials["M_Alm_Piso"]
    verde = bpy.data.materials["M_Alm_PisoVerde"]
    blanco = bpy.data.materials["M_Alm_PisoBlanco"]
    texto_blanco = bpy.data.materials["M_Alm_Texto"]

    geo = Geo("Mue_Demarcacion")
    z = SLAB + 0.006

    # carril peatonal contra el muro, con sus bordes blancos
    geo.caja((-11.28, -8.0, z), (1.00, 28.8, 0.008), verde)
    for x in (-11.80, -10.76):
        geo.caja((x, -8.0, z + 0.001), (0.07, 28.8, 0.009), blanco)
    # linea amarilla de seguridad a 0,5 m del borde de atraque
    geo.caja((-5.92, -8.0, z), (0.12, 28.6, 0.008), piso)

    # zona de cargue de cada vano: 4,45 x 5,10 m
    for y in PUERTAS:
        geo.caja((-8.375, y - 2.55, z), (4.45, 0.09, 0.008), piso)
        geo.caja((-8.375, y + 2.55, z), (4.45, 0.09, 0.008), piso)
        for x in (-10.60, -6.15):
            geo.caja((x, y, z), (0.09, 5.10, 0.008), piso)

    # cebra de paso peatonal en el patio, al norte de la plataforma
    for k in range(4):
        geo.caja((-2.70, 5.35 + k * 0.70, APRON + 0.012), (4.60, 0.42, 0.010), blanco)

    geo.objeto(col, "Mue_Demarcacion")

    # numeros de muelle pintados en la zona de cargue
    for i, y in enumerate(PUERTAS):
        texto("Mue_Numero_%d" % i, "%02d" % (i + 1), (-8.40, y - 0.55, SLAB + 0.016), 1.35, col, texto_blanco, rot=(0.0, 0.0, math.radians(-90.0)))
        texto("Mue_Numero_%d_Pie" % i, "MUELLE", (-8.40, y - 1.62, SLAB + 0.016), 0.42, col, texto_blanco, rot=(0.0, 0.0, math.radians(-90.0)))

    texto("Mue_Velocidad", "10 km/h", (0.80, 11.00, APRON + 0.015), 0.85, col,
          texto_blanco, rot=(0.0, 0.0, 0.0))


# -------------------------------------------------------------------- equipo
def estiba(geo, x, y, giro=0.0, capas=2, alto=0.44):
    madera = bpy.data.materials["M_Alm_Madera"]
    kraft = bpy.data.materials["M_Alm_Kraft"]
    F = pose(x, y, giro)
    rot = (0.0, 0.0, giro)
    px, py = F(0.0, 0.0)
    geo.caja((px, py, SLAB + 0.07), (1.20, 1.00, 0.14), madera, rot=rot)
    for capa in range(capas):
        z = SLAB + 0.14 + capa * alto + alto / 2
        for dx in (-0.30, 0.30):
            for dy in (-0.24, 0.24):
                cx, cy = F(dx, dy)
                geo.caja((cx, cy, z), (0.56, 0.46, alto - 0.03), kraft, rot=rot)


def transpaleta(geo, x, y, giro=0.0):
    acero = bpy.data.materials["M_Alm_Acero"]
    estructura = bpy.data.materials["M_Alm_Estructura"]
    llanta = bpy.data.materials["M_Mue_Llanta"]
    F = pose(x, y, giro)
    rot = (0.0, 0.0, giro)
    wx, wy = F(0.0, 0.0)
    geo.caja((wx, wy, SLAB + 0.28), (1.10, 0.62, 0.30), estructura, rot=rot)
    for lado in (-1, 1):
        cx, cy = F(0.55, lado * 0.22)
        geo.caja((cx, cy, SLAB + 0.10), (0.90, 0.12, 0.06), acero, rot=rot)
    cx, cy = F(0.62, 0.0)
    geo.caja((cx, cy, SLAB + 0.78), (0.10, 0.10, 0.96), acero,
             rot=(0.0, math.radians(-18), giro))
    for lx, ly in ((-0.42, -0.24), (-0.42, 0.24), (0.40, 0.0)):
        cx, cy = F(lx, ly)
        geo.cilindro((cx, cy, SLAB + 0.10), 0.10, 0.10, llanta,
                     rot=(math.radians(90), 0.0, giro), seg=8)


def calza(geo, x, y, giro=0.0):
    naranja = bpy.data.materials["M_Mue_Naranja"]
    for k, (dx, alto) in enumerate(((0.0, 0.10), (0.07, 0.17), (0.14, 0.24))):
        geo.caja((x + dx * math.cos(giro), y + dx * math.sin(giro), APRON + alto / 2),
                 (0.09, 0.26, alto), naranja, rot=(0.0, 0.0, giro))


def cono(geo, x, y):
    naranja = bpy.data.materials["M_Mue_Naranja"]
    blanco = bpy.data.materials["M_Alm_PisoBlanco"]
    geo.caja((x, y, APRON + 0.02), (0.36, 0.36, 0.04), naranja)
    geo.cono((x, y, APRON + 0.35), 0.16, 0.03, 0.66, naranja, seg=10)
    geo.cilindro((x, y, APRON + 0.34), 0.115, 0.10, blanco, seg=10)


def build_equipo(col):
    geo = Geo("Mue_Equipo")

    # estibas en la zona de rompe-carga de cada muelle
    for x, y, capas in ((-8.40, -18.20, 2), (-7.20, -18.20, 1), (-8.40, -17.00, 2),
                        (-8.80, -5.90, 2), (-7.70, -5.90, 1),
                        (-8.90, 1.60, 2), (-7.80, 1.60, 2)):
        estiba(geo, x, y, 0.0, capas)

    # equipo de movimiento: los montacargas llegan de Sketchfab en importar_muelle.py
    transpaleta(geo, -7.10, -6.40, math.radians(90.0))

    # calzas del camion atracado en el muelle 01 y conos del extremo sur
    for lado in (-1, 1):
        calza(geo, -3.08, -16.0 + lado * 1.24, 0.0)
    for x, y in ((-6.40, -20.20), (-5.90, -19.55), (-6.95, -19.35)):
        cono(geo, x, y)

    obj = geo.objeto(col, "Mue_Equipo")
    sin_lineas([obj])


# ---------------------------------------------------------------- tecnologia
def camara_muelle(geo, x, y, z, lado=-1):
    cam = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    acero = bpy.data.materials["M_Alm_Acero"]
    geo.caja((x, y, z + 0.22), (0.06, 0.06, 0.44), acero)
    geo.caja((x + lado * 0.22, y, z), (0.44, 0.13, 0.13), cam)
    geo.cilindro((x + lado * 0.47, y, z), 0.055, 0.10, cam,
                 rot=(0.0, math.radians(90), 0.0), seg=10)
    geo.cilindro((x + lado * 0.53, y, z), 0.042, 0.04, lente,
                 rot=(0.0, math.radians(90), 0.0), seg=10)


def punto(geo, col, gp, clave, nombre, x, y, z, alto_texto=0.24):
    """Baliza rotulada, con una copia de texto por cara."""
    acero = bpy.data.materials["M_Alm_Acero"]
    lente = bpy.data.materials["M_Alm_Lente"]
    geo.cilindro((x, y, z + 0.45), 0.07, 0.90, acero, seg=8)
    geo.cilindro((x, y, z + 0.96), 0.11, 0.12, lente, seg=10)
    for sentido in (1, -1):
        giro = math.radians(90.0) if sentido > 0 else math.radians(-90.0)
        texto("Mue_Punto_%s_%d" % (clave, sentido), "%s Â· %s" % (clave, nombre),
              (x + sentido * 0.5, y, z + 1.16), alto_texto, col,
              bpy.data.materials["M_Alm_TextoAzul"],
              rot=(math.radians(90), 0.0, giro), parent=gp)


def mueble_interfono(geo, x, y, z):
    acero = bpy.data.materials["M_Alm_Acero"]
    cam = bpy.data.materials["M_Alm_Cam"]
    ambar = bpy.data.materials["M_Alm_Ambar"]
    geo.caja((x, y, z), (0.10, 0.34, 0.52), cam)
    for k in range(3):
        geo.caja((x + 0.06, y, z + 0.14 - k * 0.09), (0.02, 0.22, 0.03), acero)
    geo.cilindro((x + 0.06, y, z - 0.16), 0.05, 0.03, ambar,
                 rot=(0.0, math.radians(90), 0.0), seg=10)


def build_tecnologia(col, gp):
    acero = bpy.data.materials["M_Alm_Acero"]
    estructura = bpy.data.materials["M_Alm_Estructura"]
    cam = bpy.data.materials["M_Alm_Cam"]
    lente = bpy.data.materials["M_Alm_Lente"]
    ambar = bpy.data.materials["M_Alm_Ambar"]
    luz = bpy.data.materials["M_Alm_Luz"]
    rojo = bpy.data.materials["M_Mue_Rojo"]
    verde = bpy.data.materials["M_Mue_VerdeLuz"]
    panel = bpy.data.materials["M_Mue_Panel"]

    geo = Geo("Mue_Tecnologia")

    # niveladora de borde en el muelle 01 (el unico con camion atracado)
    geo.caja((BORDE + 0.04, -16.0, SLAB + 0.06), (0.14, 3.20, 0.14), estructura)
    geo.caja((BORDE + 0.68, -16.0, 1.22), (1.34, 3.05, 0.09), acero,
             rot=(0.0, math.radians(8.0), 0.0))
    for lado in (-1, 1):
        geo.caja((BORDE + 0.68, -16.0 + lado * 1.55, 1.30),
                 (1.34, 0.10, 0.16), ambar, rot=(0.0, math.radians(8.0), 0.0))

    # luz de muelle sobre cada vano: rojo con camion, verde libre
    for i, y in enumerate(PUERTAS):
        geo.caja((MURO + 0.10, y + 2.02, 4.54), (0.14, 0.42, 0.34), cam)
        color = rojo if i == 0 else verde
        geo.cilindro((MURO + 0.19, y + 2.02, 4.62), 0.09, 0.05, color,
                     rot=(0.0, math.radians(90), 0.0), seg=12)
        geo.cilindro((MURO + 0.19, y + 2.02, 4.46), 0.09, 0.05,
                     verde if i == 0 else rojo,
                     rot=(0.0, math.radians(90), 0.0), seg=12)

    # postes de borde: lector de placas y luminaria sobre el atraque
    for y in (-12.3, -4.0):
        geo.cilindro((COL_X, y, APRON + 1.78), 0.09, 3.55, acero, seg=10)
        geo.caja((COL_X, y, APRON + 3.56), (0.22, 0.22, 0.14), acero)
        geo.caja((COL_X - 0.22, y, APRON + 3.44), (0.40, 0.18, 0.17), cam,
                 rot=(0.0, math.radians(-16.0), 0.0))
        geo.cilindro((COL_X - 0.44, y, APRON + 3.38), 0.055, 0.09, cam,
                     rot=(0.0, math.radians(74.0), 0.0), seg=10)
        geo.cilindro((COL_X - 0.45, y, APRON + 3.27), 0.035, 0.04, rojo,
                     rot=(0.0, math.radians(74.0), 0.0), seg=8)
        geo.caja((COL_X - 0.32, y, APRON + 2.94), (0.12, 0.36, 0.20), cam,
                 rot=(0.0, math.radians(22.0), 0.0))
        geo.caja((COL_X - 0.40, y, APRON + 2.90), (0.04, 0.32, 0.14), luz,
                 rot=(0.0, math.radians(22.0), 0.0))

    # camara por muelle sobre el muro, mirando la plataforma
    for y in PUERTAS:
        geo.caja((MURO + 0.10, y + 1.50, 4.32), (0.20, 0.10, 0.10), acero)
        camara_muelle(geo, MURO + 0.16, y + 1.50, 4.30, lado=1)
    # luminarias LED del anden, sobre la banda de fachada
    for y in PUERTAS:
        for lado in (-1, 1):
            geo.caja((MURO + 0.14, y + lado * 2.15, 4.30), (0.14, 0.40, 0.18), cam,
                     rot=(0.0, 0.0, 0.0))
            geo.caja((MURO + 0.21, y + lado * 2.15, 4.24), (0.04, 0.34, 0.13), luz)

    # intercomunicador IP junto al vano 02
    mueble_interfono(geo, MURO + 0.06, -6.10, 2.35)
    # gabinete de red del muelle, con su LED de estado
    geo.caja((-11.86, -4.00, SLAB + 0.88), (0.44, 1.05, 1.75), estructura)
    geo.caja((-11.63, -4.00, SLAB + 1.62), (0.03, 0.90, 0.05), lente)
    geo.caja((-11.63, -4.00, SLAB + 0.20), (0.03, 0.90, 0.30), cam)

    # sensores de presencia de vehiculo en el borde del anden
    for y in PUERTAS:
        geo.caja((-5.28, y + 2.35, SLAB + 0.55), (0.10, 0.10, 0.60), acero)
        geo.caja((-5.34, y + 2.35, SLAB + 0.88), (0.20, 0.16, 0.14), cam)
        geo.cilindro((-5.45, y + 2.35, SLAB + 0.88), 0.035, 0.04, lente,
                     rot=(0.0, math.radians(90), 0.0), seg=8)

    obj = geo.objeto(col, "Mue_Tecnologia", parent=gp)

    menor = Geo("Mue_Tecnologia_Menuda")
    for y in PUERTAS:
        menor.caja((MURO + 0.12, y + 2.02, 4.70), (0.20, 0.46, 0.06), cam)
    obj_menor = menor.objeto(col, "Mue_Tecnologia_Menuda", parent=gp)
    sin_lineas([obj_menor])

    # rotulos: vano sobre el muro (dos caras) y banda de la cubierta
    texto_blanco = bpy.data.materials["M_Alm_Texto"]
    for i, y in enumerate(PUERTAS):
        texto("Mue_Rotulo_Muelle_%d" % i, "MUELLE %02d" % (i + 1),
              (MURO + 0.03, y, 4.72), 0.26, col, texto_blanco,
              rot=(math.radians(90), 0.0, math.radians(90)), parent=gp)
        texto("Mue_Rotulo_Muelle_%d_Int" % i, "MUELLE %02d" % (i + 1),
              (MURO - 0.32, y, 4.72), 0.26, col, texto_blanco,
              rot=(math.radians(90), 0.0, math.radians(-90)), parent=gp)

    # puntos de tecnologia rotulados
    puntos = (("M1", "LPR PLACAS", -6.30, -12.90, SLAB),
              ("M2", "CCTV MUELLE", -6.30, -10.30, SLAB),
              ("M3", "INTERCOMUNICADOR", -11.30, -7.10, SLAB),
              ("M4", "NIVELADORA", -6.30, -14.70, SLAB),
              ("M5", "LED DE ANDEN", -6.30, -8.70, SLAB))
    for clave, nombre, x, y, z in puntos:
        punto(geo, col, gp, clave, nombre, x, y, z)


# --------------------------------------------------------------------- camara
def build_camara():
    rig = coleccion("T99_RIG")
    for nombre in ("Cam_Muelle", "Cam_Muelle_Target"):
        viejo = bpy.data.objects.get(nombre)
        if viejo:
            bpy.data.objects.remove(viejo, do_unlink=True)
    tgt = bpy.data.objects.new("Cam_Muelle_Target", None)
    # el tracto camion ya no esta en el anden: se apunta un poco al este para
    # que entre completo en la lamina, con la plataforma al centro
    tgt.location = (-5.50, -14.0, 2.2)
    rig.objects.link(tgt)
    datos = bpy.data.cameras.new("Cam_Muelle")
    datos.lens = 32.0
    datos.clip_start = 0.1
    datos.clip_end = 400.0
    cam = bpy.data.objects.new("Cam_Muelle", datos)
    cam.location = (11.0, -38.0, 19.5)
    rig.objects.link(cam)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


# ---------------------------------------------------------------------- build
def build():
    col = bpy.data.collections.get("T85_MUELLE")
    if col:
        vaciar(col)
    viejo = bpy.data.objects.get("GRP_MUELLE")
    if viejo:
        bpy.data.objects.remove(viejo, do_unlink=True)

    col = coleccion("T85_MUELLE")
    mats()

    master = bpy.data.objects.get("MASTER_DESPIECE")
    if master is not None and "p7" not in master.keys():
        master["p7"] = 0
        master.update_tag()
        bpy.context.view_layer.update()
    gp = capa("GRP_MUELLE", col, "p7", "-60 * (1 - p7)")

    # el rebuild respeta la fase vigente
    if master is not None:
        fase = master.get("fase", 0)
        master["p7"] = 1 if fase >= 2 else 0
        master.update_tag()
        bpy.context.view_layer.update()

    build_demarcacion(col)
    build_equipo(col)
    build_tecnologia(col, gp)
    build_camara()

    print("[CEDI360] muelle: %d objetos, capa p7 en GRP_MUELLE (%d textos)"
          % (len(col.objects), sum(1 for o in col.objects if o.type == "FONT")))


build()
