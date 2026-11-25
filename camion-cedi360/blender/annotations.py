"""
CEDI 360 - Cotas, rotulos y marco de plano
==========================================
Capa de anotacion tecnica sobre el modelo ya construido:

  - Marco de plano y bloque de titulo (hijos de la camara).
  - Cotas con lineas de extension y flechas (largo, ancho, alto, piso, tandem).
  - Lineas de proyeccion punteadas entre capas (aparecen desde la Fase 2).
  - Rotulos de piezas con linea guia, posicionados por coordenadas de pantalla
    para que la composicion no dependa de la proyeccion isometrica.
  - Rotulo de fase en la esquina, gobernado por drivers.

Idempotente. Se ejecuta despues de build_scene.py:

    python blender\\client.py exec --file blender\\annotations.py

Las posiciones usan u,v en [-1,1] (v positivo hacia arriba) sobre la vista
ortografica. El encuadre se calcula con ortho_scale y la proporcion del
render: mantener proporcion 16:9.
"""

import bpy
import bmesh
from mathutils import Vector, Matrix

COLLECTION = "T90_ANOTACIONES"
CAMERA = "Cam_Isometrica"
MASTER = "MASTER_DESPIECE"

CONT_L = 12.192
CONT_W = 2.438
CONT_H = 2.896
# -6,30 es la posicion original del camion; ubicar_camion.py lo corre 2,90 m
# al sur y las cotas viven en espacio de camara, asi que se desplazan aqui
CONT_CY = -9.20
# CAMION_X es el corrimiento al este de ubicar_camion.py: la camara del plano
# lo sigue (build_scene.py) y las piezas en espacio de mundo cuelgan de
# GRP_ANOTACIONES en ese mismo x, asi la lamina sale igual que siempre
CAMION_X = 8.00
CONT_Z0 = 1.30
DECK_Z = 1.30
y_rear = CONT_CY - CONT_L / 2
y_front = CONT_CY + CONT_L / 2
z_top = CONT_Z0 + CONT_H
AXLE_Y = (-12.45, -13.76)

DIST = 8.0
OFF_SCREEN = 90.0

C_AMBER = (0.98, 0.76, 0.10)
C_AMBER_DIM = (0.62, 0.46, 0.06)
C_CYAN = (0.55, 0.74, 1.0)
C_PAPER = (0.80, 0.85, 0.90)

T_CONT = "CONTENEDOR ISO 40' HC"
T_CCTV = "CCTV IP \u00b7 ANAL\u00cdTICA DE VIDEO"
T_CHASIS = "CHASIS 3 EJES \u00b7 T\u00c1NDEM"
T_UPS = "UPS DE RESPALDO"
T_CABINA = "CABINA TRACTORA"
T_FIBRA = "FIBRA \u00d3PTICA \u00b7 ENLACE REDUNDANTE"
T_TERMICO = "SENSORES T\u00c9RMICOS BPM / INVIMA"
T_ESTIBA = "20 ESTIBAS \u00b7 CARGA PALETIZADA"
T_LARGO = "12.192 m  \u00b7  " + T_CONT
T_TIT = "CEDI 360 \u00b7 DESPIECE ISOM\u00c9TRICO"
T_SUB = "ESCALA 1:1 \u00b7 CONTENEDOR 40' HC \u00b7 CHASIS 3 EJES"
FASES = {
    0: "ESTADO 0 \u00b7 EN TR\u00c1NSITO",
    1: "FASE 1 \u00b7 ESTABILIZACI\u00d3N",
    2: "FASE 2 \u00b7 MODERNIZACI\u00d3N",
    3: "FASE 3 \u00b7 INTELIGENCIA",
    4: "FASE 4 \u00b7 ACOMPA\u00d1AMIENTO",
}


# ------------------------------------------------------------------ utileria
def col():
    return bpy.data.collections[COLLECTION]


def clean(prefixes):
    for obj in list(col().objects):
        if any(obj.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def emissive(name, rgb, strength, alpha=1.0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, alpha)
    bsdf.inputs["Roughness"].default_value = 0.4
    try:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    except KeyError:
        pass
    if alpha < 1.0:
        mat.blend_method = "BLEND"
    return mat


def _mesh_box(name, size):
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
    return mesh


def segment(name, a, b, thickness, mat, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    if d.length < 1e-6:
        return None
    obj = bpy.data.objects.new(name, _mesh_box(name, (thickness, thickness, d.length)))
    obj.location = (a + b) / 2
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    col().objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(mat)
    return obj


def arrow(name, tip, direction, mat, size=0.20, radius=0.055, parent=None):
    d = Vector(direction).normalized()
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=14,
                              radius1=radius, radius2=0.0, depth=size)
    except TypeError:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=14,
                              diameter1=radius * 2, diameter2=0.0, depth=size)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    obj.location = Vector(tip) - d * (size / 2)
    col().objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(mat)
    return obj


