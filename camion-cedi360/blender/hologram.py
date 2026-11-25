"""
CEDI 360 - Capa holografica de datos (Fase 3)
=============================================
Construye los paneles de datos que levitan sobre el contenedor cuando la
Fase 3 esta activa. Todo vive en espacio de camara (u,v con v positivo hacia
arriba) para que la composicion no dependa de la proyeccion isometrica:

  - dos paneles de datos (barras de analitica y telemetria BPM),
  - flujos punteados que suben desde el techo hasta los paneles,
  - una nube de nodos con enlaces (red de sensores),
  - rotulos tecnicos.

El grupo GRP_HOLO cuelga de la camara y su visibilidad la gobierna el driver
de la propiedad p3 del MASTER_DESPIECE.

Se ejecuta despues de annotations.py:

    python blender\\client.py exec --file blender\\hologram.py
"""

import bpy
from mathutils import Matrix, Vector

COLLECTION = "T07_HOLOGRAMA"
CAMERA = "Cam_Isometrica"
MASTER = "MASTER_DESPIECE"
DEPTH = 9.5          # mas lejos que los rotulos (8.0) para quedar debajo
OFF_SCREEN = 400.0

C_CYAN = (0.55, 0.74, 1.0)
C_AMBER = (0.98, 0.76, 0.10)
C_PAPER = (0.85, 0.90, 0.96)

T_A = "ANAL\u00cdTICA DE VIDEO"
T_A_SUB = "eventos por hora"
T_B = "TELEMETR\u00cdA T\u00c9RMICA \u00b7 BPM"
T_B1 = "TEMPERATURA  4.2 \u00b0C"
T_B2 = "HUMEDAD REL.   61 %"
T_B3 = "PRECINTOS ACTIVOS  128"
T_NET = "RED DE SENSORES \u00b7 42 NODOS"
T_FLOW = "WMS / TMS \u00b7 8.4K PEDIDOS"


def col():
    for obj in list(bpy.data.collections.get(COLLECTION).objects if bpy.data.collections.get(COLLECTION) else []):
        bpy.data.objects.remove(obj, do_unlink=True)
    coleccion = bpy.data.collections.get(COLLECTION)
    if not coleccion:
        coleccion = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(coleccion)
    return coleccion


def mat(name, rgb, strength, alpha=1.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, alpha)
    bsdf.inputs["Roughness"].default_value = 0.45
    try:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    except KeyError:
        pass
    if alpha < 1.0:
        m.blend_method = "BLEND"
        m.use_backface_culling = False
    return m


def screen():
    scene = bpy.context.scene
    cam = bpy.data.objects[CAMERA]
    w = cam.data.ortho_scale
    h = w * scene.render.resolution_y / scene.render.resolution_x
    return w, h


def local(u, v, depth=DEPTH):
    w, h = screen()
    return Vector((u * w / 2, v * h / 2, -depth))


