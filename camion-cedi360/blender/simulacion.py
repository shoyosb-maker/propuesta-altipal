# -*- coding: utf-8 -*-
"""
CEDI 360 - Modulo de simulacion (panel de operacion)
====================================================
Levanta las piezas que el panel del visor mueve en vivo. No son decoracion:
cada objeto es una pieza con nombre propio y su pivote resuelto, para que el
visor pueda abrir un porton, correr la puerta del frio, mover un AMR o soltar
carga sin tocar el resto del modelo.

  SIM_Puerta_Muelle_N   porton seccional; pivote en el dintel (z = PUERTA_ALTO),
                        asi que escalar en Z lo recoge hacia arriba
  SIM_Puerta_Frio       hoja corredera del cuarto frio, cerrada; corre en Y
  SIM_Caja_NN           cartones de la simulacion de cargue y descargue
  SIM_Palet_NN          estibas bajo los cartones
  SIM_AMR_N             robots de almacen del corredor central
  SIM_Banda_Caja_NN     cajas que corren por el pasillo central
  SIM_Baliza_N          balizas de alarma sobre la banda de fachada

Los objetos que la simulacion esconde al arrancar (carga, AMR, cajas de banda,
balizas) viajan en el glb y el visor los apaga en el panel.

Uso:
    python blender\\client.py exec --file blender\\simulacion.py
"""

import math

import bpy
from mathutils import Euler, Vector

COLECCION = "T93_SIM"

SLAB = 1.25
HX0, HX1 = -62.0, -12.42
HY0, HY1 = -30.0, 16.0
PUERTAS = (-16.0, -8.0, 0.0)
PUERTA_ANCHO = 3.40
PUERTA_ALTO = 3.10
FRIO_X1 = -78.00
FRIO_YD = -23.00
CORREDOR = -20.3

AZUL = 0x00274B
AZUL_MEDIO = 0x0072B2
AMARILLO = 0xFBC710
TURQUESA = 0x5CDACE
ROJO = 0xD2463C
GRIS = 0x8C97A3


def lin(hexa):
    canales = (((hexa >> 16) & 255) / 255.0, ((hexa >> 8) & 255) / 255.0,
               (hexa & 255) / 255.0)
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                 for c in canales)


def material(nombre, hexa, emision=None, fuerza=0.0, rugosidad=0.65,
             metal=0.0, alpha=1.0):
    mat = bpy.data.materials.get(nombre)
    if not mat:
        mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nodos = mat.node_tree.nodes
    bsdf = nodos.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = lin(hexa) + (1.0,)
        bsdf.inputs["Roughness"].default_value = rugosidad
        bsdf.inputs["Metallic"].default_value = metal
        if alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
        if emision is not None:
            try:
                bsdf.inputs["Emission Color"].default_value = lin(emision) + (1.0,)
                bsdf.inputs["Emission Strength"].default_value = fuerza
            except KeyError:
                pass
    mat.diffuse_color = lin(hexa) + (alpha,)
    return mat


def mats():
    material("M_Sim_Puerta", 0xB8C4CC, emision=0x8FA2AE, fuerza=0.32,
             rugosidad=0.55, metal=0.25)
    material("M_Sim_PuertaFrio", 0x1E4C63, emision=AZUL_MEDIO, fuerza=0.30,
             rugosidad=0.45)
    material("M_Sim_Caja", 0xB09A72, emision=0x9C855F, fuerza=0.18,
             rugosidad=0.85)
    material("M_Sim_CajaClara", 0xDCE8F0, emision=0xE8F2F8, fuerza=0.24,
             rugosidad=0.80)
    material("M_Sim_Palet", 0x8A7147, emision=0x9A7F50, fuerza=0.12,
             rugosidad=0.88)
    material("M_Sim_AMR", 0x1B2530, emision=0x24313D, fuerza=0.18,
             rugosidad=0.55, metal=0.30)
    material("M_Sim_Led", TURQUESA, emision=TURQUESA, fuerza=2.4,
             rugosidad=0.30)
    material("M_Sim_Alarma", ROJO, emision=ROJO, fuerza=2.2, rugosidad=0.40)
    material("M_Sim_Acero", GRIS, emision=GRIS, fuerza=0.34, rugosidad=0.40,
             metal=0.45)


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
                self.v.append((centro[0] + p.x, centro[1] + p.y,
                               centro[2] + p.z))
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

    def objeto(self, col, nombre=None, loc=None):
        nombre = nombre or self.nombre
        malla = bpy.data.meshes.new(nombre)
        malla.from_pydata(self.v, [], self.f)
        malla.update()
        for clave in self.mats:
            malla.materials.append(bpy.data.materials[clave])
        for i, poli in enumerate(malla.polygons):
            poli.material_index = self.m[i]
        obj = bpy.data.objects.new(nombre, malla)
        if loc:
            obj.location = loc
        col.objects.link(obj)
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


def mat(nombre):
    return bpy.data.materials[nombre]


