# -*- coding: utf-8 -*-
"""
CEDI 360 - Programa de areas nuevas del CEDI
============================================
Levanta las areas que la propuesta necesita para poder recorrerse dentro del
modelo: cada eje y cada frente de operacion tiene un sitio fisico donde
mostrarse.

Colecciones (todas visibles en cualquier fase, sin capa propia):
  T87_FRIO      cuarto frio de lacteos y refrigerados, con su monitoreo
  T88_ADMIN     area administrativa con sala de juntas y pantalla
  T89_ENERGIA   subestacion, tablero general, UPS y banco de condensadores
  T92_REDES     sala tecnica de redes, racks y puntos de acceso

Coordenadas: nave de x -56 a -12,42 y de y -30 a 16, piso a SLAB = 1,25.
El cuarto frio va en la franja sur, contra el corredor; la administracion en
la franja este bajo el entrepiso del cuarto de control; la subestacion en la
esquina suroeste y las redes en la franja norte.

Modulo autocontenido e idempotente.

Uso:
    python blender\\client.py exec --file blender\\programa.py
"""

import math

import bpy
from mathutils import Euler, Vector

# --------------------------------------------------------------- geometria
SLAB = 1.25
HX0, HX1 = -56.0, -12.42
HY0, HY1 = -30.0, 16.0

