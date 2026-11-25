# -*- coding: utf-8 -*-
"""
CEDI 360 - Programa de areas nuevas del CEDI
============================================
Levanta las areas que la propuesta necesita para poder recorrerse dentro del
modelo: cada eje y cada frente de operacion tiene un sitio fisico donde
mostrarse.

Colecciones (todas visibles en cualquier fase, sin capa propia):
  T87_FRIO      pabellon de frio exento, con su monitoreo
  T88_ADMIN     area administrativa con sala de juntas acristalada
  T89_ENERGIA   pabellon electrico exento: subestacion, tablero y UPS
  T90_ANEXO     piso 2 del anexo, pasillo tecnico y jardin de acceso
  T92_REDES     sala tecnica de redes, racks y puntos de acceso

Coordenadas: nave de x -62 a -12,42 y de y -30 a 16, piso a SLAB = 1,25.
El frio y la energia salen de la nave: dos pabellones exentos al oeste, sobre
una plataforma comun, unidos por un pasillo acristalado y servidos por un
jardin que llega a la puerta de personal de la nave. La administracion queda
en el anexo norte y las redes en su piso 2.

Modulo autocontenido e idempotente.

Uso:
    python blender\\client.py exec --file blender\\programa.py
"""

import math

import bpy
from mathutils import Euler, Vector

# --------------------------------------------------------------- geometria
SLAB = 1.25
HX0, HX1 = -62.0, -12.42
HY0, HY1 = -30.0, 16.0

# Reparto del programa: cada area en su propia zona, sin compartir esquina.
#   frio     pabellon exento al oeste de la nave, con su propia camara
#   energia  pabellon exento al oeste, al norte del frio
#   pasillo  corredor acristalado que sirve a los dos pabellones
#   jardin   patio verde entre el pasillo y la fachada oeste de la nave
#   admin    edificio anexo, fuera de la nave, al norte
#   redes    entrepiso junto al cuarto de control (piso de arriba)
FRIO = (-96.00, -78.00, -30.00, -16.00)     # 18 x 14 m
FRIO_ALTO = 6.40                            # de SLAB hacia arriba
ADMIN = (-38.00, -26.00, 21.00, 29.00)      # 12 x 8 m, anexo exterior
ADMIN_ALTO = 4.10
ENE = (-96.00, -78.00, -12.00, 0.00)        # 18 x 12 m
RED = (-36.20, -31.20, 24.30, 28.00)        # sala tecnica en el piso 2 del anexo
RED_Z0 = SLAB + 4.30
PASILLO = (-78.00, -74.00, -30.00, 0.00)    # corredor acristalado de 4 x 30 m
JARDIN = (-74.00, -62.30, -30.00, 0.00)     # patio ajardinado de 12 x 30 m
PLATAFORMA = (-97.00, -62.30, -31.50, 1.50)  # plataforma comun a cota SLAB
ACCESO_Y = -16.00                            # puerta de personal de la nave
MURO_OESTE = HX0 - 0.30                      # cara exterior del muro oeste
ACCESO_N_X = -36.80                          # eje de la puerta norte, con el anexo
JARDIN_NORTE = (-52.00, -20.00)              # franja verde entre nave y anexo

# ------------------------------------------------------------- paleta sRGB
AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
AZUL_NAVE = 0x07466E
TURQUESA = 0x5CDACE
AMARILLO = 0xFBC710
BLANCO = 0xF2F5F8
GRIS = 0x69727D


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
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
        mat.use_backface_culling = False
    return mat


def mats():
    # cuarto frio: panel sanitario blanco, piso azul, equipo galvanizado
    material("M_Frio_Caja", 0xDCE8F0, emision=0xE8F2F8, fuerza=0.26,
             rugosidad=0.80)
    material("M_Frio_Panel", 0xE6EDF2, emision=0xF2F8FC, fuerza=0.30,
             rugosidad=0.45)
    material("M_Frio_Cielo", 0xDCE6EC, emision=0xEAF2F7, fuerza=0.22,
             rugosidad=0.55)
    material("M_Frio_Piso", 0x27454F, emision=0x3C6E7C, fuerza=0.20,
             rugosidad=0.80)
    material("M_Frio_Zocalo", 0x9AA6B2, emision=0x8C97A3, fuerza=0.20,
             rugosidad=0.60, metal=0.30)
    material("M_Frio_Puerta", 0x1E4C63, emision=AZUL_MEDIO, fuerza=0.30,
             rugosidad=0.45)
    material("M_Frio_Unidad", 0xC9D3DA, emision=0xDCE4EA, fuerza=0.28,
             rugosidad=0.50, metal=0.25)
    material("M_Frio_Rejilla", 0x39424D, emision=0x2C3A46, fuerza=0.10,
             rugosidad=0.70)
    material("M_Frio_Tubo", 0xB08A3C, emision=0x8A6C2A, fuerza=0.10,
             rugosidad=0.55, metal=0.40)
    material("M_Frio_Sensor", 0x11171E, emision=0x1B2530, fuerza=0.15,
             rugosidad=0.55, metal=0.30)
    material("M_Frio_Lente", TURQUESA, emision=TURQUESA, fuerza=2.2,
             rugosidad=0.25)
    material("M_Frio_Led", 0x9FC55A, emision=0x9FC55A, fuerza=2.0,
             rugosidad=0.30)
    material("M_Frio_Alarma", 0xFBC710, emision=0xFBC710, fuerza=1.8,
             rugosidad=0.35)
    # administracion
    material("M_Adm_Muro", 0x3A4E60, emision=0x4E6A80, fuerza=0.30,
             rugosidad=0.75)
    material("M_Adm_Panel", 0x4A6478, emision=0x5E7C92, fuerza=0.26,
             rugosidad=0.80)
    material("M_Adm_Vidrio", 0x0C2C4A, emision=AZUL_MEDIO, fuerza=0.18,
             rugosidad=0.10, alpha=0.16)
    material("M_Adm_Piso", 0x36434F, emision=0x46565F, fuerza=0.22,
             rugosidad=0.85)
    material("M_Adm_Mesa", 0x6B4A2E, emision=0x3A2A1A, fuerza=0.10,
             rugosidad=0.45)
    material("M_Adm_Silla", 0x1B2530, emision=0x24313D, fuerza=0.12,
             rugosidad=0.70)
    material("M_Adm_Mueble", 0x25333E, emision=0x33454F, fuerza=0.16,
             rugosidad=0.60)
    material("M_Adm_Luz", 0xFFF6DA, emision=0xFFEFC2, fuerza=2.2,
             rugosidad=0.35)
    material("M_Adm_TV", 0x0A1018, emision=0x14202E, fuerza=0.10,
             rugosidad=0.30)
    material("M_Adm_TVMarco", 0x11171E, emision=0x1B2530, fuerza=0.12,
             rugosidad=0.45, metal=0.35)
    # energia
    material("M_Ene_Cabina", 0x5A646E, emision=0x6C7885, fuerza=0.16,
             rugosidad=0.55, metal=0.40)
    material("M_Ene_Tablero", 0x39424D, emision=0x46525E, fuerza=0.16,
             rugosidad=0.50, metal=0.35)
    material("M_Ene_Breaker", 0x11171E, emision=0x1B2530, fuerza=0.12,
             rugosidad=0.60)
    material("M_Ene_UPS", 0x1E4C63, emision=AZUL_MEDIO, fuerza=0.26,
             rugosidad=0.50)
    material("M_Ene_Aviso", 0xFBC710, emision=0xFBC710, fuerza=1.6,
             rugosidad=0.40)
    # exterior tecnico: plataforma, pasillo acristalado y jardin de acceso
    material("M_Pas_Losa", 0x8C97A3, emision=0x7E8A96, fuerza=0.14,
             rugosidad=0.85)
    material("M_Pas_Luz", 0xFFF6DA, emision=0xFFEFC2, fuerza=2.0,
             rugosidad=0.40)
    material("M_Jar_Pasto", 0x66C77E, emision=0x66C77E, fuerza=0.95,
             rugosidad=0.92)
    material("M_Jar_Grava", 0xD8D2C2, emision=0xC9C3B4, fuerza=0.55,
             rugosidad=0.94)
    material("M_Jar_Tronco", 0x4A3624, emision=0x3A2A1C, fuerza=0.10,
             rugosidad=0.90)
    material("M_Jar_Follaje", 0x4FB36E, emision=0x4FB36E, fuerza=0.95,
             rugosidad=0.86)
    material("M_Jar_Seto", 0x4C9E68, emision=0x4C9E68, fuerza=0.85,
             rugosidad=0.88)
    material("M_Jar_Madera", 0x6B4A2E, emision=0x3A2A1A, fuerza=0.10,
             rugosidad=0.60)
    # redes

    material("M_Red_Rack", 0x11171E, emision=0x1B2530, fuerza=0.14,
             rugosidad=0.55, metal=0.30)
    material("M_Red_Patch", 0xC9A227, emision=0xA8871E, fuerza=0.25,
             rugosidad=0.50)
    material("M_Red_Switch", 0x1E4C63, emision=AZUL_MEDIO, fuerza=0.30,
             rugosidad=0.45)
    material("M_Red_Led", 0x5CDACE, emision=0x5CDACE, fuerza=2.4,
             rugosidad=0.30)
    material("M_Red_UPS", 0x2A3B4A, emision=0x3C5468, fuerza=0.22,
             rugosidad=0.50)


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
            self.f.append((base + k * 2, base + n * 2,
                           base + n * 2 + 1, base + k * 2 + 1))
            self.m.append(idx)
        self.f.append(tuple(base + k * 2 + 1 for k in range(seg)))
        self.m.append(idx)
        self.f.append(tuple(base + k * 2 for k in range(seg - 1, -1, -1)))
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
    col = bpy.data.collections.get(FILTRO)
    if col is None:
        col = bpy.data.collections.new(FILTRO)
        bpy.context.scene.collection.children.link(col)
    for obj in objetos:
        if col not in obj.users_collection:
            col.objects.link(obj)