def dashed(name, a, b, mat, thickness=0.014, dash=0.14, gap=0.10, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    total = d.length
    if total < 1e-6:
        return []
    unit = d.normalized()
    made, t, i = [], 0.0, 0
    while t < total:
        end = min(t + dash, total)
        made.append(segment("%s_%02d" % (name, i), a + unit * t, a + unit * end,
                            thickness, mat, parent))
        t = end + gap
        i += 1
    return [m for m in made if m]


# ------------------------------------------------------- helpers de pantalla
def screen_size():
    scene = bpy.context.scene
    cam = bpy.data.objects[CAMERA]
    w = cam.data.ortho_scale
    h = w * scene.render.resolution_y / scene.render.resolution_x
    return w, h


def to_local(u, v):
    w, h = screen_size()
    return Vector((u * w / 2, v * h / 2, -DIST))


def to_world(u, v):
    return bpy.data.objects[CAMERA].matrix_world @ to_local(u, v)


def screen_label(name, body, u, v, size, mat, align="LEFT"):
    cam = bpy.data.objects[CAMERA]
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    obj.parent = cam
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = to_local(u, v)
    col().objects.link(obj)
    obj.data.materials.append(mat)
    return obj


# ------------------------------------------------------------------ drivers
def drive_off(obj, prop, axis=2, base=0.0, off=OFF_SCREEN):
    fc = obj.driver_add("location", axis)
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = prop
    var.type = "SINGLE_PROP"
    var.targets[0].id = bpy.data.objects[MASTER]
    var.targets[0].data_path = '["%s"]' % prop
    drv.expression = "%.4f - %.1f * (1 - %s)" % (base, off, prop)
    return drv


def drive_only(obj, prop_on, props_off, axis=0, base=0.0, off=OFF_SCREEN * 14):
    """Visible solo cuando prop_on=1 y todas las props_off=0."""
    fc = obj.driver_add("location", axis)
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = prop_on
    var.type = "SINGLE_PROP"
    var.targets[0].id = bpy.data.objects[MASTER]
    var.targets[0].data_path = '["%s"]' % prop_on
    suma = ["1 - %s" % prop_on]
    for nombre in props_off:
        v2 = drv.variables.new()
        v2.name = nombre
        v2.type = "SINGLE_PROP"
        v2.targets[0].id = bpy.data.objects[MASTER]
        v2.targets[0].data_path = '["%s"]' % nombre
        suma.append(nombre)
    drv.expression = "%.4f - %.1f * (%s)" % (base, off, " + ".join(suma))
    return drv


def drive_hide_if_any(obj, props, axis=0, base=0.0, off=OFF_SCREEN * 14):
    fc = obj.driver_add("location", axis)
    drv = fc.driver
    drv.type = "SCRIPTED"
    for name in props:
        var = drv.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        var.targets[0].id = bpy.data.objects[MASTER]
        var.targets[0].data_path = '["%s"]' % name
    drv.expression = "%.4f - %.1f * (%s)" % (base, off, " + ".join(props))
    return drv


# ------------------------------------------------------------------ cotas
def dim_length(mat_line, mat_text):
    x = -CONT_W / 2 - 0.42
    z = z_top + 0.85
    a, b = (x, y_rear, z), (x, y_front, z)
    segment("COTA_Largo_linea", a, b, 0.018, mat_line)
    arrow("COTA_Largo_flecha_1", a, (0, -1, 0), mat_line)
    arrow("COTA_Largo_flecha_2", b, (0, 1, 0), mat_line)
    for idx, y in enumerate((y_rear, y_front)):
        segment("COTA_Largo_ext_%d" % idx, (x + 0.05, y, z_top + 0.10),
                (x + 0.05, y, z + 0.06), 0.012, mat_line)
        segment("COTA_Largo_ref_%d" % idx, (-CONT_W / 2, y, z_top + 0.04),
                (x + 0.10, y, z_top + 0.04), 0.010, mat_line)
    screen_label("COTA_Largo_texto", T_LARGO, 0.30, 0.90, 0.36, mat_text, align="CENTER")


def dim_width(mat_line, mat_text):
    y = y_rear - 0.85
    z = z_top + 0.16
    a, b = (-CONT_W / 2, y, z), (CONT_W / 2, y, z)
    segment("COTA_Ancho_linea", a, b, 0.018, mat_line)
    arrow("COTA_Ancho_flecha_1", a, (-1, 0, 0), mat_line)
    arrow("COTA_Ancho_flecha_2", b, (1, 0, 0), mat_line)
    for idx, x in enumerate((-CONT_W / 2, CONT_W / 2)):
        segment("COTA_Ancho_ext_%d" % idx, (x, y_rear, z_top + 0.02),
                (x, y - 0.08, z + 0.06), 0.012, mat_line)
    screen_label("COTA_Ancho_texto", "2.438 m", -0.52, 0.93, 0.28, mat_text, align="CENTER")


def dim_height(mat_line, mat_text):
    x = CONT_W / 2 + 0.22
    y = y_rear - 0.55
    a, b = (x, y, CONT_Z0), (x, y, z_top)
    segment("COTA_Alto_linea", a, b, 0.018, mat_line)
    arrow("COTA_Alto_flecha_1", a, (0, 0, -1), mat_line)
    arrow("COTA_Alto_flecha_2", b, (0, 0, 1), mat_line)
    for idx, z in enumerate((CONT_Z0, z_top)):
        segment("COTA_Alto_ext_%d" % idx, (CONT_W / 2, y_rear, z),
                (x + 0.10, y, z), 0.012, mat_line)
    screen_label("COTA_Alto_texto", "2.896 m", -0.62, 0.16, 0.30, mat_text, align="RIGHT")


def dim_deck(mat_line, mat_text):
    x = CONT_W / 2 + 0.22
    y = y_rear - 0.55
    a, b = (x, y, 0.02), (x, y, DECK_Z)
    segment("COTA_Piso_linea", a, b, 0.016, mat_line)
    arrow("COTA_Piso_flecha_1", a, (0, 0, -1), mat_line, size=0.16)
    arrow("COTA_Piso_flecha_2", b, (0, 0, 1), mat_line, size=0.16)
    for idx, z in enumerate((0.02, DECK_Z)):
        segment("COTA_Piso_ext_%d" % idx, (CONT_W / 2, y_rear, z),
                (x + 0.10, y, z), 0.010, mat_line)
    screen_label("COTA_Piso_texto", "1.30 m", -0.62, -0.08, 0.26, mat_text, align="RIGHT")


def dim_tandem(mat_line, mat_text):
    x = 1.85
    z = 0.34
    a, b = (x, AXLE_Y[0], z), (x, AXLE_Y[1], z)
    segment("COTA_Tandem_linea", a, b, 0.014, mat_line)
    arrow("COTA_Tandem_flecha_1", a, (0, -1, 0), mat_line, size=0.15)
    arrow("COTA_Tandem_flecha_2", b, (0, 1, 0), mat_line, size=0.15)
    for idx, y in enumerate(AXLE_Y):
        segment("COTA_Tandem_ext_%d" % idx, (1.16, y, 0.14), (x + 0.04, y, z + 0.03),
                0.010, mat_line)
    screen_label("COTA_Tandem_texto", "1.310 m", -0.54, -0.28, 0.24, mat_text, align="LEFT")


# ------------------------------------------------------------------ guias
def projections(mat):
    grupo = bpy.data.objects.get("GRP_GUIAS")
    if not grupo:
        grupo = bpy.data.objects.new("GRP_GUIAS", None)
        grupo.empty_display_size = 0.4
        col().objects.link(grupo)
        drive_off(grupo, "p2")
    for i, (x, y) in enumerate(((-CONT_W / 2, y_rear), (CONT_W / 2, y_rear),
                                (-CONT_W / 2, y_front), (CONT_W / 2, y_front))):
        dashed("GUIA_V_%d" % i, (x, y, CONT_Z0 + 0.05), (x, y, z_top + 3.4),
               mat, thickness=0.010, dash=0.16, gap=0.13, parent=grupo)
    for i, (x0, x1) in enumerate(((-CONT_W / 2 - 0.1, -CONT_W / 2 - 1.6),
                                  (CONT_W / 2 + 0.1, CONT_W / 2 + 1.6))):
        dashed("GUIA_H_%d" % i, (x0, CONT_CY, CONT_Z0 + CONT_H / 2),
               (x1, CONT_CY, CONT_Z0 + CONT_H / 2), mat, thickness=0.010,
               dash=0.16, gap=0.13, parent=grupo)
    return grupo


# ------------------------------------------------------------------ rotulos
def leader(nombre, texto, punto, u, v, size, mat_line, mat_text,
           parent=None, align="LEFT", drive=None):
    a = Vector(punto)
    tip = to_world(u, v)
    if align == "RIGHT":
        tip = tip - bpy.data.objects[CAMERA].matrix_world.to_3x3() @ Vector((0.35, 0, 0))
    direction = tip - a
    gap = 0.25
    end = tip - direction.normalized() * gap if direction.length > gap else tip
    segment("GUI_%s" % nombre, a, end, 0.010, mat_line, parent)
    obj = bpy.data.objects.new("DOT_%s" % nombre, None)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.05
    obj.location = a
    col().objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
    text_obj = screen_label("TXT_%s" % nombre, texto, u, v, size, mat_text, align=align)
    if drive:
        drive_off(text_obj, drive, axis=0, base=text_obj.location.x)
    return obj


def labels_ext(mat_line, mat_text):
    leader("CCTV", T_CCTV, (-0.37, y_rear + 0.45, z_top - 0.22),
           -0.87, 0.28, 0.25, mat_line, mat_text)
    leader("Chasis", T_CHASIS, (0.90, AXLE_Y[1], 1.05),
           -0.64, -0.68, 0.25, mat_line, mat_text)
    leader("UPS", T_UPS, (0.72, -4.10, 0.95),
           -0.16, -0.82, 0.23, mat_line, mat_text)
    leader("Cabina", T_CABINA, (1.10, 1.35, 2.20),
           0.60, -0.54, 0.25, mat_line, mat_text)
    leader("Fibra", T_FIBRA, (0.95, -1.70, DECK_Z - 0.20),
           0.60, -0.80, 0.23, mat_line, mat_text)


def labels_int(mat_line, mat_text):
    grupo = bpy.data.objects.get("GRP_ETIQUETAS_INT")
    if not grupo:
        grupo = bpy.data.objects.new("GRP_ETIQUETAS_INT", None)
        grupo.empty_display_size = 0.3
        col().objects.link(grupo)
        drive_off(grupo, "p2")
    leader("Termico", T_TERMICO, (0.55, -11.55, CONT_Z0 + 0.35),
           -0.87, 0.04, 0.24, mat_line, mat_text, parent=grupo, drive="p2")
    leader("Estiba", T_ESTIBA, (-0.55, -6.6, CONT_Z0 + 1.7),
           -0.06, 0.30, 0.24, mat_line, mat_text, parent=grupo, drive="p2")
    return grupo


# ------------------------------------------------------------------ marco
def frame_box(name, size, loc, mat_line, cam, dist=DIST):
    obj = bpy.data.objects.new(name, _mesh_box(name, size))
    obj.parent = cam
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = (loc[0], loc[1], -dist)
    col().objects.link(obj)
    obj.data.materials.append(mat_line)
    return obj


def plan_frame(mat_line, mat_text):
    cam = bpy.data.objects.get(CAMERA)
    if not cam:
        return
    w, h = screen_size()
    fw, fh = w * 0.96, h * 0.94
    t = 0.012
    frame_box("MARCO_Sup", (fw, t, t), (0, fh / 2, 0), mat_line, cam)
    frame_box("MARCO_Inf", (fw, t, t), (0, -fh / 2, 0), mat_line, cam)
    frame_box("MARCO_Izq", (t, fh, t), (-fw / 2, 0, 0), mat_line, cam)
    frame_box("MARCO_Der", (t, fh, t), (fw / 2, 0, 0), mat_line, cam)

    tick = 0.26
    for sx in (-1, 1):
        for sy in (-1, 1):
            frame_box("MARCO_TicX_%d_%d" % (sx, sy), (tick * 2, t, t),
                      (sx * (fw / 2 - tick), sy * fh / 2, 0), mat_line, cam)
            frame_box("MARCO_TicY_%d_%d" % (sx, sy), (t, tick * 2, t),
                      (sx * fw / 2, sy * (fh / 2 - tick), 0), mat_line, cam)

    bw, bh = 3.55, 0.62
    bx = -fw / 2 + 0.24 + bw / 2
    by = -fh / 2 + 0.22 + bh / 2
    frame_box("TIT_Caja_Sup", (bw, t, t), (bx, by + bh / 2, 0), mat_line, cam)
    frame_box("TIT_Caja_Izq", (t, bh, t), (bx - bw / 2, by, 0), mat_line, cam)
    frame_box("TIT_Caja_Der", (t, bh, t), (bx + bw / 2, by, 0), mat_line, cam)
    frame_box("TIT_Caja_Inf", (bw, t, t), (bx, by - bh / 2, 0), mat_line, cam)
    frame_box("TIT_Div", (bw, t * 0.8, t), (bx, by - 0.02, 0), mat_line, cam)

    screen_label("TIT_Texto", T_TIT, (bx - bw / 2 + 0.10) / (w / 2),
                 (by + 0.13) / (h / 2), 0.20, mat_text, align="LEFT")
    screen_label("TIT_Sub", T_SUB, (bx - bw / 2 + 0.10) / (w / 2),
                 (by - 0.15) / (h / 2), 0.13, mat_text, align="LEFT")


def phase_badges(mat_text):
    cam = bpy.data.objects.get(CAMERA)
    if not cam:
        return
    w, h = screen_size()
    u = -(w * 0.94 / 2 - 0.34) / (w / 2)
    v = (h * 0.92 / 2 - 0.30) / (h / 2)
    ambar = emissive("M_CotaAmbar", C_AMBER, 2.0)
    for fase, body in FASES.items():
        obj = screen_label("FASE_TXT_%d" % fase, body, u, v, 0.19,
                           ambar if fase else mat_text, align="LEFT")
        posteriores = ["p%d" % i for i in range(fase + 1, 5)]
        drive_only(obj, "p%d" % fase, posteriores, axis=0, base=obj.location.x)


# ------------------------------------------------------------------ build
def anclar(dx):
    """Cuelga lo que vive en espacio de mundo de un grupo corrido en x.

    El marco y los textos van colgados de la camara, asi que ya acompanan el
    corrimiento de build_scene.py; las cotas, guias y el suelo no, y sin este
    ancla el plano quedaria con las medidas a 8 m del camion. Se usa el mismo
    truco de ubicar_camion.py: sin inversa, el hijo hereda el desplazamiento.
    """
    ancla = bpy.data.objects.get("GRP_ANOTACIONES")
    if ancla is None:
        ancla = bpy.data.objects.new("GRP_ANOTACIONES", None)
        ancla.empty_display_type = "PLAIN_AXES"
        ancla.empty_display_size = 1.0
        col().objects.link(ancla)
    ancla.parent = None
    ancla.location = (dx, 0.0, 0.0)
    cam = bpy.data.objects.get(CAMERA)
    for obj in list(col().objects):
        if obj is ancla or obj.parent is not None:
            continue
        obj.parent = ancla
        obj.matrix_parent_inverse.identity()


def build():
    clean(("COTA_", "GUIA_", "GUI_", "TXT_", "DOT_", "MARCO_", "TIT_", "FASE_TXT_"))
    for nombre in ("GRP_GUIAS", "GRP_ETIQUETAS_INT"):
        obj = bpy.data.objects.get(nombre)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    mat_line = emissive("M_CotaLinea", C_AMBER, 1.6)
    mat_text = emissive("M_Texto", C_PAPER, 1.4)
    mat_cyan = emissive("M_TextoCian", C_CYAN, 1.6)

    dim_length(mat_line, mat_text)
    dim_width(mat_line, mat_text)
    dim_height(mat_line, mat_text)
    dim_deck(mat_line, mat_text)
    dim_tandem(mat_line, mat_text)
    projections(emissive("M_CotaPunteada", C_AMBER_DIM, 0.9))
    labels_ext(mat_line, mat_text)
    labels_int(mat_line, mat_cyan)
    plan_frame(mat_line, mat_text)
    phase_badges(mat_text)
    anclar(CAMION_X)
    bpy.context.view_layer.update()

    # las cotas no llevan entintado: se enlazan al filtro de Freestyle
    filtro = bpy.data.collections.get("T91_SIN_LINEAS")
    if filtro:
        for obj in col().objects:
            if filtro not in obj.users_collection:
                filtro.objects.link(obj)

    print("[CEDI360] anotaciones listas: %d objetos en %s" % (len(col().objects), COLLECTION))


if __name__ == "__main__":
    build()
