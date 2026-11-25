"""
CEDI 360 · Construcción procedural del camión y el contenedor
============================================================
Dimensiones reales tomadas de "el pront.txt":
  - Contenedor ISO 40 ft HC: 12.192 x 2.438 x 2.896 m
  - Chasis portacontenedores: 12.35 x 2.48 m, piso a 1.30 m
  - 3 ejes traseros separados 1.31 m, llanta Ø 1.07 m
  - Cabina tractora: 2.30 x 2.50 x 3.65 m
  - Estiba GMA: 1.20 x 1.00 x 0.145 m; 20 estibas

Se ejecuta dentro de Blender a través del puente. Es idempotente: borra las
colecciones del proyecto antes de reconstruir.
"""

import bmesh
import bpy
import math
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_DIR = os.path.join(PROJECT_DIR, "render")

# ---------------------------------------------------------------- constantes
CONT_L = 12.192
CONT_W = 2.438
CONT_H = 2.896
DECK_Z = 1.30
CONT_CY = -6.30
CAMION_X = 8.00             # ubicar_camion.py corre el camion a x = 8
CONT_Z0 = DECK_Z
TRAILER_L = 12.35
TIRE_R = 0.535
TIRE_W = 0.38
AXLE_Y = (-9.55, -10.86, -12.17)
CAB_W = 2.50
CAB_L = 2.30
CAB_H = 3.65

AMBER = (0.965, 0.745, 0.055)
AMBER_DIM = (0.55, 0.40, 0.03)
CYAN = (0.50, 0.69, 1.0)
INK = (0.012, 0.020, 0.031)
STEEL = (0.09, 0.11, 0.13)
PAPER = (0.85, 0.87, 0.90)

COLLECTIONS = {}
MATS = {}

COL_FILTRO = "T91_SIN_LINEAS"