def mat(nombre):
    return bpy.data.materials[nombre]


def uv_frente(obj, voltear=False):
    """UV 0-1 en el plano YZ, para pantallas que se miran de frente.

    El exportador glTF invierte la v respecto de Blender, por eso se guarda
    1 - v: si no, la imagen sale cabeza abajo. voltear invierte u, para las
    pantallas cuya cara visible mira a -x.
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
            u = (co.y - y0) / ancho
            uv.data[k].uv = (1.0 - u if voltear else u, 1.0 - (co.z - z0) / alto)


# ------------------------------------------------------------- cuarto frio
def caja_fria(geo, x, y, z, ancho, largo, alto, giro=0.0):
    """Caja de producto perecedero: carton blanco con banda de familia."""
    geo.caja((x, y, z), (ancho, largo, alto * 0.82), mat("M_Frio_Caja"),
             rot=(0.0, 0.0, giro))
    geo.caja((x, y, z + alto * 0.41), (ancho * 0.98, largo * 0.98, alto * 0.06),
             mat("M_Alm_Lab_LACTEOS"), rot=(0.0, 0.0, giro))


def build_frio(col):
    x0, x1, y0, y1 = FRIO
    z0 = SLAB
    techo = z0 + FRIO_ALTO
    ancho, largo = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    yd = -23.00                  # eje del vano en el muro oriente
    vano = 1.30                  # medio ancho del vano
    panel = mat("M_Frio_Panel")
    cielo = mat("M_Frio_Cielo")
    piso = mat("M_Frio_Piso")
    zocalo = mat("M_Frio_Zocalo")
    puerta = mat("M_Frio_Puerta")

    geo = Geo("FRIO_Camara")
    # piso sanitario con zocalo y rejillas de drenaje
    geo.caja((cx, cy, z0 + 0.03), (ancho - 0.24, largo - 0.24, 0.06), piso)
    for (bx, by, sx, sy) in ((cx, y0 + 0.06, ancho, 0.12),
                             (cx, y1 - 0.06, ancho, 0.12),
                             (x0 + 0.06, cy, 0.12, largo),
                             (x1 - 0.06, cy, 0.12, largo)):
        geo.caja((bx, by, z0 + 0.08), (sx, sy, 0.16), zocalo)
    for k in range(4):
        geo.caja((x0 + 2.40 + k * 3.60, y0 + 0.34, z0 + 0.045),
                 (0.70, 0.34, 0.02), mat("M_Frio_Rejilla"))
    # paneleria: muros ciegos sur, norte y occidente
    geo.caja((cx, y0 + 0.06, z0 + FRIO_ALTO / 2), (ancho, 0.12, FRIO_ALTO),
             panel)
    geo.caja((cx, y1 - 0.06, z0 + FRIO_ALTO / 2), (ancho, 0.12, FRIO_ALTO),
             panel)
    geo.caja((x0 + 0.06, cy, z0 + FRIO_ALTO / 2), (0.12, largo, FRIO_ALTO),
             panel)
    # muro oriente partido por el vano de la puerta corredera
    for (ya, yb) in ((y0, yd - vano), (yd + vano, y1)):
        geo.caja((x1 - 0.06, (ya + yb) / 2.0, z0 + FRIO_ALTO / 2),
                 (0.12, yb - ya, FRIO_ALTO), panel)
    geo.caja((x1 - 0.06, yd, z0 + (2.44 + FRIO_ALTO) / 2.0),
             (0.12, 2 * vano, FRIO_ALTO - 2.44), panel)
    geo.caja((cx, cy, techo + 0.06), (ancho, largo, 0.12), cielo)
    # nervios de la paneleria: cada 1,20 m
    x = x0 + 0.40
    while x < x1:
        for yw in (y0 + 0.13, y1 - 0.13):
            geo.caja((x, yw, z0 + FRIO_ALTO / 2), (0.05, 0.03, FRIO_ALTO),
                     zocalo)
        x += 1.20
    # marco del vano y hoja corredera, que abre hacia el pasillo
    geo.caja((x1 - 0.06, yd, z0 + 2.44), (0.20, 2 * vano + 0.30, 0.18),
             zocalo)
    for lado in (-1, 1):
        geo.caja((x1 - 0.06, yd + lado * (vano - 0.07), z0 + 1.22),
                 (0.20, 0.18, 2.44), zocalo)
    geo.caja((x1 + 0.16, yd + vano + 1.05, z0 + 1.22), (0.10, 2.10, 2.34),
             puerta)
    geo.caja((x1 + 0.16, yd + vano + 1.05, z0 + 2.46), (0.16, 2.22, 0.10),
             zocalo)
    for k in range(7):
        geo.caja((x1 - 0.14, yd - 1.05 + k * 0.35, z0 + 1.30),
                 (0.03, 0.31, 2.20), mat("M_Alm_Vidrio"))
    geo.caja((x1 + 0.55, yd, z0 + 0.06), (1.00, 2.70, 0.12), zocalo)
    # revestimiento exterior: la camara es blanca por dentro y azul por fuera
    rev = mat("M_Alm_Muro")
    banda = mat("M_Alm_Ambar")
    for (bx, by, sx, sy) in ((cx, y0 - 0.05, ancho + 0.20, 0.10),
                             (cx, y1 + 0.05, ancho + 0.20, 0.10),
                             (x0 - 0.05, cy, 0.10, largo + 0.20)):
        geo.caja((bx, by, z0 + FRIO_ALTO / 2), (sx, sy, FRIO_ALTO), rev)
        geo.caja((bx, by, z0 + FRIO_ALTO - 0.62), (sx + 0.06, sy + 0.06,
                 0.26), banda)
    geo.caja((cx, cy, techo + 0.22), (ancho + 0.44, largo + 0.44, 0.22), rev)
    geo.objeto(col, "FRIO_Camara")
    # estanteria interior: cuatro filas de 13,5 m, tres niveles
    nivel_z = (z0 + 0.95, z0 + 3.10, z0 + 5.20)
    filas = (y0 + 2.20, y0 + 5.60, y0 + 9.00, y0 + 12.40)
    xa, xb = x0 + 0.90, x1 - 3.60
    est = Geo("FRIO_Estanteria")
    for yf in filas:
        for xp in (xa, xb):
            for dy in (-0.55, 0.55):
                est.caja((xp, yf + dy, z0 + 3.10), (0.09, 0.09, 6.00),
                         mat("M_Alm_Rack"))
        for z in nivel_z:
            est.caja(((xa + xb) / 2.0, yf, z), (xb - xa, 1.30, 0.12),
                     mat("M_Alm_Acero"))
    est.objeto(col, "FRIO_Estanteria")

    # producto palletizado dentro de la camara
    prod = Geo("FRIO_Producto")
    for yf in filas:
        for k in range(6):
            xp = xa + 0.75 + k * 2.30
            for z in nivel_z:
                prod.caja((xp, yf, z + 0.20), (1.20, 1.10, 0.14),
                          mat("M_Alm_Madera"))
                for dx in (-0.28, 0.28):
                    for dy in (-0.25, 0.25):
                        caja_fria(prod, xp + dx, yf + dy, z + 0.42,
                                  0.52, 0.46, 0.60)
    prod.objeto(col, "FRIO_Producto")

    # evaporadores colgados y condensadoras en la cubierta
    eq = Geo("FRIO_Equipo")
    for xp in (x0 + 3.20, x0 + 8.00, x0 + 12.80):
        eq.caja((xp, y0 + 1.35, techo - 0.55), (2.20, 0.80, 0.55),
                mat("M_Frio_Unidad"))
        eq.caja((xp, y0 + 1.35, techo - 0.86), (1.90, 0.62, 0.10),
                mat("M_Frio_Rejilla"))
        for k in (-1, 1):
            eq.cilindro((xp + k * 0.52, y0 + 0.97, techo - 0.86), 0.22, 0.08,
                        mat("M_Frio_Rejilla"), rot=(math.radians(90), 0.0, 0.0),
                        seg=12)
        eq.caja((xp, y0 + 1.35, techo - 0.24), (0.42, 0.42, 0.10),
                mat("M_Frio_Zocalo"))
    for xp in (x0 + 4.00, x0 + 11.00):
        eq.caja((xp, cy, techo + 0.92), (1.60, 1.10, 1.30),
                mat("M_Frio_Unidad"))
        eq.caja((xp, cy, techo + 1.62), (1.70, 1.20, 0.10),
                mat("M_Frio_Rejilla"))
        for k in (-1, 1):
            eq.caja((xp + k * 0.40, cy, techo + 0.30), (0.14, 0.90, 0.40),
                    mat("M_Frio_Zocalo"))
    eq.caja((x1 + 0.34, cy, techo - 1.20), (0.16, 0.16, 3.20),
            mat("M_Frio_Tubo"))
    eq.objeto(col, "FRIO_Equipo")

    # monitoreo de cadena de frio: sondas, registrador, panel y baliza
    sen = Geo("FRIO_Monitoreo")
    for (xp, z) in ((x0 + 1.40, z0 + 1.70), (x0 + 6.20, z0 + 4.10),
                    (x0 + 11.00, z0 + 1.70), (x1 - 1.30, z0 + 3.40)):
        sen.caja((xp, y0 + 0.30, z), (0.12, 0.20, 0.24), mat("M_Frio_Sensor"))
        sen.caja((xp, y0 + 0.19, z + 0.14), (0.06, 0.03, 0.06),
                 mat("M_Frio_Lente"))
    for lado in (-1, 1):
        sen.caja((x1 - 0.22, yd + lado * (vano - 0.10), z0 + 1.90),
                 (0.10, 0.08, 0.22), mat("M_Frio_Sensor"))
    sen.cilindro((x1 - 0.34, yd - vano - 0.45, techo - 0.30), 0.14, 0.24,
                 mat("M_Frio_Alarma"), seg=12)
    sen.caja((x0 + 8.00, y0 + 0.62, techo - 1.16), (0.16, 0.10, 0.20),
             mat("M_Frio_Sensor"))
    # registrador y panel, en el pasillo junto a la puerta
    sen.caja((x1 + 0.24, yd + vano + 2.60, z0 + 1.55), (0.16, 0.42, 0.58),
             mat("M_Frio_Sensor"))
    sen.caja((x1 + 0.33, yd + vano + 2.60, z0 + 1.66), (0.02, 0.30, 0.24),
             mat("M_Frio_Lente"))
    sen.caja((cx, y0 + 1.00, techo - 0.22), (ancho - 0.60, 0.30, 0.08),
             mat("M_Alm_Acero"))
    sen.objeto(col, "FRIO_Monitoreo")
    sin_lineas([bpy.data.objects.get("FRIO_Monitoreo")])

    # rotulos
    t_azul = mat("M_Alm_TextoAzul")
    t_blanco = mat("M_Alm_Texto")
    texto("FRIO_Rotulo", "CUARTO FRIO · LACTEOS Y REFRIGERADOS",
          (x1 + 0.14, yd, z0 + 3.70), 0.30, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("FRIO_Rotulo2", "2 °C A 4 °C · CADENA DE FRIO MONITOREADA",
          (x1 + 0.14, yd, z0 + 3.28), 0.20, col, t_azul,
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("FRIO_Rotulo3", "LACTEOS · REFRIGERADOS · CONGELADOS",
          (cx, y0 - 0.24, z0 + 4.35), 0.32, col, t_azul,
          rot=(math.radians(90), 0.0, 0.0))
    texto("FRIO_Rotulo4", "CUARTO FRIO · 18 × 14 M",
          (cx, y0 - 0.24, z0 + 5.05), 0.55, col, t_blanco,
          rot=(math.radians(90), 0.0, 0.0))
    texto("FRIO_PisoMarca", "ZONA DE FRIO · NO BLOQUEAR",
          (x1 + 1.80, yd, z0 + 0.06), 0.24, col, t_blanco,
          rot=(0.0, 0.0, math.radians(90)))

# ---------------------------------------------------------- administracion
def silla(geo, x, y, giro=0.0):
    silla_m = mat("M_Adm_Silla")
    acero = mat("M_Alm_Acero")
    c, s = math.cos(giro), math.sin(giro)
    geo.caja((x, y, SLAB + 0.46), (0.50, 0.50, 0.10), silla_m,
             rot=(0.0, 0.0, giro))
    geo.caja((x - 0.24 * c, y - 0.24 * s, SLAB + 0.78), (0.10, 0.50, 0.56),
             silla_m, rot=(0.0, 0.0, giro))
    geo.cilindro((x, y, SLAB + 0.20), 0.05, 0.42, acero, seg=8)


def build_admin(col):
    x0, x1, y0, y1 = ADMIN
    z0 = SLAB
    techo = z0 + ADMIN_ALTO
    muro = mat("M_Adm_Muro")
    panel = mat("M_Adm_Panel")
    vidrio = mat("M_Adm_Vidrio")
    piso = mat("M_Adm_Piso")
    acero = mat("M_Alm_Acero")

    geo = Geo("ADM_Estructura")
    # el anexo se apoya en el patio, a nivel de anden
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 / 2),
             (x1 - x0 + 1.40, y1 - y0 + 1.40, z0), mat("M_Alm_Losa"))
    # piso y cielo raso
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.02),
             (x1 - x0, y1 - y0, 0.04), piso)
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, techo + 0.13),
             (x1 - x0 + 0.90, y1 - y0 + 0.90, 0.26), muro)
    # muros: sur y occidente ciegos; norte y oriente acristalados, para que
    # desde el patio se vea que hay dentro de cada sala
    geo.caja(((x0 + x1) / 2, y0 + 0.06, z0 + ADMIN_ALTO / 2),
             (x1 - x0, 0.12, ADMIN_ALTO), muro)
    geo.caja((x0 + 0.06, (y0 + y1) / 2, z0 + ADMIN_ALTO / 2),
             (0.12, y1 - y0, ADMIN_ALTO), muro)
    _ventanal(geo, "x", y1 - 0.06, x0 + 0.14, x1 - 0.14, z0, ADMIN_ALTO,
              vidrio, acero, antepecho=0.85, paso=1.60)
    # fachada oriente: dos ventanales con el muro de la pantalla al centro
    tv_y = (y0 + y1) / 2
    geo.caja((x1 - 0.06, tv_y, z0 + ADMIN_ALTO / 2),
             (0.12, 2.30, ADMIN_ALTO), muro)
    _ventanal(geo, "y", x1 - 0.06, y0 + 0.14, tv_y - 1.15, z0, ADMIN_ALTO,
              vidrio, acero, antepecho=0.85, paso=1.60)
    _ventanal(geo, "y", x1 - 0.06, tv_y + 1.15, y1 - 0.14, z0, ADMIN_ALTO,
              vidrio, acero, antepecho=0.85, paso=1.60)
    # division vidriada entre recepcion y sala de juntas
    xdiv = x0 + 2.90
    geo.caja((xdiv, (y0 + y1) / 2, z0 + ADMIN_ALTO / 2),
             (0.06, y1 - y0 - 0.2, ADMIN_ALTO - 0.3), vidrio)
    for y in (y0 + 0.20, (y0 + y1) / 2, y1 - 0.20):
        geo.caja((xdiv, y, z0 + ADMIN_ALTO / 2), (0.14, 0.14, ADMIN_ALTO),
                 acero)
    geo.caja((xdiv, (y0 + y1) / 2, techo - 0.06), (0.14, y1 - y0, 0.12), acero)
    # vano de circulacion en la division
    geo.caja((xdiv, y0 + 1.50, z0 + 2.20), (0.14, 0.10, 2.20), acero)
    # puerta de entrada al area, en el muro sur
    geo.caja((x0 + 1.20, y0 + 0.06, z0 + 1.05), (1.00, 0.16, 2.10), panel)
    geo.caja((x0 + 1.20, y0 + 0.16, z0 + 1.10), (0.10, 0.06, 0.20), acero)
    # cielo raso: luminarias
    for (lx, ly) in ((x0 + 1.50, y0 + 1.60), (x0 + 1.50, y1 - 1.80),
                     (x0 + 4.90, y0 + 1.80), (x0 + 4.90, y1 - 1.80)):
        geo.caja((lx, ly, techo - 0.04), (1.20, 0.60, 0.06), mat("M_Adm_Luz"))
    geo.objeto(col, "ADM_Estructura")

    # sala de juntas: mesa de directivos, sillas, pantalla y credenza
    mob = Geo("ADM_Muebles")
    mx, my = (xdiv + x1) / 2 + 0.10, (y0 + y1) / 2
    mob.caja((mx, my, z0 + 0.74), (3.60, 1.50, 0.08), mat("M_Adm_Mesa"))
    for dx in (-1.55, 1.55):
        for dy in (-0.55, 0.55):
            mob.caja((mx + dx, my + dy, z0 + 0.37), (0.10, 0.10, 0.70),
                     acero)
    mob.caja((mx, my, z0 + 0.30), (1.20, 0.30, 0.10), mat("M_Adm_Mueble"))
    # sillas: tres por lado largo, alineadas con la mesa y mirandola, y una
    # en cada cabecera
    for dx in (-1.15, 0.0, 1.15):
        silla(mob, mx + dx, my - 1.10, giro=math.radians(90))
        silla(mob, mx + dx, my + 1.10, giro=math.radians(-90))
    silla(mob, mx - 2.15, my, giro=0.0)
    silla(mob, mx + 2.15, my, giro=math.radians(180))
    # pantalla de la sala: el panel va suelto y con UV para que el visor le
    # pueda poner contenido encima, como a las pantallas del muro de video
    tv_x = x1 - 0.14
    mob.caja((tv_x, my, z0 + 2.40), (0.10, 1.86, 1.10),
             mat("M_Adm_TVMarco"))
    tv = Geo("ADM_Pantalla")
    tv.caja((tv_x - 0.06, my, z0 + 2.40), (0.02, 1.74, 0.98), mat("M_Adm_TV"))
    uv_frente(tv.objeto(col, "ADM_Pantalla"), voltear=True)
    mob.caja((tv_x - 0.14, my, z0 + 0.85), (0.42, 2.00, 0.55),
             mat("M_Adm_Mueble"))
    # pared norte de la sala: tablero de corcho y reloj
    mob.caja((mx - 0.60, y1 - 0.14, z0 + 2.10), (1.60, 0.04, 1.10),
             mat("M_Adm_Mueble"))
    # recepcion: escritorio, silla, estanteria y equipo
    mob.caja((x0 + 1.55, y1 - 1.40, z0 + 0.76), (1.90, 0.80, 0.06),
             mat("M_Adm_Mesa"))
    for dx in (-0.80, 0.80):
        mob.caja((x0 + 1.55 + dx, y1 - 1.40, z0 + 0.38), (0.10, 0.70, 0.72),
                 mat("M_Adm_Mueble"))
    silla(mob, x0 + 1.55, y1 - 2.10, giro=0.0)
    mob.caja((x0 + 0.55, y0 + 2.60, z0 + 1.10), (0.60, 1.90, 2.00),
             mat("M_Adm_Mueble"))
    for k in range(4):
        mob.caja((x0 + 0.42, y0 + 2.60, z0 + 0.45 + k * 0.48),
                 (0.06, 1.70, 0.05), mat("M_Alm_Acero"))
    mob.caja((x0 + 1.60, y1 - 1.40, z0 + 0.86), (0.50, 0.34, 0.14),
             mat("M_Adm_TVMarco"))
    mob.objeto(col, "ADM_Muebles")

    # tecnologia del area: pantalla, punto de acceso y lector
    tec = Geo("ADM_Tecnologia")
    tec.caja((x0 + 2.10, y0 + 0.30, z0 + 1.45), (0.20, 0.10, 0.30),
             mat("M_Frio_Sensor"))
    tec.cilindro(((x0 + x1) / 2, y0 + 2.40, techo - 0.10), 0.18, 0.06,
                 mat("M_Frio_Sensor"), seg=12)
    tec.objeto(col, "ADM_Tecnologia")
    sin_lineas([bpy.data.objects.get("ADM_Tecnologia")])

    t_blanco = mat("M_Alm_Texto")
    t_azul = mat("M_Alm_TextoAzul")
    texto("ADM_Rotulo", "SALA DE JUNTAS · COMITE DEL PROGRAMA",
          (mx, y0 + 0.16, z0 + 3.10), 0.20, col, t_blanco,
          rot=(math.radians(90), 0.0, 0.0))
    texto("ADM_Rotulo2", "GERENCIA ADMINISTRATIVA Y FINANCIERA",
          (x0 + 1.55, y1 - 0.16, z0 + 3.05), 0.18, col, t_azul,
          rot=(math.radians(90), 0.0, math.radians(180)))


# ---------------------------------------------------------------- energia
def build_energia(col):
    x0, x1, y0, y1 = ENE
    z0 = SLAB
    ancho, largo = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    yd = -6.00                   # eje de la puerta de la reja oriente
    cabina = mat("M_Ene_Cabina")
    tablero = mat("M_Ene_Tablero")
    breaker = mat("M_Ene_Breaker")
    ups = mat("M_Ene_UPS")
    acero = mat("M_Alm_Acero")
    muro = mat("M_Adm_Muro")
    losa = mat("M_Alm_Losa")

    geo = Geo("ENE_Subestacion")
    # cerramiento: tres muros ciegos, remate y reja oriente hacia el pasillo
    for (bx, by, sx, sy) in ((cx, y0 + 0.10, ancho, 0.20),
                             (cx, y1 - 0.10, ancho, 0.20),
                             (x0 + 0.10, cy, 0.20, largo)):
        geo.caja((bx, by, z0 + 1.40), (sx, sy, 2.80), muro)
        geo.caja((bx, by, z0 + 2.88), (sx + 0.16, sy + 0.16, 0.16), acero)
    # reja: montantes cada 3 m, tres travesanos y barrotes verticales
    for k in range(7):
        yy = y0 + 0.10 + k * (largo - 0.20) / 6.0
        geo.caja((x1 - 0.10, yy, z0 + 1.18), (0.16, 0.16, 2.36), acero)
    for zz in (z0 + 0.32, z0 + 1.22, z0 + 2.26):
        geo.caja((x1 - 0.10, cy, zz), (0.10, largo - 0.20, 0.10),
                 acero)
    yy = y0 + 0.10
    while yy < y1 - 0.10:
        if not (yd - 1.45 <= yy <= yd + 1.45):
            geo.caja((x1 - 0.10, yy, z0 + 1.29), (0.05, 0.05, 1.80), acero)
        yy += 0.42
    # puerta de dos hojas en la reja
    for lado in (-1, 1):
        geo.caja((x1 - 0.10, yd + lado * 0.72, z0 + 1.20),
                 (0.08, 1.38, 2.10), mat("M_Ene_Tablero"))
        geo.caja((x1 - 0.16, yd + lado * 1.36, z0 + 1.20),
                 (0.06, 0.08, 2.10), acero)
    geo.caja((x1 - 0.16, yd, z0 + 1.60), (0.06, 0.24, 0.10), acero)

    # patio de maniobra y equipo: transformador sobre dado, tableros y UPS
    geo.caja((x0 + 3.40, y0 + 3.60, z0 + 0.10), (2.60, 2.30, 0.20), losa)
    geo.caja((x0 + 3.40, y0 + 8.20, z0 + 0.10), (2.60, 2.30, 0.20), losa)
    geo.caja((x0 + 3.40, y0 + 3.60, z0 + 1.25), (1.80, 1.50, 2.10), cabina)
    for k in range(5):
        geo.caja((x0 + 3.40, y0 + 2.90 + k * 0.35, z0 + 1.95),
                 (1.50, 0.16, 0.10), breaker)
    geo.caja((x0 + 3.40, y0 + 3.60, z0 + 2.36), (1.90, 1.60, 0.10), cabina)
    # dado de reserva para el segundo transformador
    geo.caja((x0 + 3.40, y0 + 8.20, z0 + 0.62), (1.90, 1.60, 0.90),
             tablero)
    # tablero general de baja tension con sus circuitos
    geo.caja((x0 + 9.00, y0 + 0.90, z0 + 1.20), (2.60, 0.70, 2.40), tablero)
    for k in range(6):
        geo.caja((x0 + 8.10 + k * 0.36, y0 + 0.52, z0 + 1.95),
                 (0.26, 0.06, 0.34), breaker)
    for k in range(6):
        geo.caja((x0 + 8.10 + k * 0.36, y0 + 0.52, z0 + 1.20),
                 (0.26, 0.06, 0.30), breaker)
    # tablero de transferencia
    geo.caja((x0 + 12.60, y0 + 0.90, z0 + 1.20), (1.60, 0.70, 2.40),
             tablero)
    geo.caja((x0 + 12.60, y0 + 0.52, z0 + 1.75), (0.70, 0.06, 0.50),
             mat("M_Frio_Lente"))
    # UPS de la sala de control, del cuarto frio y del cuarto de monitoreo
    for k, (xu, yu) in enumerate(((x0 + 15.60, y0 + 0.90),
                                  (x0 + 15.60, y0 + 2.60))):
        geo.caja((xu, yu, z0 + 0.95), (0.90, 0.85, 1.90), ups)
        geo.caja((xu, yu + 0.46, z0 + 1.55), (0.60, 0.04, 0.40),
                 mat("M_Frio_Lente"))
    # banco de condensadores
    geo.caja((x0 + 15.40, y0 + 7.60, z0 + 1.10), (1.50, 0.60, 2.20),
             tablero)
    # aisladores de la subestacion y demarcacion del patio de maniobra
    for k in (-0.55, 0.00, 0.55):
        geo.cilindro((x0 + 3.40 + k, y0 + 3.60, z0 + 2.62), 0.12, 0.42,
                     mat("M_Frio_Sensor"), seg=8)
    amari = mat("M_Alm_Piso")
    for (bx, by, sx, sy) in ((x0 + 3.40, y0 + 2.15, 3.50, 0.12),
                             (x0 + 3.40, y0 + 5.05, 3.50, 0.12),
                             (x0 + 1.65, y0 + 3.60, 0.12, 3.02),
                             (x0 + 5.15, y0 + 3.60, 0.12, 3.02)):
        geo.caja((bx, by, z0 + 0.028), (sx, sy, 0.02), amari)
    geo.caja((cx, y0 + 0.45, z0 + 0.028), (ancho - 2.20, 0.10, 0.02), amari)
    # bandeja y ductos hacia el pasillo
    geo.caja((cx, y0 + 1.40, z0 + 2.90), (ancho - 1.20, 0.35, 0.10), acero)
    geo.caja((x1 - 0.30, y0 + 1.40, z0 + 2.45), (0.20, 0.35, 1.00), acero)
    geo.objeto(col, "ENE_Subestacion")

    # rotulos
    t_blanco = mat("M_Alm_Texto")
    t_ambar = mat("M_Ene_Aviso")
    geo2 = Geo("ENE_Rotulos")
    geo2.caja((x1 - 0.02, cy - 3.20, z0 + 3.30), (0.12, 5.20, 0.86), muro)
    geo2.caja((x1 + 0.06, cy - 3.20, z0 + 3.30), (0.06, 5.00, 0.72), tablero)
    geo2.objeto(col, "ENE_Rotulos")
    texto("ENE_Rotulo", "SUBESTACION 500 kVA · TABLERO GENERAL",
          (x1 + 0.10, cy - 3.20, z0 + 3.44), 0.28, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("ENE_Aviso", "ALTA TENSION · SOLO PERSONAL AUTORIZADO",
          (x1 + 0.10, cy - 3.20, z0 + 3.10), 0.17, col, t_ambar,
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("ENE_Piso", "SUBESTACION",
          (cx, y0 + 5.20, z0 + 0.024), 0.60, col, t_blanco,
          rot=(0.0, 0.0, 0.0))
    texto("ENE_Rotulo_Muro", "SUBESTACION 500 kVA · 13.200 / 440 V",
          (x0 + 0.18, cy, z0 + 1.90), 0.34, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(90)))

# ------------------------------------------- plataforma, pasillo y jardin
def _ventanal(geo, eje, cte, a, b, z0, alto, vidrio, acero,
              antepecho=0.85, paso=1.70, dintel=0.18):
    """Paño de fachada: antepecho, vidrio con montantes y dintel.

    eje="x": la fachada corre a lo largo de x, en el plano y = cte.
    eje="y": la fachada corre a lo largo de y, en el plano x = cte.
    """
    largo = b - a
    if largo < 0.20:
        return

    def blq(p, dl, dz, dh, mat):
        if eje == "x":
            geo.caja((p, cte, dz), (dl, 0.10, dh), mat)
        else:
            geo.caja((cte, p, dz), (0.10, dl, dh), mat)

    if antepecho > 0.05:
        blq((a + b) / 2.0, largo, z0 + antepecho / 2.0, antepecho, acero)
    if alto - antepecho > 0.10:
        blq((a + b) / 2.0, largo, z0 + (antepecho + alto) / 2.0,
            alto - antepecho, vidrio)
    blq((a + b) / 2.0, largo, z0 + alto - dintel / 2.0, dintel, acero)
    n = max(1, int(round(largo / paso)))
    for k in range(n + 1):
        blq(a + largo * k / n, 0.14, z0 + (antepecho + alto) / 2.0,
            alto - antepecho, acero)


def build_plataforma(col):
    """Plataforma comun de los pabellones exentos, a la cota de la nave."""
    px0, px1, py0, py1 = PLATAFORMA
    cx, cy = (px0 + px1) / 2.0, (py0 + py1) / 2.0
    losa = mat("M_Alm_Losa")
    remate = mat("M_Pas_Losa")

    geo = Geo("PLA_Plataforma")
    geo.caja((cx, cy, SLAB / 2.0), (px1 - px0, py1 - py0, SLAB), losa)
    geo.caja((cx, cy, SLAB + 0.015),
             (px1 - px0 - 0.24, py1 - py0 - 0.24, 0.03), remate)
    # remate perimetral con el hueco de la escalera al norte
    esc_x, esc_ancho = -68.00, 3.00
    geo.caja((px0 + 0.14, cy, SLAB + 0.24), (0.28, py1 - py0, 0.48), remate)
    geo.caja((cx, py0 + 0.14, SLAB + 0.24), (px1 - px0, 0.28, 0.48), remate)
    geo.caja(((px0 + esc_x - esc_ancho / 2) / 2.0, py1 - 0.14, SLAB + 0.24),
             (esc_x - esc_ancho / 2 - px0, 0.28, 0.48), remate)
    geo.caja(((esc_x + esc_ancho / 2 + px1) / 2.0, py1 - 0.14, SLAB + 0.24),
             (px1 - esc_x - esc_ancho / 2, 0.28, 0.48), remate)
    geo.objeto(col, "PLA_Plataforma")

    esc = Geo("PLA_Escalera")
    for k in range(6):
        esc.caja((esc_x, py1 + 0.17 + k * 0.34, SLAB - 0.105 - k * 0.21),
                 (esc_ancho, 0.34, 0.21), remate)
    esc.objeto(col, "PLA_Escalera")


def build_pasillos(col):
    """Corredor acristalado que sirve al frio y a la energia desde el jardin."""
    x0, x1, y0, y1 = PASILLO
    z0 = SLAB
    alto = 3.30
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    vidrio = mat("M_Adm_Vidrio")
    acero = mat("M_Alm_Acero")
    losa = mat("M_Alm_Losa")
    luz = mat("M_Pas_Luz")

    geo = Geo("PAS_Corredor")
    geo.caja((cx, cy, z0 + 0.05), (x1 - x0 + 0.30, y1 - y0 + 0.30, 0.10),
             mat("M_Pas_Losa"))
    geo.caja((cx, cy, z0 + alto + 0.14),
             (x1 - x0 + 0.80, y1 - y0 + 0.80, 0.28), losa)
    for k in range(11):
        geo.caja((cx, y0 + 1.40 + k * 2.70, z0 + alto - 0.06),
                 (0.44, 1.40, 0.08), luz)
    for k in range(11):
        yy = y0 + 0.20 + k * 3.00
        for xx in (x0 + 0.12, x1 - 0.12):
            geo.caja((xx, yy, z0 + alto / 2.0), (0.22, 0.22, alto), acero)
    geo.objeto(col, "PAS_Corredor")

    vd = Geo("PAS_Vidrio")
    # costado occidente: vano del frio, puerta de la energia y testero sur
    for (ya, yb) in ((y0 + 0.20, -24.40), (-21.60, -7.50),
                     (-4.50, y1 - 0.20)):
        _ventanal(vd, "y", x0, ya, yb, z0, alto, vidrio, acero, antepecho=0.42)
    # costado oriente: puerta del jardin al centro
    for (ya, yb) in ((y0 + 0.20, -17.40), (-14.60, y1 - 0.20)):
        _ventanal(vd, "y", x1, ya, yb, z0, alto, vidrio, acero, antepecho=0.42)
    # testero norte acristalado y testero sur ciego
    _ventanal(vd, "x", y1, x0 + 0.20, x1 - 0.20, z0, alto, vidrio, acero,
              antepecho=0.42)
    vd.caja((cx, y0 + 0.06, z0 + alto / 2.0), (x1 - x0, 0.12, alto), acero)
    # puerta de dos hojas del jardin en el costado oriente
    for lado in (-1, 1):
        vd.caja((x1, ACCESO_Y + lado * 0.72, z0 + 1.24), (0.08, 1.38, 2.30),
                vidrio)
        vd.caja((x1, ACCESO_Y + lado * 1.36, z0 + 1.22), (0.12, 0.08, 2.44),
                acero)
    vd.caja((x1, ACCESO_Y, z0 + 2.46), (0.14, 2.86, 0.10), acero)
    vd.caja((x1, ACCESO_Y, z0 + 0.06), (0.30, 2.86, 0.08), acero)
    vd.objeto(col, "PAS_Vidrio")


def build_jardin(col):
    """Patio verde alrededor de la puerta de personal de la nave."""
    x0, x1, y0, y1 = JARDIN
    z0 = SLAB
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    pasto = mat("M_Jar_Pasto")
    grava = mat("M_Jar_Grava")
    tronco = mat("M_Jar_Tronco")
    follaje = mat("M_Jar_Follaje")
    seto = mat("M_Jar_Seto")
    madera = mat("M_Jar_Madera")
    acero = mat("M_Alm_Acero")
    vidrio = mat("M_Adm_Vidrio")
    losa = mat("M_Alm_Losa")
    luz = mat("M_Pas_Luz")

    geo = Geo("JAR_Patio")
    # cesped, camino al pasillo y anden de acceso a la puerta
    geo.caja((cx, cy, z0 + 0.04), (x1 - x0, y1 - y0, 0.08), pasto)
    geo.caja((cx, ACCESO_Y, z0 + 0.06), (x1 - x0, 3.60, 0.05), grava)
    geo.caja((x0 + 2.00, cy, z0 + 0.06), (3.00, y1 - y0, 0.05), grava)
    # arriates y setos que enmarcan el camino
    for lado in (-1, 1):
        geo.caja((cx, ACCESO_Y + lado * 2.20, z0 + 0.30),
                 (x1 - x0 - 0.50, 0.40, 0.60), seto)
    # arboles
    # arboles: dos a cada lado del camino, sin tapar la puerta
    for (tx, ty) in ((-70.20, -20.20), (-70.20, -11.60), (-64.60, -24.40),
                     (-64.60, -8.00)):
        geo.cilindro((tx, ty, z0 + 1.20), 0.18, 2.40, tronco, seg=8)
        for (dz, radio) in ((2.60, 1.20), (3.02, 1.05), (3.44, 0.88),
                            (3.86, 0.70), (4.28, 0.46)):
            geo.cilindro((tx, ty, z0 + dz), radio, 0.44, follaje, seg=14)
    # bancas de madera mirando al camino
    for (bx, by, s) in ((-66.60, -19.90, -1), (-66.60, -12.10, 1)):
        geo.caja((bx, by, z0 + 0.44), (1.80, 0.50, 0.10), madera)
        geo.caja((bx, by + s * 0.22, z0 + 0.76), (1.80, 0.10, 0.54), madera)
        for dx in (-0.68, 0.68):
            geo.caja((bx + dx, by, z0 + 0.22), (0.12, 0.44, 0.40), acero)
    # materas en las esquinas
    for (px, py) in ((-64.00, -1.80), (-64.00, -28.20), (-69.00, -1.80),
                     (-69.00, -28.20)):
        geo.caja((px, py, z0 + 0.30), (1.40, 1.40, 0.60), acero)
        geo.caja((px, py, z0 + 0.70), (1.20, 1.20, 0.30), seto)
    # luminarias
    for (lx, ly) in ((-69.60, -22.00), (-69.60, -10.00), (-63.60, -22.00),
                     (-63.60, -10.00)):
        geo.caja((lx, ly, z0 + 1.90), (0.12, 0.12, 3.80), acero)
        geo.caja((lx, ly, z0 + 3.86), (0.44, 0.44, 0.14), luz)
    # puerta de personal de la nave con marquesina: hoja de vidrio abierta
    # contra el jardin, para que el vano quede libre al recorrer a pie
    geo.caja((MURO_OESTE - 0.06, ACCESO_Y, z0 + 1.32), (0.12, 3.20, 2.64),
             acero)
    geo.caja((MURO_OESTE - 0.16, ACCESO_Y, z0 + 2.62), (0.10, 3.10, 0.10),
             acero)
    geo.caja((MURO_OESTE - 0.75, ACCESO_Y + 1.48, z0 + 1.30),
             (1.44, 0.08, 2.52), vidrio)
    geo.caja((MURO_OESTE - 0.75, ACCESO_Y + 1.48, z0 + 2.60),
             (1.50, 0.12, 0.08), acero)
    geo.caja((MURO_OESTE - 1.45, ACCESO_Y, z0 + 3.10), (2.90, 4.20, 0.14),
             losa)
    for lado in (-1, 1):
        geo.caja((MURO_OESTE - 2.70, ACCESO_Y + lado * 1.90, z0 + 1.55),
                 (0.16, 0.16, 3.10), acero)
    geo.caja((MURO_OESTE - 0.34, ACCESO_Y, z0 + 0.03), (0.70, 3.60, 0.06),
             grava)
    geo.objeto(col, "JAR_Patio")

    texto("JAR_Rotulo", "ACCESO PEATONAL · JARDIN",
          (MURO_OESTE - 0.10, ACCESO_Y, z0 + 3.55), 0.26, col,
          mat("M_Alm_Texto"),
          rot=(math.radians(90), 0.0, math.radians(-90)))
    # rotulos de la fachada oeste de la nave, que ahora mira al jardin
    texto("JAR_RotuloNave", "CENTRO DE ACOPIO",
          (MURO_OESTE - 0.10, -6.00, SLAB + 7.30), 2.10, col,
          mat("M_Alm_TextoAzul"),
          rot=(math.radians(90), 0.0, math.radians(-90)))
    texto("JAR_RotuloNave2", "ALTIPAL · 47.300 m² DE FULFILLMENT",
          (MURO_OESTE - 0.10, -6.00, SLAB + 5.40), 0.95, col,
          mat("M_Alm_Texto"),
          rot=(math.radians(90), 0.0, math.radians(-90)))

def build_jardin_norte(col):
    """Patio verde que une la nave con el anexo administrativo."""
    x0, x1 = JARDIN_NORTE
    y0, y1 = HY1, ADMIN[2]                 # 16,00 a 21,00
    z0 = SLAB
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    pasto = mat("M_Jar_Pasto")
    grava = mat("M_Jar_Grava")
    tronco = mat("M_Jar_Tronco")
    follaje = mat("M_Jar_Follaje")
    seto = mat("M_Jar_Seto")
    madera = mat("M_Jar_Madera")
    acero = mat("M_Alm_Acero")
    vidrio = mat("M_Adm_Vidrio")
    losa = mat("M_Alm_Losa")
    remate = mat("M_Pas_Losa")
    luz = mat("M_Pas_Luz")

    geo = Geo("JAR_Norte")
    # plataforma, cesped, camino al anexo y remates laterales
    geo.caja((cx, cy, SLAB / 2.0), (x1 - x0, y1 - y0, SLAB), losa)
    geo.caja((cx, cy, z0 + 0.03), (x1 - x0 - 0.24, y1 - y0 - 0.24, 0.06),
             pasto)
    geo.caja((ACCESO_N_X, (y0 + y1) / 2.0, z0 + 0.07),
             (3.00, y1 - y0 - 0.20, 0.06), grava)
    for xx in (x0 + 0.14, x1 - 0.14):
        geo.caja((xx, cy, z0 + 0.20), (0.28, y1 - y0, 0.40), remate)
    # setos que enmarcan el camino
    for lado in (-1, 1):
        geo.caja((ACCESO_N_X + lado * 1.90, cy, z0 + 0.28),
                 (0.40, y1 - y0 - 0.70, 0.56), seto)
    # arboles
    for (tx, ty) in ((-47.00, 18.40), (-42.00, 17.50), (-30.00, 18.60),
                     (-24.00, 17.60)):
        geo.cilindro((tx, ty, z0 + 1.20), 0.18, 2.40, tronco, seg=8)
        for (dz, radio) in ((2.60, 1.20), (3.02, 1.05), (3.44, 0.88),
                            (3.86, 0.70), (4.28, 0.46)):
            geo.cilindro((tx, ty, z0 + dz), radio, 0.44, follaje, seg=14)
    # bancas y materas
    for (bx, by) in ((-41.60, 20.20), (-31.60, 20.20)):
        geo.caja((bx, by, z0 + 0.44), (1.80, 0.50, 0.10), madera)
        geo.caja((bx, by + 0.22, z0 + 0.76), (1.80, 0.10, 0.54), madera)
        for dx in (-0.68, 0.68):
            geo.caja((bx + dx, by, z0 + 0.22), (0.12, 0.44, 0.40), acero)
    for (px, py) in ((x0 + 1.40, y0 + 1.40), (x1 - 1.40, y0 + 1.40)):
        geo.caja((px, py, z0 + 0.30), (1.40, 1.40, 0.60), acero)
        geo.caja((px, py, z0 + 0.70), (1.20, 1.20, 0.30), seto)
    # luminarias
    for (lx, ly) in ((ACCESO_N_X - 2.30, 19.40), (ACCESO_N_X + 2.30, 19.40)):
        geo.caja((lx, ly, z0 + 1.90), (0.12, 0.12, 3.80), acero)
        geo.caja((lx, ly, z0 + 3.86), (0.44, 0.44, 0.14), luz)

    # vano de paso en la banda de la nave: marco, hojas abiertas y marquesina
    for lado in (-1, 1):
        geo.caja((ACCESO_N_X + lado * 1.56, y0 + 0.06, z0 + 1.35),
                 (0.14, 0.24, 2.70), acero)
        geo.caja((ACCESO_N_X + lado * 2.24, y0 + 0.80, z0 + 1.30),
                 (0.08, 1.46, 2.52), vidrio)
        geo.caja((ACCESO_N_X + lado * 2.24, y0 + 0.80, z0 + 2.58),
                 (0.12, 1.50, 0.08), acero)
        geo.caja((ACCESO_N_X + lado * 2.24, y0 + 0.14, z0 + 1.30),
                 (0.10, 0.10, 2.52), acero)
    geo.caja((ACCESO_N_X, y0 + 0.06, z0 + 2.76), (3.30, 0.24, 0.16), acero)
    geo.caja((ACCESO_N_X, y0 + 1.35, z0 + 3.06), (4.60, 2.60, 0.14), losa)
    for lado in (-1, 1):
        geo.caja((ACCESO_N_X + lado * 2.10, y0 + 2.45, z0 + 1.53),
                 (0.14, 0.14, 3.06), acero)
    geo.objeto(col, "JAR_Norte")

    texto("JAR_NorteRotulo", "PASO AL ANEXO · SALA DE JUNTAS",
          (ACCESO_N_X, y0 + 0.40, z0 + 3.24), 0.24, col,
          mat("M_Alm_Texto"),
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("JAR_NortePiso", "ANEXO · SALA DE JUNTAS",
          (ACCESO_N_X, y0 + 3.30, z0 + 0.11), 0.22, col,
          mat("M_Alm_Texto"), rot=(0.0, 0.0, 0.0))

# ------------------------------------------------------------------ redes
def build_redes(col):
    x0, x1, y0, y1 = RED
    z0 = RED_Z0
    techo = z0 + 3.60
    muro = mat("M_Adm_Muro")
    vidrio = mat("M_Adm_Vidrio")
    rack = mat("M_Red_Rack")
    patch = mat("M_Red_Patch")
    switch = mat("M_Red_Switch")
    led = mat("M_Red_Led")
    acero = mat("M_Alm_Acero")
    estructura = mat("M_Alm_Estructura")

    geo = Geo("RED_Sala")
    geog = geo
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.03),
             (x1 - x0, y1 - y0, 0.06), mat("M_Adm_Piso"))
    # muros: occidente, oriente y norte ciegos; sur vidriado con puerta
    geo.caja((x0 + 0.06, (y0 + y1) / 2, z0 + 1.85), (0.12, y1 - y0, 3.50), muro)
    geo.caja((x1 - 0.06, (y0 + y1) / 2, z0 + 1.85), (0.12, y1 - y0, 3.50), muro)
    geo.caja(((x0 + x1) / 2, y1 - 0.06, z0 + 1.85), (x1 - x0, 0.12, 3.50), muro)
    geo.caja(((x0 + x1) / 2, y0 + 0.05, z0 + 1.85),
             (x1 - x0, 0.06, 3.50), vidrio)
    geo.caja(((x0 + x1) / 2, y0 + 0.05, z0 + 3.55), (x1 - x0, 0.10, 0.12), acero)
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, techo + 0.08),
             (x1 - x0, y1 - y0, 0.16), muro)
    # piso tecnico y pasacables
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.10),
             (x1 - x0 - 0.3, y1 - y0 - 0.3, 0.10), mat("M_Alm_Acero"))
    geo.objeto(col, "RED_Sala")

    # cinco gabinetes con patch panels, switch, ODF y UPS
    rackes = Geo("RED_Racks")
    for i, x in enumerate([x0 + 0.75 + i * 0.80 for i in range(5)]):
        rackes.caja((x, y1 - 0.80, z0 + 1.05), (0.60, 0.80, 2.00), rack)
        rackes.caja((x, y1 - 1.22, z0 + 1.10), (0.54, 0.04, 1.80),
                    mat("M_Frio_Rejilla"))
        for k in range(4):
            rackes.caja((x, y1 - 1.24, z0 + 1.75 - k * 0.18), (0.46, 0.03, 0.10),
                        patch)
        rackes.caja((x, y1 - 1.26, z0 + 0.95), (0.46, 0.05, 0.16), switch)
        for k in range(8):
            rackes.caja((x - 0.19 + k * 0.055, y1 - 1.29, z0 + 0.95),
                        (0.02, 0.02, 0.03), led)
        rackes.caja((x, y1 - 1.26, z0 + 0.62), (0.46, 0.05, 0.14),
                    mat("M_Red_UPS"))
    # mesa de trabajo y punto de acceso de la propia sala
    rackes.caja(((x0 + x1) / 2, y0 + 0.95, z0 + 0.78),
                (1.60, 0.70, 0.06), mat("M_Adm_Mesa"))
    for dx in (-0.68, 0.68):
        rackes.caja(((x0 + x1) / 2 + dx, y0 + 0.95, z0 + 0.39),
                    (0.08, 0.60, 0.78), mat("M_Adm_Mueble"))
    rackes.caja(((x0 + x1) / 2, y0 + 0.95, z0 + 0.86),
                (0.44, 0.32, 0.10), mat("M_Red_UPS"))
    # bandeja de fibra hacia el cuarto de control
    rackes.caja(((x0 + x1) / 2, y0 + 0.60, techo - 0.20),
                (x1 - x0 - 0.4, 0.22, 0.08), acero)
    # puntos de acceso colgados en la nave, sobre el pasillo del corredor
    for x in (-24.0, -33.0):
        rackes.cilindro((x, -20.3, 7.60), 0.16, 0.05, mat("M_Frio_Sensor"), seg=12)
        rackes.cilindro((x, -20.3, 7.66), 0.06, 0.04, led, seg=10)
    rackes.objeto(col, "RED_Racks")

    t_blanco = mat("M_Alm_Texto")
    t_cian = mat("M_Alm_TextoAzul")
    texto("RED_Rotulo", "SALA TECNICA · REDES Y COMUNICACIONES",
          ((x0 + x1) / 2, y0 + 0.02, z0 + 3.10), 0.15, col, t_blanco,
          rot=(math.radians(90), 0.0, 0.0))
    texto("RED_Rotulo2", "FO · COBRE · SWITCHING · UPS",
          ((x0 + x1) / 2, y0 + 0.02, z0 + 2.84), 0.12, col, t_cian,
          rot=(math.radians(90), 0.0, 0.0))


# ------------------------------------------------------------------- build
def camara(nombre, loc, objetivo, lente=35.0):
    rig = coleccion("T99_RIG")
    for n in (nombre, nombre + "_Target"):
        viejo = bpy.data.objects.get(n)
        if viejo:
            bpy.data.objects.remove(viejo, do_unlink=True)
    tgt = bpy.data.objects.new(nombre + "_Target", None)
    tgt.location = objetivo
    rig.objects.link(tgt)
    datos = bpy.data.cameras.new(nombre)
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


# ------------------------------------------------------------------ anexo
def build_anexo(col):
    """Piso 2 del anexo: terraza al sur, volumen cerrado y escalera exterior."""
    x0, x1, y0, y1 = ADMIN
    z1 = SLAB + ADMIN_ALTO + 0.10        # losa del piso 2
    z2 = z1 + 3.40                       # cubierta
    losa = mat("M_Alm_Losa")
    muro = mat("M_Adm_Muro")
    vidrio = mat("M_Adm_Vidrio")
    acero = mat("M_Alm_Acero")

    geo = Geo("ANX_Piso2")
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z1 + 0.11),
             (x1 - x0 + 0.50, y1 - y0 + 0.50, 0.22), losa)
    # baranda de la terraza que queda sobre la cubierta de la planta baja
    for (cx, cy, sx, sy) in (((x0 + x1) / 2, y0 + 0.10, x1 - x0 + 0.5, 0.10),
                             (x0 - 0.20, y0 + 1.15, 0.10, 2.30),
                             (x1 + 0.20, y0 + 1.15, 0.10, 2.30)):
        geo.caja((cx, cy, z1 + 0.70), (sx, sy, 1.20), acero)

    # volumen cerrado, retranqueado 2,2 m al sur para dejar la terraza
    px0, px1 = x0 + 0.45, x1 - 0.45
    py0, py1 = y0 + 2.20, y1
    geo.caja(((px0 + px1) / 2, py0, z1 + 1.70), (px1 - px0, 0.16, 3.40), muro)
    geo.caja(((px0 + px1) / 2, py0 + 0.05, z1 + 1.95),
             ((px1 - px0) * 0.60, 0.06, 1.70), vidrio)
    for (cx, cy, sx, sy) in ((px0, (py0 + py1) / 2, 0.16, py1 - py0),
                             ((px0 + px1) / 2, py1 - 0.08, px1 - px0, 0.16)):
        geo.caja((cx, cy, z1 + 1.70), (sx, sy, 3.40), muro)
    # costado oriente acristalado: deja ver la sala de redes desde la escalera
    _ventanal(geo, "y", px1, py0 + 0.20, y0 + 5.60, z1 + 0.05, 3.30,
              vidrio, acero, antepecho=0.85, paso=1.55)
    geo.caja((px1, y0 + 6.35, z1 + 1.70), (0.16, 2.70, 3.40), muro)
    geo.caja(((px0 + px1) / 2, (py0 + py1) / 2, z2 + 0.18),
             (px1 - px0 + 0.90, py1 - py0 + 0.90, 0.36), losa)

    # escalera exterior sobre el costado oriental, con rellano y puerta
    pasos = 13
    dy = 5.20 / pasos
    dz = (z1 + 0.22 - SLAB) / pasos
    for k in range(pasos):
        geo.caja((px1 + 0.95, y0 + 0.60 + (k + 0.5) * dy,
                  SLAB + (k + 1) * dz - 0.08), (1.60, dy + 0.05, 0.16), acero)
    geo.caja((px1 + 0.95, y0 + 6.35, z1 + 0.11), (1.60, 1.50, 0.22), acero)
    for xr in (px1 + 0.32, px1 + 1.58):
        geo.caja((xr, y0 + 3.90, (SLAB + z1) / 2 + 0.55),
                 (0.06, 6.60, 1.10), acero)
    geo.caja((px1 - 0.03, y0 + 6.35, z1 + 1.05), (0.06, 1.00, 2.10), vidrio)

    # equipos de cubierta
    for dx in (-2.10, 1.90):
        geo.caja(((px0 + px1) / 2 + dx, (py0 + py1) / 2 + 0.60, z2 + 0.85),
                 (1.90, 1.60, 0.95), acero)
    geo.objeto(col, "ANX_Piso2")


def build_camaras():
    # los pabellones exentos se miran por dentro y desde el jardin
    camara("Cam_Frio", (-94.60, -26.20, SLAB + 2.00), (-79.00, -25.00,
          SLAB + 2.40), 20.0)
    camara("Cam_Admin", (-37.40, 21.50, SLAB + 2.60), (-30.00, 26.10,
          SLAB + 1.20), 22.0)
    camara("Cam_Energia", (-82.00, -2.00, SLAB + 2.50), (-91.00, -10.00,
          SLAB + 1.00), 26.0)
    camara("Cam_Redes", (-31.90, 24.95, 7.25), (-35.10, 27.40, 6.60), 24.0)
    camara("Cam_Pasillo_Tec", (-76.00, -28.40, SLAB + 1.75), (-76.00, -1.00,
          SLAB + 1.55), 26.0)
    camara("Cam_Jardin", (-72.00, -34.00, SLAB + 6.80), (-62.50, -14.00,
          SLAB + 1.40), 28.0)
    camara("Cam_Oeste", (-118.00, -50.00, 26.00), (-80.00, -12.00, 4.20),
           35.0)
    camara("Cam_Anexo_Ext", (-18.00, 36.00, 10.00), (-32.00, 26.00, 3.60),
           28.0)
    camara("Cam_Jardin_Norte", (-24.00, 27.00, 7.50), (-38.00, 18.00, 2.60),
           26.0)


def build():
    mats()
    cols = {}
    for nombre in ("T87_FRIO", "T88_ADMIN", "T89_ENERGIA", "T90_ANEXO",
                   "T92_REDES"):
        col = coleccion(nombre)
        vaciar(col)
        cols[nombre] = col

    build_plataforma(cols["T90_ANEXO"])
    build_frio(cols["T87_FRIO"])
    build_admin(cols["T88_ADMIN"])
    build_energia(cols["T89_ENERGIA"])
    build_pasillos(cols["T90_ANEXO"])
    build_jardin(cols["T90_ANEXO"])
    build_jardin_norte(cols["T90_ANEXO"])
    build_anexo(cols["T90_ANEXO"])
    build_redes(cols["T92_REDES"])
    build_camaras()
    bpy.context.view_layer.update()

    print("[CEDI360] programa: %d frio, %d admin, %d energia, %d anexo, %d redes"
          % (len(cols["T87_FRIO"].objects), len(cols["T88_ADMIN"].objects),
             len(cols["T89_ENERGIA"].objects), len(cols["T90_ANEXO"].objects),
             len(cols["T92_REDES"].objects)))
    return cols


build()