# ------------------------------------------------------------------ puertas
def build_puertas(col):
    """Portones seccionales y hoja corredera del cuarto frio."""
    puerta = mat("M_Sim_Puerta")
    acero = mat("M_Sim_Acero")
    for i, y in enumerate(PUERTAS):
        geo = Geo("SIM_Puerta_Muelle_%d" % i)
        # cinco panos colgados del dintel: el pivote queda arriba
        for k in range(5):
            geo.caja((0.0, 0.0, -0.32 - k * 0.60), (0.14, 3.28, 0.56),
                     puerta)
        geo.caja((0.0, 0.0, -3.05), (0.18, 3.28, 0.12), acero)
        for lado in (-1, 1):
            geo.caja((0.0, lado * 1.68, -1.55), (0.10, 0.10, 3.06), acero)
        geo.caja((0.0, 0.0, -3.02), (0.20, 0.60, 0.16), acero)
        geo.objeto(col, "SIM_Puerta_Muelle_%d" % i,
                   (HX1 + 0.42, y, PUERTA_ALTO))

    # hoja corredera del frio, cerrada sobre el vano
    frio = Geo("SIM_Puerta_Frio")
    frio.caja((0.0, 0.0, 0.0), (0.12, 2.10, 2.34), mat("M_Sim_PuertaFrio"))
    for k in range(4):
        frio.caja((0.09, 0.0, -0.84 + k * 0.56), (0.04, 1.94, 0.10), acero)
    frio.caja((0.0, 0.98, 0.10), (0.10, 0.10, 0.70), acero)
    frio.objeto(col, "SIM_Puerta_Frio",
                (FRIO_X1 + 0.16, FRIO_YD, SLAB + 1.22))


# ------------------------------------------------------------------- carga
def build_carga(col):
    """Cartones y estibas del simulacro de cargue y descargue."""
    caja = mat("M_Sim_Caja")
    clara = mat("M_Sim_CajaClara")
    palet = mat("M_Sim_Palet")
    n = 0
    for i, (cx, cy) in enumerate(((-10.90, -18.80), (-10.90, -16.60),
                                  (-10.90, -14.40))):
        p = Geo("SIM_Palet_%d" % i)
        p.caja((0.0, 0.0, 0.06), (1.20, 1.10, 0.12), palet)
        p.caja((0.0, 0.0, 0.16), (1.10, 1.00, 0.06), palet)
        p.objeto(col, "SIM_Palet_%d" % i, (cx, cy, SLAB))
        for k in range(4):
            c = Geo("SIM_Caja_%02d" % n)
            alto = 0.42
            c.caja((0.0, 0.0, alto / 2.0), (0.94, 0.84, alto),
                   clara if (n % 3 == 0) else caja)
            c.caja((0.0, 0.0, alto - 0.04), (0.96, 0.86, 0.06), caja)
            c.objeto(col, "SIM_Caja_%02d" % n,
                     (cx, cy, SLAB + 0.19 + k * (alto + 0.02)))
            n += 1


def build_sistemas(col):
    """AMR del corredor central y cajas que corren por el pasillo."""
    amr_m = mat("M_Sim_AMR")
    led = mat("M_Sim_Led")
    rueda = mat("M_Sim_Acero")
    for i, (x, y) in enumerate(((CORREDOR - 0.85, -12.0),
                                (CORREDOR + 0.85, 2.0))):
        geo = Geo("SIM_AMR_%d" % i)
        geo.caja((0.0, 0.0, 0.30), (1.10, 0.80, 0.26), amr_m)
        geo.caja((0.0, 0.0, 0.50), (0.90, 0.70, 0.14), amr_m)
        for dx in (-0.36, 0.36):
            for dy in (-0.34, 0.34):
                geo.cilindro((dx, dy, 0.12), 0.11, 0.10, rueda,
                             rot=(math.radians(90), 0.0, 0.0), seg=10)
        geo.caja((0.0, 0.0, 0.60), (0.24, 0.24, 0.10), led)
        geo.objeto(col, "SIM_AMR_%d" % i, (x, y, SLAB))

    caja = mat("M_Sim_Caja")
    for k in range(7):
        geo = Geo("SIM_Banda_Caja_%02d" % k)
        geo.caja((0.0, 0.0, 0.22), (0.60, 0.52, 0.44), caja)
        geo.caja((0.0, 0.0, 0.42), (0.62, 0.54, 0.05), mat("M_Sim_CajaClara"))
        geo.objeto(col, "SIM_Banda_Caja_%02d" % k,
                   (CORREDOR + 0.10, -16.0 + k * 4.0, SLAB))


def build_balizas(col):
    """Balizas de alarma sobre la banda de la fachada este."""
    alarma = mat("M_Sim_Alarma")
    acero = mat("M_Sim_Acero")
    for i, y in enumerate((-16.0, -8.0, 0.0)):
        geo = Geo("SIM_Baliza_%d" % i)
        geo.caja((0.0, 0.0, 0.06), (0.20, 0.20, 0.12), acero)
        geo.cilindro((0.0, 0.0, 0.26), 0.14, 0.30, alarma, seg=12)
        geo.objeto(col, "SIM_Baliza_%d" % i, (HX1 + 0.34, y, 3.62))


def build():
    mats()
    col = coleccion(COLECCION)
    vaciar(col)
    build_puertas(col)
    build_carga(col)
    build_sistemas(col)
    build_balizas(col)
    print("[CEDI360] simulacion: %d objetos en %s"
          % (len(col.objects), COLECCION))
    return col


build()