def quad(name, w_m, h_m, u, v, material, coleccion, parent):
    sx = w_m
    sy = h_m
    mesh = bpy.data.meshes.new(name)
    verts = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = local(u, v) - Vector((0, 0, 0.002))
    coleccion.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def box(name, w_m, h_m, u, v, material, coleccion, parent):
    mesh = bpy.data.meshes.new(name)
    sx, sy, sz = w_m, h_m, 0.01
    verts = [
        (-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
        (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
        (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
        (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = local(u, v)
    coleccion.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def line(name, a_uv, b_uv, thickness, material, coleccion, parent):
    """Segmento entre dos puntos de pantalla."""
    a = local(a_uv[0], a_uv[1])
    b = local(b_uv[0], b_uv[1])
    d = b - a
    if d.length < 1e-5:
        return None
    mesh = bpy.data.meshes.new(name)
    sx, sy, sz = thickness, thickness, d.length
    verts = [
        (-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
        (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
        (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
        (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (a + b) / 2
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    coleccion.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def dot(name, u, v, radius, material, coleccion, parent):
    mesh = bpy.data.meshes.new(name)
    verts, faces = [], []
    steps = 12
    import math
    for i in range(steps):
        ang = 2 * math.pi * i / steps
        verts.append((radius * math.cos(ang), radius * math.sin(ang), 0))
    faces.append(tuple(range(steps)))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = local(u, v)
    coleccion.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


def text(name, body, u, v, size, material, coleccion, parent, align="LEFT"):
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    obj.location = local(u, v, DEPTH - 0.05)
    coleccion.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.data.materials.append(material)
    return obj


# ---------------------------------------------------------------- paneles
def panel_bars(coleccion, parent, line_mat, fill_mat, amber, txt):
    u0, v0 = -0.46, 0.62
    w, h = 3.55, 2.05
    x0, y0 = u0 * screen()[0] / 2, v0 * screen()[1] / 2

    box("HOLO_Tele_Caja", w, h, u0, v0, fill_mat, coleccion, parent)
    # marco
    for name, bw, bh, du, dv in (
        ("HOLO_Tele_Sup", w, 0.014, 0, h / 2),
        ("HOLO_Tele_Inf", w, 0.014, 0, -h / 2),
        ("HOLO_Tele_Izq", 0.014, h, -w / 2, 0),
        ("HOLO_Tele_Der", 0.014, h, w / 2, 0),
    ):
        box(name, bw, bh, x0 / (screen()[0] / 2) + du / (screen()[0] / 2),
            y0 / (screen()[1] / 2) + dv / (screen()[1] / 2), line_mat, coleccion, parent)

    text("HOLO_Tele_Txt", T_A, (x0 - w / 2 + 0.14) / (screen()[0] / 2),
         (y0 + h / 2 - 0.22) / (screen()[1] / 2), 0.155, txt, coleccion, parent)
    text("HOLO_Tele_Sub", T_A_SUB, (x0 - w / 2 + 0.14) / (screen()[0] / 2),
         (y0 + h / 2 - 0.44) / (screen()[1] / 2), 0.10, line_mat, coleccion, parent)

    valores = [0.42, 0.66, 0.52, 0.86, 0.58, 0.74, 0.46, 0.68, 0.92, 0.55]
    ancho = (w - 0.4) / len(valores)
    base_y = -h / 2 + 0.32
    for i, valor in enumerate(valores):
        bx = -w / 2 + 0.20 + ancho * (i + 0.5)
        altura = valor * (h - 0.95)
        box("HOLO_Barra_%02d" % i, ancho * 0.55, altura,
            x0 / (screen()[0] / 2) + bx / (screen()[0] / 2),
            y0 / (screen()[1] / 2) + (base_y + altura / 2) / (screen()[1] / 2),
            amber if i in (3, 8) else line_mat, coleccion, parent)
    box("HOLO_Base", w - 0.4, 0.014, u0,
        y0 / (screen()[1] / 2) + base_y / (screen()[1] / 2), line_mat, coleccion, parent)


def panel_telemetry(coleccion, parent, line_mat, fill_mat, amber, txt):
    u0, v0 = 0.46, 0.64
    w, h = 3.55, 2.05
    x0, y0 = u0 * screen()[0] / 2, v0 * screen()[1] / 2

    box("HOLO_Bpm_Caja", w, h, u0, v0, fill_mat, coleccion, parent)
    for name, bw, bh, du, dv in (
        ("HOLO_Bpm_Sup", w, 0.014, 0, h / 2),
        ("HOLO_Bpm_Inf", w, 0.014, 0, -h / 2),
        ("HOLO_Bpm_Izq", 0.014, h, -w / 2, 0),
        ("HOLO_Bpm_Der", 0.014, h, w / 2, 0),
    ):
        box(name, bw, bh, x0 / (screen()[0] / 2) + du / (screen()[0] / 2),
            y0 / (screen()[1] / 2) + dv / (screen()[1] / 2), line_mat, coleccion, parent)

    text("HOLO_Bpm_Txt", T_B, (x0 - w / 2 + 0.14) / (screen()[0] / 2),
         (y0 + h / 2 - 0.22) / (screen()[1] / 2), 0.14, txt, coleccion, parent)
    for i, cuerpo in enumerate((T_B1, T_B2, T_B3)):
        text("HOLO_Bpm_L%d" % i, cuerpo, (x0 - w / 2 + 0.14) / (screen()[0] / 2),
             (y0 + h / 2 - 0.55 - i * 0.26) / (screen()[1] / 2), 0.115, line_mat,
             coleccion, parent)

    # linea de tendencia
    puntos = [0.05, 0.18, 0.12, 0.28, 0.22, 0.36, 0.30, 0.44, 0.38, 0.52, 0.46, 0.60]
    ancho = w - 0.36
    prev = None
    for i, valor in enumerate(puntos):
        px = (x0 - w / 2 + 0.18 + ancho * i / (len(puntos) - 1)) / (screen()[0] / 2)
        py = (y0 - h / 2 + 0.24 + valor) / (screen()[1] / 2)
        dot("HOLO_Pto_%02d" % i, px, py, 0.035, amber if i == len(puntos) - 1 else line_mat,
            coleccion, parent)
        if prev:
            line("HOLO_Tend_%02d" % i, prev, (px, py), 0.012, line_mat, coleccion, parent)
        prev = (px, py)


def uplinks(coleccion, parent, line_mat):
    """Flujos punteados desde el techo del contenedor hasta los paneles."""
    from bpy_extras.object_utils import world_to_camera_view as wv

    cam = bpy.data.objects[CAMERA]
    escena = bpy.context.scene
    anclas = [(-1.219, -11.8, 6.85), (1.219, -11.8, 6.85),
              (-1.219, -7.0, 6.85), (1.219, -7.0, 6.85), (0.0, -3.0, 6.85)]
    idx = 0
    for punto in anclas:
        v = wv(escena, cam, Vector(punto))
        u = v.x * 2 - 1
        vv = v.y * 2 - 1
        destino = 0.505 if u < 0 else 0.525
        pasos = 7
        for s in range(pasos):
            t0 = s / pasos
            t1 = t0 + 0.055
            a = (u, vv + (destino - vv) * t0)
            b = (u, vv + (destino - vv) * t1)
            line("HOLO_Flujo_%02d_%02d" % (idx, s), a, b, 0.010, line_mat, coleccion, parent)
        dot("HOLO_Nodo_%02d" % idx, u, vv, 0.045, line_mat, coleccion, parent)
        idx += 1


def network(coleccion, parent, line_mat, amber, txt):
    """Constelacion de sensores debajo del panel de telemetria."""
    nodos = [(0.24, 0.475), (0.295, 0.492), (0.35, 0.474), (0.405, 0.494), (0.46, 0.476)]
    enlaces = [(0, 1), (1, 2), (2, 3), (3, 4), (1, 3)]
    for i, (a, b) in enumerate(enlaces):
        line("HOLO_Red_%02d" % i, nodos[a], nodos[b], 0.008, line_mat, coleccion, parent)
    for i, (u, v) in enumerate(nodos):
        dot("HOLO_RedN_%02d" % i, u, v, 0.042, amber if i == 1 else line_mat, coleccion, parent)
    text("HOLO_Red_Txt", T_NET, 0.26, 0.555, 0.095, txt, coleccion, parent)


def flow_label(coleccion, parent, line_mat, txt):
    text("HOLO_Flow_Txt", T_FLOW, -0.46, 0.47, 0.11, txt, coleccion, parent, align="CENTER")


# ---------------------------------------------------------------- build
def build():
    coleccion = col()
    cam = bpy.data.objects[CAMERA]

    grupo = bpy.data.objects.get("GRP_HOLO")
    if grupo:
        bpy.data.objects.remove(grupo, do_unlink=True)
    grupo = bpy.data.objects.new("GRP_HOLO", None)
    grupo.empty_display_size = 0.2
    coleccion.objects.link(grupo)
    grupo.parent = cam
    grupo.matrix_parent_inverse = Matrix.Identity(4)
    grupo.location = (0, 0, 0)

    fc = grupo.driver_add("location", 0)
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "p3"
    var.type = "SINGLE_PROP"
    var.targets[0].id = bpy.data.objects[MASTER]
    var.targets[0].data_path = '["p3"]'
    drv.expression = "-%.1f * (1 - p3)" % OFF_SCREEN

    line_mat = mat("M_HoloLinea", C_CYAN, 1.8)
    amber = mat("M_HoloAmbar", C_AMBER, 2.4)
    txt = mat("M_HoloTexto", C_PAPER, 1.5)
    fill = mat("M_HoloPanel", (0.02, 0.06, 0.10), 0.25, alpha=0.55)

    panel_bars(coleccion, grupo, line_mat, fill, amber, txt)
    panel_telemetry(coleccion, grupo, line_mat, fill, amber, txt)
    uplinks(coleccion, grupo, line_mat)
    network(coleccion, grupo, line_mat, amber, txt)
    flow_label(coleccion, grupo, line_mat, txt)

    bpy.context.view_layer.update()
    print("[CEDI360] holograma listo: %d objetos" % len(coleccion.objects))


if __name__ == "__main__":
    build()
