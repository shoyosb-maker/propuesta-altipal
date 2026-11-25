# -*- coding: utf-8 -*-
"""
CEDI 360 - Detalles de marca y acabados
=======================================
Anade al camion:
  - el lema de ALTIPAL y la marca CEDI 360 sobre la pared del contenedor,
  - la firma de FUNDASERINCO en el frente,
  - espejos retrovisores y franja de seguridad en el chasis.

El texto de la pared cuelga de GRP_PARED_DER, asi que viaja con el despiece.
"""

import bpy
from math import radians
from mathutils import Matrix, Vector

COLLECTION = "T06_DETALLES"
C_CYAN = (0.55, 0.74, 1.0)
C_AMBER = (0.98, 0.76, 0.10)
C_PAPER = (0.88, 0.92, 0.96)

CONT_W = 2.438
CONT_CY = -6.30

T_LEMA_A = "ENTREGAMOS CONFIANZA,"
T_LEMA_B = "NO SOLO PRODUCTOS"
T_MARCA = "CEDI 360"
T_FIRMA = "FUNDASERINCO \u00b7 INGENIER\u00cdA Y TECNOLOG\u00cdA"


def col():
    coleccion = bpy.data.collections.get(COLLECTION)
    if coleccion:
        for obj in list(coleccion.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        coleccion = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(coleccion)
    return coleccion


def mat(name, rgb, strength):
    existente = bpy.data.materials.get(name)
    if existente:
        return existente
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    try:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    except KeyError:
        pass
    return m


def texto(nombre, cuerpo, loc, size, material, coleccion, parent,
          hacia=Vector((1, 0, 0)), align="CENTER", line=1.0):
    curve = bpy.data.curves.new(nombre, type="FONT")
    curve.body = cuerpo
    curve.size = size
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.space_line = line
    obj = bpy.data.objects.new(nombre, curve)
    obj.location = loc
    obj.rotation_euler = (radians(90), 0.0, radians(90))
    coleccion.objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def caja(nombre, size, loc, material, coleccion, parent):
    sx, sy, sz = size
    mesh = bpy.data.meshes.new(nombre)
    verts = [
        (-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
        (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
        (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
        (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(nombre, mesh)
    obj.location = loc
    coleccion.objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def build():
    coleccion = col()
    pared = bpy.data.objects.get("GRP_PARED_DER")
    cabina = bpy.data.objects.get("GRP_CABINA")
    chasis = bpy.data.objects.get("GRP_CHASIS")

    blanco = mat("M_MarcaBlanca", (0.90, 0.93, 0.97), 1.1)
    ambar = mat("M_MarcaAmbar", C_AMBER, 1.8)
    cian = mat("M_MarcaCian", C_CYAN, 1.2)

    x_cara = CONT_W / 2 + 0.165

    texto("DET_Marca", T_MARCA, (x_cara, CONT_CY - 4.55, 3.00), 0.62, ambar,
          coleccion, pared)
    texto("DET_Firma", T_FIRMA, (x_cara, CONT_CY - 4.55, 2.42), 0.19, cian,
          coleccion, pared)
    texto("DET_LemaA", T_LEMA_A, (x_cara, CONT_CY + 0.55, 3.02), 0.37, blanco,
          coleccion, pared)
    texto("DET_LemaB", T_LEMA_B, (x_cara, CONT_CY + 0.55, 2.52), 0.37, blanco,
          coleccion, pared)
    texto("DET_Lado", "2026", (x_cara, CONT_CY + 4.55, 2.80), 0.26, cian,
          coleccion, pared)

    if cabina:
        for lado in (-1, 1):
            caja("DET_Espejo_%d" % lado, (0.10, 0.16, 0.62),
                 (lado * 1.52, 2.30, 2.45), ambar, coleccion, cabina)
            caja("DET_Brazo_%d" % lado, (0.42, 0.05, 0.05),
                 (lado * 1.32, 2.30, 2.62), cian, coleccion, cabina)
        caja("DET_Deflector_Luz", (2.10, 0.06, 0.07), (0, 1.16, 3.44), ambar,
             coleccion, cabina)

    if chasis:
        for lado in (-1, 1):
            caja("DET_Franja_%d" % lado, (0.04, 9.60, 0.10),
                 (lado * 1.16, -7.10, 1.16), ambar, coleccion, chasis)

    bpy.context.view_layer.update()
    print("[CEDI360] detalles de marca listos: %d objetos" % len(coleccion.objects))


if __name__ == "__main__":
    build()