# ---------------------------------------------------------------- utilidades
def _reset():
    for name in ("T01_CHASIS", "T02_CONTENEDOR", "T03_CARGA", "T04_TELEMETRIA",
                 "T05_CABINA", "T07_HOLOGRAMA", "T90_ANOTACIONES", "T99_RIG"):
        col = bpy.data.collections.get(name)
        if col:
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(col)
    for obj in list(bpy.data.objects):
        if obj.name in ("MASTER_DESPIECE", "Cam_Isometrica", "Cam_Target", "Suelo"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for empty in ("GRP_TECHO", "GRP_CARGA", "GRP_PARED_IZQ", "GRP_PARED_DER",
                  "GRP_PUERTA_IZQ", "GRP_PUERTA_DER", "GRP_FRONTAL", "GRP_CABINA",
                  "GRP_HOLOGRAMA", "GRP_CHASIS", "GRP_CONTENEDOR"):
        obj = bpy.data.objects.get(empty)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mat in [m for m in bpy.data.materials if m.name.startswith("M_")]:
        bpy.data.materials.remove(mat, do_unlink=True)
    MATS.clear()


def collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    COLLECTIONS[name] = col
    return col


def empty(name, col, size=0.6):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = size
    col.objects.link(obj)
    return obj


def material(name, color, emission=None, strength=0.0, roughness=0.55, metallic=0.0, alpha=1.0):
    mat = bpy.data.materials.get(name)
    if mat:
        MATS[name] = mat
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        try:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = strength
        except KeyError:
            pass
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        mat.use_backface_culling = False
    MATS[name] = mat
    return mat


def _assign(obj, mat):
    if mat is not None:
        obj.data.materials.append(mat)


def box(name, size, loc, col, mat=None, bevel=0.0, rot=(0.0, 0.0, 0.0), parent=None):
    sx, sy, sz = size
    mesh = bpy.data.meshes.new(name)
    verts = [
        (-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
        (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
        (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
        (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    if bevel > 0:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    _assign(obj, mat)
    return obj


def cylinder(name, radius, depth, loc, col, mat=None, segments=28,
             axis="Z", parent=None, rot=(0.0, 0.0, 0.0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=radius, radius2=radius, depth=depth)
    except TypeError:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              diameter1=radius * 2, diameter2=radius * 2, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    if axis == "X":
        obj.rotation_euler = (0.0, math.radians(90), 0.0)
    elif axis == "Y":
        obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    obj.rotation_euler = (
        obj.rotation_euler.x + rot[0],
        obj.rotation_euler.y + rot[1],
        obj.rotation_euler.z + rot[2],
    )
    col.objects.link(obj)
    if parent:
        obj.parent = parent
    _assign(obj, mat)
    return obj


def text(name, body, loc, size, col, mat, rot=(math.radians(90), 0, 0), align="CENTER"):
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    obj = bpy.data.objects.new(name, curve)
    obj.location = loc
    obj.rotation_euler = rot
    col.objects.link(obj)
    _assign(obj, mat)
    return obj


def driver_multi(obj, prop, variables, expression):
    """Driver con varias propiedades de MASTER_DESPIECE."""
    fc = obj.driver_add(prop[0], prop[1])
    drv = fc.driver
    drv.type = "SCRIPTED"
    for nombre in variables:
        var = drv.variables.new()
        var.name = nombre
        var.type = "SINGLE_PROP"
        var.targets[0].id = bpy.data.objects["MASTER_DESPIECE"]
        var.targets[0].data_path = '["%s"]' % nombre
    drv.expression = expression
    return drv


def driver(obj, prop, var, expression):
    """Driver de una sola propiedad de MASTER_DESPIECE sobre un canal de obj."""
    fc = obj.driver_add(prop[0], prop[1])
    drv = fc.driver
    drv.type = "SCRIPTED"
    variable = drv.variables.new()
    variable.name = var
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = bpy.data.objects["MASTER_DESPIECE"]
    variable.targets[0].data_path = '["%s"]' % var
    drv.expression = expression
    return drv


# ---------------------------------------------------------------- materiales
def build_materials():
    material("M_Tinta", INK, roughness=0.9)
    material("M_Acero", (0.028, 0.034, 0.045), emission=(0.02, 0.03, 0.045), strength=0.18, roughness=0.6)
    material("M_Ambar", (0.10, 0.08, 0.01), emission=AMBER, strength=2.4, roughness=0.4)
    material("M_AmbarSuave", (0.016, 0.017, 0.022), emission=(0.42, 0.32, 0.035), strength=0.05, roughness=0.65)
    material("M_Cian", (0.02, 0.05, 0.09), emission=CYAN, strength=0.45, roughness=0.4)
    material("M_Carga", (0.025, 0.045, 0.075), emission=(0.10, 0.18, 0.28), strength=0.30, alpha=0.85)
    material("M_Vidrio", (0.015, 0.025, 0.045), emission=(0.18, 0.26, 0.38), strength=0.35, alpha=0.5)
    material("M_Holograma", (0.05, 0.12, 0.18), emission=(0.95, 0.72, 0.15), strength=2.4, alpha=0.25)


# ---------------------------------------------------------------- chasis
def build_chassis():
    col = collection("T01_CHASIS")
    grupo = empty("GRP_CHASIS", col)

    for x in (-0.95, 0.95):
        box("Viga_%s" % ("Izq" if x < 0 else "Der"), (0.15, TRAILER_L, 0.45),
            (x, -6.15, DECK_Z - 0.225), col, MATS["M_Acero"], bevel=0.008, parent=grupo)
        box("Ala_%s" % ("Izq" if x < 0 else "Der"), (0.40, TRAILER_L, 0.03),
            (x, -6.15, DECK_Z - 0.01), col, MATS["M_Acero"], parent=grupo)

    for i in range(11):
        y = -12.4 + i * 1.18
        box("Travesano_%02d" % i, (1.95, 0.08, 0.16), (0, y, DECK_Z - 0.30),
            col, MATS["M_Acero"], parent=grupo)

    box("Placa_Kingpin", (1.20, 0.70, 0.06), (0, 0.05, DECK_Z - 0.03), col, MATS["M_Acero"], parent=grupo)
    cylinder("Kingpin", 0.05, 0.18, (0, 0.05, DECK_Z - 0.15), col, MATS["M_Ambar"], axis="Z", parent=grupo)

    for x in (-0.85, 0.85):
        box("Pata_%s" % ("Izq" if x < 0 else "Der"), (0.12, 0.12, 0.62),
            (x, -2.60, 0.31), col, MATS["M_Acero"], parent=grupo)
        box("Pie_%s" % ("Izq" if x < 0 else "Der"), (0.30, 0.26, 0.05),
            (x, -2.60, 0.025), col, MATS["M_Acero"], parent=grupo)

    for idx, y in enumerate(AXLE_Y):
        cylinder("Eje_%d" % idx, 0.055, 2.30, (0, y, TIRE_R), col, MATS["M_Acero"], axis="X", parent=grupo)
        for side in (-1, 1):
            x = side * 1.05
            cylinder("Llanta_%d_%s" % (idx, "I" if side < 0 else "D"), TIRE_R, TIRE_W,
                     (x, y, TIRE_R), col, MATS["M_Acero"], axis="X", parent=grupo)
            cylinder("Rin_%d_%s" % (idx, "I" if side < 0 else "D"), 0.30, TIRE_W + 0.02,
                     (x, y, TIRE_R), col, MATS["M_AmbarSuave"], axis="X", parent=grupo)
        box("Guardafango_%d" % idx, (2.35, 0.95, 0.04), (0, y, TIRE_R * 2 + 0.06),
            col, MATS["M_Acero"], parent=grupo)

    box("Parachoques", (2.40, 0.10, 0.22), (0, -12.42, 0.78), col, MATS["M_Acero"], parent=grupo)
    for x in (-0.95, 0.0, 0.95):
        box("Luz_Trasera_%s" % x, (0.18, 0.05, 0.10), (x, -12.47, 0.78), col, MATS["M_Ambar"], parent=grupo)

    # Racks laterales de UPS / baterías (Fase 1)
    for x in (-0.72, 0.72):
        box("Rack_UPS_%s" % ("Izq" if x < 0 else "Der"), (0.60, 1.20, 0.50),
            (x, -4.10, 0.78), col, MATS["M_Cian"], parent=grupo)
    return grupo


# ---------------------------------------------------------------- contenedor
def build_container():
    col = collection("T02_CONTENEDOR")
    grupo = empty("GRP_CONTENEDOR", col)

    z0 = CONT_Z0
    zc = z0 + CONT_H / 2
    y0 = CONT_CY - CONT_L / 2
    y1 = CONT_CY + CONT_L / 2

    box("Piso", (CONT_W, CONT_L, 0.06), (0, CONT_CY, z0 + 0.03), col, MATS["M_Acero"], parent=grupo)

    # techo en su propio grupo (sube en Fase 3)
    techo = empty("GRP_TECHO", col)
    box("Techo", (CONT_W, CONT_L, 0.05), (0, CONT_CY, z0 + CONT_H - 0.025), col, MATS["M_Acero"], parent=techo)
    for side in (-1, 1):
        box("Larguero_Techo_%d" % side, (0.10, CONT_L, 0.10),
            (side * (CONT_W / 2 - 0.05), CONT_CY, z0 + CONT_H - 0.11), col, MATS["M_Acero"], parent=techo)

    # paredes laterales en su propio grupo (se abren en Fase 2)
    for side in (-1, 1):
        pared = empty("GRP_PARED_%s" % ("IZQ" if side < 0 else "DER"), col)
        x = side * (CONT_W / 2 - 0.03)
        box("Pared_%s" % ("Izq" if side < 0 else "Der"), (0.05, CONT_L, CONT_H - 0.10),
            (x, CONT_CY, zc), col, MATS["M_AmbarSuave"], parent=pared)
        ribs = box("Corrugado_%s" % ("Izq" if side < 0 else "Der"),
                   (0.03, 0.05, CONT_H - 0.20),
                   (x + side * 0.035, y0 + 0.14, zc), col, MATS["M_AmbarSuave"], parent=pared)
        mod = ribs.modifiers.new("array", "ARRAY")
        mod.count = int(CONT_L / 0.28)
        mod.use_relative_offset = False
        mod.use_constant_offset = True
        mod.constant_offset_displace = (0.0, 0.28, 0.0)
        box("Riel_Inf_%s" % ("Izq" if side < 0 else "Der"), (0.06, CONT_L, 0.10),
            (x, CONT_CY, z0 + 0.08), col, MATS["M_Acero"], parent=pared)
        box("Riel_Sup_%s" % ("Izq" if side < 0 else "Der"), (0.06, CONT_L, 0.10),
            (x, CONT_CY, z0 + CONT_H - 0.10), col, MATS["M_Acero"], parent=pared)

    # frente (hacia la cabina), se separa en Fase 2
    frontal = empty("GRP_FRONTAL", col)
    box("Frente", (CONT_W, 0.05, CONT_H - 0.10), (0, y1 - 0.03, zc), col, MATS["M_AmbarSuave"], parent=frontal)

    # puertas traseras con bisagra en los extremos
    for side in (-1, 1):
        puerta = empty("GRP_PUERTA_%s" % ("IZQ" if side < 0 else "DER"), col)
        puerta.location = (side * (CONT_W / 2 - 0.05), y0 + 0.05, zc)
        box("Puerta_%s" % ("Izq" if side < 0 else "Der"),
            (CONT_W / 2 - 0.06, 0.07, CONT_H - 0.12),
            (-side * (CONT_W / 4), 0.0, 0.0), col, MATS["M_AmbarSuave"], parent=puerta)
        for z in (-CONT_H / 2 + 0.35, 0.0, CONT_H / 2 - 0.35):
            box("Bisagra_%s_%d" % ("Izq" if side < 0 else "Der", int(z * 10)),
                (0.06, 0.10, 0.10), (0, 0.06, z), col, MATS["M_Ambar"], parent=puerta)
        for z in (-CONT_H / 2 + 0.35, 0.0, CONT_H / 2 - 0.35):
            box("Barra_%s_%d" % ("Izq" if side < 0 else "Der", int(z * 10)),
                (0.04, 0.04, 2.3), (-side * (CONT_W / 2 - 0.35), -0.05, 0),
                col, MATS["M_Ambar"], parent=puerta)
        cylinder("Precinto_%s" % ("Izq" if side < 0 else "Der"), 0.045, 0.16,
                 (0, -0.10, 0.05), col, MATS["M_Cian"], axis="Z", parent=puerta)

    # esquineros ISO
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                box("Esquinero_%d%d%d" % (sx, sy, sz), (0.178, 0.162, 0.118),
                    (sx * (CONT_W / 2 - 0.089), CONT_CY + sy * (CONT_L / 2 - 0.081),
                     z0 + CONT_H / 2 + sz * (CONT_H / 2 - 0.059)),
                    col, MATS["M_Ambar"], bevel=0.012, parent=grupo)

    return grupo, techo


# ---------------------------------------------------------------- carga
def build_cargo():
    col = collection("T03_CARGA")
    grupo = empty("GRP_CARGA", col)
    for i in range(10):
        y = -11.55 + i * 1.26
        for side in (-1, 1):
            x = side * 0.55
            box("Estiba_%02d_%s" % (i, "I" if side < 0 else "D"), (1.00, 1.18, 0.145),
                (x, y, CONT_Z0 + 0.075), col, MATS["M_Acero"], parent=grupo)
            box("Carga_%02d_%s" % (i, "I" if side < 0 else "D"), (0.95, 1.12, 1.55),
                (x, y, CONT_Z0 + 0.145 + 0.775), col, MATS["M_Carga"], parent=grupo)
            if i % 3 == 0:
                box("Sensor_%02d_%s" % (i, "I" if side < 0 else "D"), (0.085, 0.055, 0.03),
                    (x, y - 0.58, CONT_Z0 + 0.32), col, MATS["M_Cian"], parent=grupo)
    return grupo


# ---------------------------------------------------------------- telemetría
def build_telemetry(techo):
    col = collection("T04_TELEMETRIA")
    zt = CONT_Z0 + CONT_H
    box("Nodo_Borde", (0.35, 0.35, 0.14), (-1.0, CONT_CY + 2.2, zt + 0.10), col, MATS["M_Ambar"], parent=techo)
    box("Nodo_Borde_2", (0.35, 0.35, 0.14), (1.0, CONT_CY - 2.2, zt + 0.10), col, MATS["M_Ambar"], parent=techo)
    cylinder("Antena", 0.02, 1.10, (0.95, CONT_CY + 4.4, zt + 0.60), col, MATS["M_Cian"], axis="Z", parent=techo)
    box("Panel_Solar", (1.60, 2.40, 0.03), (-0.30, CONT_CY + 3.4, zt + 0.07), col, MATS["M_Cian"], parent=techo)
    for i in range(4):
        box("Camara_%d" % i, (0.10, 0.16, 0.10),
            (-1.10 + i * 0.73, CONT_CY - CONT_L / 2 + 0.45, zt - 0.22),
            col, MATS["M_Ambar"], parent=techo)
    return collection("T04_TELEMETRIA")


# ---------------------------------------------------------------- cabina
def build_cab():
    col = collection("T05_CABINA")
    grupo = empty("GRP_CABINA", col)
    yc = 1.35
    box("Cabina", (CAB_W, CAB_L, CAB_H - 0.75), (0, yc, 1.05 + (CAB_H - 0.75) / 2),
        col, MATS["M_Acero"], bevel=0.05, parent=grupo)
    box("Deflector", (CAB_W, 1.40, 0.55), (0, yc - 0.15, CAB_H - 0.28),
        col, MATS["M_Acero"], bevel=0.04, parent=grupo)
    box("Parabrisas", (CAB_W - 0.22, 0.05, 0.95), (0, yc + CAB_L / 2 - 0.02, 2.55),
        col, MATS["M_Vidrio"], parent=grupo)
    box("Faldon", (CAB_W - 0.10, CAB_L - 0.10, 0.55), (0, yc, 0.72),
        col, MATS["M_Acero"], parent=grupo)
    box("Parrilla", (1.70, 0.05, 0.38), (0, yc + CAB_L / 2 + 0.02, 1.62),
        col, MATS["M_AmbarSuave"], parent=grupo)
    for side in (-1, 1):
        box("Faro_%d" % side, (0.42, 0.05, 0.16),
            (side * 0.85, yc + CAB_L / 2 + 0.02, 1.36), col, MATS["M_Ambar"], parent=grupo)
        cylinder("Llanta_Cab_%d" % side, 0.54, 0.36, (side * 1.02, yc + 0.35, 0.54),
                 col, MATS["M_Acero"], axis="X", parent=grupo)
        cylinder("Llanta_Cab_Tras_%d" % side, 0.54, 0.36, (side * 1.02, yc - 0.95, 0.54),
                 col, MATS["M_Acero"], axis="X", parent=grupo)
    cylinder("Quinta_Rueda", 0.45, 0.10, (0, 0.05, 0.98), col, MATS["M_AmbarSuave"], axis="Z", parent=grupo)
    cylinder("Chimenea", 0.07, 1.60, (1.20, yc - 0.30, 2.10), col, MATS["M_Acero"], axis="Z", parent=grupo)
    return grupo


# ---------------------------------------------------------------- escena
def build_master():
    col = collection("T99_RIG")
    master = bpy.data.objects.new("MASTER_DESPIECE", None)
    master.empty_display_type = "ARROWS"
    master.empty_display_size = 1.2
    master.location = (-7.2, 3.5, 0.0)
    col.objects.link(master)
    for i in range(5):
        master["p%d" % i] = 0
    master["fase"] = 0
    try:
        master.id_properties_ui("fase").update(min=0, max=4, description="Fase de despiece 0-4")
    except Exception:
        pass
    return master


def build_ground():
    col = collection("T90_ANOTACIONES")
    box("Suelo", (220, 220, 0.02), (0, -6, -0.02), col, MATS["M_Tinta"])
    build_grid(col)


def build_grid(col, extent=30.0, step=1.0, width=0.022):
    """Retícula técnica de 1 m dibujada como malla (líneas de 2 cm)."""
    mat = material("M_Grid", (0.006, 0.006, 0.008), emission=(0.26, 0.19, 0.02), strength=0.10)
    verts = []
    faces = []
    steps = int(extent / step)
    z = 0.004
    for i in range(-steps, steps + 1):
        p = i * step
        base = len(verts)
        verts += [
            (p - width / 2, -extent, z), (p + width / 2, -extent, z),
            (p + width / 2, extent, z), (p - width / 2, extent, z),
            (-extent, p - width / 2, z), (extent, p - width / 2, z),
            (extent, p + width / 2, z), (-extent, p + width / 2, z),
        ]
        faces += [(base, base + 1, base + 2, base + 3),
                  (base + 4, base + 5, base + 6, base + 7)]
    mesh = bpy.data.meshes.new("Grid_Tecnico")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Grid_Tecnico", mesh)
    col.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def build_camera():
    col = collection("T99_RIG")
    target = bpy.data.objects.new("Cam_Target", None)
    target.location = (CAMION_X, -5.6, 3.0)
    col.objects.link(target)

    cam_data = bpy.data.cameras.new("Cam_Isometrica")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 32.0
    cam = bpy.data.objects.new("Cam_Isometrica", cam_data)
    cam.location = (17.5 + CAMION_X, 12.5, 12.0)
    col.objects.link(cam)
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    bpy.context.scene.camera = cam


def build_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.008, 0.013, 0.020, 1.0)
    bg.inputs[1].default_value = 1.0


def build_render_settings():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 24
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except Exception:
            continue
    try:
        scene.eevee.taa_render_samples = 48
    except Exception:
        pass
    if hasattr(scene.render, "use_freestyle"):
        scene.render.use_freestyle = True
        try:
            lineset = scene.view_layers[0].freestyle_settings.linesets[0]
            linestyle = lineset.linestyle
            linestyle.color = (0.96, 0.74, 0.06)
            linestyle.thickness = 1.15
        except Exception:
            pass
    try:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
    except Exception:
        pass


def build_drivers():
    master = bpy.data.objects["MASTER_DESPIECE"]

    def prop(index):
        return ("location", index)

    driver_multi(bpy.data.objects["GRP_TECHO"], prop(2), ["p1", "p3"],
                 "p1 * 1.15 + p3 * 1.45")
    driver(bpy.data.objects["GRP_CARGA"], prop(2), "p1", "p1 * 0.85")
    driver(bpy.data.objects["GRP_PARED_IZQ"], prop(0), "p2", "p2 * -2.05")
    driver(bpy.data.objects["GRP_PARED_DER"], prop(0), "p2", "p2 * 2.05")
    driver(bpy.data.objects["GRP_FRONTAL"], prop(1), "p2", "p2 * 1.30")
    driver(bpy.data.objects["GRP_PUERTA_IZQ"], ("rotation_euler", 2), "p2", "p2 * -2.36")
    driver(bpy.data.objects["GRP_PUERTA_DER"], ("rotation_euler", 2), "p2", "p2 * 2.36")
    driver(bpy.data.objects["GRP_CABINA"], prop(1), "p4", "p4 * 1.20")
    master["p0"] = 1
    master["fase"] = 0


def configure_freestyle():
    """Contornos ámbar en todo el modelo, excepto las piezas menudas.

    Las cotas, los rotulos y la carga palletizada (miles de cajas) van a la
    coleccion filtro T91_SIN_LINEAS: sin ella, un centro de acopio de 44 x 46 m
    se convierte en una masa de lineas y no se lee. almacen.py y annotations.py
    enlazan ahi sus objetos; el objeto sigue viviendo en su coleccion real.
    """
    scene = bpy.context.scene
    if not hasattr(scene.render, "use_freestyle"):
        return
    scene.render.use_freestyle = True
    try:
        col = bpy.data.collections.get(COL_FILTRO)
        if not col:
            col = bpy.data.collections.new(COL_FILTRO)
            bpy.context.scene.collection.children.link(col)
        for obj in list(col.objects):
            col.objects.unlink(obj)
        for obj in bpy.data.collections["T90_ANOTACIONES"].objects:
            col.objects.link(obj)
        lineset = scene.view_layers[0].freestyle_settings.linesets[0]
        lineset.linestyle.color = (0.96, 0.74, 0.06)
        lineset.linestyle.thickness = 1.15
        lineset.select_by_collection = True
        lineset.collection = col
        lineset.collection_negation = "EXCLUSIVE"
    except Exception:
        pass


def build():
    _reset()
    for obj in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(obj, do_unlink=True)
    build_materials()
    build_world()
    build_render_settings()
    build_master()
    build_chassis()
    _, techo = build_container()
    build_cargo()
    build_telemetry(techo)
    build_cab()
    build_ground()
    build_camera()
    build_drivers()
    configure_freestyle()
    bpy.context.view_layer.update()
    total = len(bpy.data.objects)
    print("[CEDI360] escena construida: %d objetos" % total)
    return total


if __name__ == "__main__":
    build()