FRIO = (-46.4, -35.4, -29.2, -21.0)     # x0, x1, y0, y1
FRIO_ALTO = 6.00                        # de SLAB hacia arriba
ADMIN = (-21.90, -13.70, 9.60, 15.80)
ADMIN_ALTO = 4.10                       # techo a 5,35 (entrepiso del control)
ENE = (-55.10, -48.40, -29.40, -24.10)
RED = (-30.20, -26.40, 12.40, 15.70)

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
    panel = mat("M_Frio_Panel")
    cielo = mat("M_Frio_Cielo")
    piso = mat("M_Frio_Piso")
    zocalo = mat("M_Frio_Zocalo")
    puerta = mat("M_Frio_Puerta")

    geo = Geo("FRIO_Camara")
    # piso sanitario con zocalo y rejilla de drenaje
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.03),
             (x1 - x0 - 0.24, y1 - y0 - 0.24, 0.06), piso)
    for (cx, cy, sx, sy) in (((x0 + x1) / 2, y0 + 0.06, x1 - x0, 0.12),
                             ((x0 + x1) / 2, y1 - 0.06, x1 - x0, 0.12),
                             (x0 + 0.06, (y0 + y1) / 2, 0.12, y1 - y0),
                             (x1 - 0.06, (y0 + y1) / 2, 0.12, y1 - y0)):
        geo.caja((cx, cy, z0 + 0.08), (sx, sy, 0.16), zocalo)
    # paneleria: cuatro muros y cubierta
    geo.caja(((x0 + x1) / 2, y0 + 0.06, z0 + FRIO_ALTO / 2),
             (x1 - x0, 0.12, FRIO_ALTO), panel)
    geo.caja(((x0 + x1) / 2, y1 - 0.06, z0 + FRIO_ALTO / 2),
             (x1 - x0, 0.12, FRIO_ALTO), panel)
    geo.caja((x0 + 0.06, (y0 + y1) / 2, z0 + FRIO_ALTO / 2),
             (0.12, y1 - y0, FRIO_ALTO), panel)
    geo.caja((x1 - 0.06, (y0 + y1) / 2, z0 + FRIO_ALTO / 2),
             (0.12, y1 - y0, FRIO_ALTO), panel)
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, techo + 0.06),
             (x1 - x0, y1 - y0, 0.12), cielo)
    # nervios de la paneleria: cada 1,15 m
    x = x0 + 0.30
    while x < x1:
        for yw in (y0 + 0.13, y1 - 0.13):
            geo.caja((x, yw, z0 + FRIO_ALTO / 2), (0.05, 0.03, FRIO_ALTO),
                     zocalo)
        x += 1.15
    # vano de la puerta corredera en el muro norte
    puerta_x = (x0 + x1) / 2
    geo.caja((puerta_x, y1 - 0.06, z0 + 2.36), (2.30, 0.16, 0.16), zocalo)
    for lado in (-1, 1):
        geo.caja((puerta_x + lado * 1.18, y1 - 0.06, z0 + 1.20),
                 (0.16, 0.16, 2.36), zocalo)
    # hoja corredera (abierta hacia el oriente) + cortina de lamina
    geo.caja((puerta_x + 1.90, y1 + 0.16, z0 + 1.22), (2.10, 0.10, 2.34),
             puerta)
    geo.caja((puerta_x + 1.90, y1 + 0.16, z0 + 2.46), (2.20, 0.14, 0.10),
             zocalo)
    for k in range(7):
        xl = puerta_x - 0.96 + k * 0.32
        geo.caja((xl, y1 + 0.02, z0 + 1.30), (0.28, 0.02, 2.20),
                 mat("M_Alm_Vidrio"))
    # rampa de acceso con tope
    geo.caja((puerta_x, y1 + 0.60, z0 + 0.06), (2.60, 1.00, 0.12), zocalo)
    geo.objeto(col, "FRIO_Camara")

    # estanteria interior: tres modulos de 3 m, tres niveles
    nivel_z = (z0 + 0.90, z0 + 3.10, z0 + 5.10)
    est = Geo("FRIO_Estanteria")
    for b in range(4):
        xb = x0 + 1.10 + b * 2.95
        for dy in (-0.55, 0.55):
            est.caja((xb, y0 + 3.60 + dy, z0 + 3.00), (0.09, 0.09, 5.60),
                     mat("M_Alm_Rack"))
    for z in nivel_z:
        est.caja((x0 + 5.52, y0 + 3.60, z), (9.10, 1.30, 0.12),
                 mat("M_Alm_Acero"))
    est.objeto(col, "FRIO_Estanteria")

    # producto palletizado dentro de la camara
    prod = Geo("FRIO_Producto")
    for i, x in enumerate((x0 + 2.2, x0 + 5.1, x0 + 8.0)):
        for z in nivel_z:
            prod.caja((x, y0 + 3.60, z + 0.20), (1.20, 1.10, 0.14),
                      mat("M_Alm_Madera"))
            for dx in (-0.28, 0.28):
                for dy in (-0.25, 0.25):
                    caja_fria(prod, x + dx, y0 + 3.60 + dy, z + 0.42,
                              0.52, 0.46, 0.60)
    for x in (x0 + 2.0, x0 + 8.4):
        prod.caja((x, y0 + 1.60, z0 + 0.09), (1.20, 1.00, 0.14),
                  mat("M_Alm_Madera"))
        for dx in (-0.28, 0.28):
            for dy in (-0.22, 0.22):
                caja_fria(prod, x + dx, y0 + 1.60 + dy, z0 + 0.32,
                          0.52, 0.44, 0.52)
    prod.objeto(col, "FRIO_Producto")

    # evaporadores, condensadora y linea de refrigerante
    eq = Geo("FRIO_Equipo")
    for x in (x0 + 2.8, x0 + 7.6):
        eq.caja((x, y0 + 2.10, techo - 0.55), (2.20, 0.80, 0.55),
                mat("M_Frio_Unidad"))
        eq.caja((x, y0 + 2.10, techo - 0.86), (1.90, 0.62, 0.10),
                mat("M_Frio_Rejilla"))
        for k in (-1, 1):
            eq.cilindro((x + k * 0.52, y0 + 1.72, techo - 0.86), 0.22, 0.08,
                        mat("M_Frio_Rejilla"), rot=(math.radians(90), 0.0, 0.0),
                        seg=12)
        eq.caja((x, y0 + 2.10, techo - 0.24), (0.42, 0.42, 0.10),
                mat("M_Frio_Zocalo"))
    # condensadora exterior, junto al muro oriente de la camara
    eq.caja((x1 + 1.30, y0 + 2.40, z0 + 0.72), (1.40, 0.95, 1.30),
            mat("M_Frio_Unidad"))
    eq.caja((x1 + 1.30, y0 + 2.40, z0 + 1.42), (1.50, 1.05, 0.10),
            mat("M_Frio_Rejilla"))
    eq.caja((x1 + 0.62, y0 + 2.40, z0 + 1.10), (0.24, 0.30, 2.10),
            mat("M_Frio_Tubo"))
    eq.caja((x1 + 0.20, y0 + 2.40, z0 + 2.16), (0.80, 0.24, 0.16),
            mat("M_Frio_Tubo"))
    eq.objeto(col, "FRIO_Equipo")

    # monitoreo de cadena de frio: sondas, registrador, panel y baliza
    sen = Geo("FRIO_Monitoreo")
    for (x, z) in ((x0 + 1.60, z0 + 1.70), (x0 + 6.40, z0 + 4.10),
                   (x0 + 9.40, z0 + 1.70)):
        sen.caja((x, y0 + 0.30, z), (0.12, 0.20, 0.24), mat("M_Frio_Sensor"))
        sen.caja((x, y0 + 0.19, z + 0.14), (0.06, 0.03, 0.06),
                 mat("M_Frio_Lente"))
    sen.caja((x0 + 1.60, y0 + 0.30, z0 + 2.10), (0.16, 0.22, 0.16),
             mat("M_Frio_Sensor"))
    # contacto magnetico de puerta
    sen.caja((puerta_x - 1.18, y1 - 0.22, z0 + 1.90), (0.10, 0.08, 0.22),
             mat("M_Frio_Sensor"))
    sen.caja((puerta_x + 0.92, y1 - 0.22, z0 + 1.90), (0.10, 0.08, 0.22),
             mat("M_Frio_Sensor"))
    # detector de fuga de refrigerante junto al evaporador
    sen.caja((x0 + 2.8, y0 + 1.66, techo - 1.16), (0.16, 0.10, 0.20),
             mat("M_Frio_Sensor"))
    # registrador y panel de control al lado de la puerta, por fuera
    sen.caja((puerta_x + 2.95, y1 + 0.14, z0 + 1.55), (0.42, 0.16, 0.58),
             mat("M_Frio_Sensor"))
    sen.caja((puerta_x + 2.95, y1 + 0.24, z0 + 1.66), (0.30, 0.02, 0.24),
             mat("M_Frio_Lente"))
    sen.caja((puerta_x + 2.95, y1 + 0.06, z0 + 1.16), (0.34, 0.10, 0.06),
             mat("M_Frio_Led"))
    # baliza de alarma sobre la puerta
    sen.cilindro((puerta_x - 1.70, y1 + 0.10, techo - 0.30), 0.14, 0.24,
                 mat("M_Frio_Alarma"), seg=12)
    # bandeja portacables y canalizacion de datos
    sen.caja(((x0 + x1) / 2, y0 + 1.10, techo - 0.22), (x1 - x0 - 0.4, 0.30, 0.08),
             mat("M_Alm_Acero"))
    sen.caja((x1 - 0.30, y0 + 1.10, techo - 0.55), (0.10, 0.10, 0.70),
             mat("M_Alm_Acero"))
    sen.objeto(col, "FRIO_Monitoreo")
    sin_lineas([bpy.data.objects.get("FRIO_Monitoreo")])

    # rotulos
    t_azul = mat("M_Alm_TextoAzul")
    t_blanco = mat("M_Alm_Texto")
    texto("FRIO_Rotulo", "CUARTO FRIO · LACTEOS Y REFRIGERADOS",
          (puerta_x, y1 + 0.18, z0 + 3.30), 0.30, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("FRIO_Rotulo2", "2 °C A 4 °C · CADENA DE FRIO MONITOREADA",
          (puerta_x, y1 + 0.18, z0 + 2.92), 0.20, col, t_azul,
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("FRIO_Rotulo3", "LACTEOS · REFRIGERADOS · CONGELADOS",
          (x0 + 0.20, (y0 + y1) / 2, z0 + 4.60), 0.26, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(90)))
    texto("FRIO_PisoMarca", "ZONA DE FRIO · NO BLOQUEAR",
          (puerta_x, y1 + 1.60, z0 + 0.016), 0.24, col, t_blanco,
          rot=(0.0, 0.0, 0.0))


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
    # piso y cielo raso
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 0.02),
             (x1 - x0, y1 - y0, 0.04), piso)
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, techo + 0.10),
             (x1 - x0, y1 - y0, 0.20), muro)
    # muros perimetrales (sur con puerta, oriente, occidente y norte)
    geo.caja(((x0 + x1) / 2, y0 + 0.06, z0 + ADMIN_ALTO / 2),
             (x1 - x0, 0.12, ADMIN_ALTO), muro)
    geo.caja((x1 - 0.06, (y0 + y1) / 2, z0 + ADMIN_ALTO / 2),
             (0.12, y1 - y0, ADMIN_ALTO), muro)
    geo.caja((x0 + 0.06, (y0 + y1) / 2, z0 + ADMIN_ALTO / 2),
             (0.12, y1 - y0, ADMIN_ALTO), muro)
    geo.caja(((x0 + x1) / 2, y1 - 0.06, z0 + ADMIN_ALTO / 2),
             (x1 - x0, 0.12, ADMIN_ALTO), muro)
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
    # sillas: tres por lado largo y una en cada cabecera
    for dy in (-1.10, 0.0, 1.10):
        silla(mob, mx - 0.80, my + dy, giro=math.radians(90))
        silla(mob, mx + 0.80, my + dy, giro=math.radians(-90))
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
    cabina = mat("M_Ene_Cabina")
    tablero = mat("M_Ene_Tablero")
    breaker = mat("M_Ene_Breaker")
    ups = mat("M_Ene_UPS")
    acero = mat("M_Alm_Acero")

    geo = Geo("ENE_Subestacion")
    # cerramiento bajo con malla y puerta
    for (cx, cy, sx, sy) in (((x0 + x1) / 2, y0 + 0.05, x1 - x0, 0.10),
                             ((x0 + x1) / 2, y1 - 0.05, x1 - x0, 0.10),
                             (x0 + 0.05, (y0 + y1) / 2, 0.10, y1 - y0),
                             (x1 - 0.05, (y0 + y1) / 2, 0.10, y1 - y0)):
        geo.caja((cx, cy, z0 + 1.10), (sx, sy, 2.20), acero)
    # transformador de 500 kVA con rejillas y aviso
    geo.caja((x0 + 1.90, (y0 + y1) / 2, z0 + 1.05), (1.80, 1.50, 2.10),
             cabina)
    for k in range(5):
        geo.caja((x0 + 1.90, (y0 + y1) / 2 - 0.70 + k * 0.35, z0 + 1.75),
                 (1.50, 0.16, 0.10), breaker)
    geo.caja((x0 + 1.90, (y0 + y1) / 2, z0 + 2.16), (1.90, 1.60, 0.10),
             cabina)
    # tablero general de baja tension con sus circuitos
    geo.caja((x0 + 4.30, y0 + 1.20, z0 + 1.15), (2.20, 0.70, 2.30), tablero)
    for k in range(6):
        geo.caja((x0 + 3.55 + k * 0.30, y0 + 0.84, z0 + 1.85),
                 (0.22, 0.06, 0.30), breaker)
    for k in range(4):
        geo.caja((x0 + 3.70 + k * 0.36, y0 + 0.84, z0 + 1.20),
                 (0.26, 0.06, 0.24), breaker)
    # UPS de la sala de control y del cuarto frio
    geo.caja((x0 + 4.60, y1 - 0.90, z0 + 0.95), (0.90, 0.85, 1.90), ups)
    geo.caja((x0 + 4.60, y1 - 0.44, z0 + 1.55), (0.60, 0.04, 0.40),
             mat("M_Frio_Lente"))
    # banco de condensadores
    geo.caja((x0 + 1.60, y1 - 0.85, z0 + 1.05), (1.50, 0.60, 2.10), tablero)
    # bandeja y ductos hacia la nave
    geo.caja(((x0 + x1) / 2, (y0 + y1) / 2, z0 + 2.80), (x1 - x0 - 1.0, 0.35, 0.10),
             acero)
    geo.caja((x1 - 0.20, (y0 + y1) / 2, z0 + 2.40), (0.20, 0.35, 0.90),
             acero)
    geo.objeto(col, "ENE_Subestacion")

    t_blanco = mat("M_Alm_Texto")
    t_ambar = mat("M_Ene_Aviso")
    texto("ENE_Rotulo", "SUBESTACION 500 kVA · TABLERO GENERAL",
          ((x0 + x1) / 2, y1 - 0.20, z0 + 2.60), 0.18, col, t_blanco,
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("ENE_Aviso", "ALTA TENSION · SOLO PERSONAL AUTORIZADO",
          ((x0 + x1) / 2, y1 - 0.22, z0 + 2.20), 0.14, col, t_ambar,
          rot=(math.radians(90), 0.0, math.radians(180)))
    texto("ENE_Piso", "SUBESTACION",
          ((x0 + x1) / 2, y0 + 1.10, z0 + 0.018), 0.40, col, t_blanco,
          rot=(0.0, 0.0, 0.0))


# ------------------------------------------------------------------ redes
def build_redes(col):
    x0, x1, y0, y1 = RED
    z0 = SLAB
    techo = z0 + 3.60
    muro = mat("M_Adm_Muro")
    vidrio = mat("M_Adm_Vidrio")
    rack = mat("M_Red_Rack")
    patch = mat("M_Red_Patch")
    switch = mat("M_Red_Switch")
    led = mat("M_Red_Led")
    acero = mat("M_Alm_Acero")

    geo = Geo("RED_Sala")
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

    # dos gabinetes con patch panels, switch, ODF y UPS
    rackes = Geo("RED_Racks")
    for i, x in enumerate((x0 + 0.75, x0 + 1.55)):
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


def build_camaras():
    # interiores: las cuatro areas son cuartos cerrados, se miran por dentro
    camara("Cam_Frio", (-36.4, -22.3, 3.1), (-44.6, -26.2, 2.2), 22.0)
    camara("Cam_Admin", (-20.8, 10.1, 2.7), (-15.3, 13.9, 1.7), 20.0)
    camara("Cam_Energia", (-42.8, -19.6, 8.2), (-51.6, -26.6, 2.2), 30.0)
    camara("Cam_Redes", (-29.9, 13.0, 2.3), (-27.2, 15.3, 1.2), 22.0)


def build():
    mats()
    cols = {}
    for nombre in ("T87_FRIO", "T88_ADMIN", "T89_ENERGIA", "T92_REDES"):
        col = coleccion(nombre)
        vaciar(col)
        cols[nombre] = col

    build_frio(cols["T87_FRIO"])
    build_admin(cols["T88_ADMIN"])
    build_energia(cols["T89_ENERGIA"])
    build_redes(cols["T92_REDES"])
    build_camaras()
    bpy.context.view_layer.update()

    print("[CEDI360] programa: %d frio, %d admin, %d energia, %d redes"
          % (len(cols["T87_FRIO"].objects), len(cols["T88_ADMIN"].objects),
             len(cols["T89_ENERGIA"].objects), len(cols["T92_REDES"].objects)))
    return cols


build()
