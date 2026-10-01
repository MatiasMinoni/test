"""Fotos de producto 3D fotorrealistas de la marca de ejemplo "cítrica" (Blender / Cycles).

    python render_products.py [--preview] [toma ...]

Requiere el módulo bpy de Blender 4.2 (pip install bpy==4.2.0, Python 3.11) y las etiquetas
exportadas por make_labels.mjs. Las imágenes salen en assets/products/.
Tomas: hero_orange, hero_cream, family, flatlay
"""
import math
import os
import sys

import bpy  # bmesh y mathutils solo existen después de importar bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, 'products', 'tex')
OUT = os.path.join(ROOT, 'assets', 'products')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
PREVIEW = '--preview' in sys.argv


def srgb(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*[x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c], a)


# ------------------------------------------------------------------ escena
def reset(res, samples=192):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 24 if PREVIEW else samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = .01
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 24
    s.cycles.transmission_bounces = 24
    s.cycles.transparent_max_bounces = 24
    s.cycles.glossy_bounces = 8
    s.cycles.diffuse_bounces = 4
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 30 if PREVIEW else 80
    s.render.image_settings.file_format = 'JPEG'
    s.render.image_settings.quality = 93
    # Khronos PBR Neutral respeta el tono y la saturación de los materiales (ideal para producto)
    s.view_settings.view_transform = 'Khronos PBR Neutral'
    s.view_settings.exposure = -.35
    w = bpy.data.worlds.new('world')
    s.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.92, 0.9, 0.88, 1)
    bg.inputs[1].default_value = .22
    return s


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def mesh_obj(name, verts, faces, uvs=None, smooth=True, sharp=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    if uvs is not None:
        layer = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices):
                layer.data[li].uv = uvs[vi]
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if sharp:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    return link(bpy.data.objects.new(name, me))


def revolve(name, prof, seg=128, sharp=40):
    n = len(prof)
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for r, z in prof:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(seg):
        i2 = (i + 1) % seg
        for j in range(n - 1):
            faces.append((i * n + j, i2 * n + j, i2 * n + j + 1, i * n + j + 1))
    return mesh_obj(name, verts, faces, sharp=sharp)


def band(name, r, z0, z1, span, center=-90, seg=160):
    verts, faces, uvs = [], [], []
    for i in range(seg + 1):
        u = i / seg
        a = math.radians(center - span / 2 + span * u)
        verts += [(r * math.cos(a), r * math.sin(a), z0), (r * math.cos(a), r * math.sin(a), z1)]
        uvs += [(u, 0), (u, 1)]
    for i in range(seg):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    return mesh_obj(name, verts, faces, uvs)


def disk(name, r, z=0, seg=128, up=True):
    verts = [(0, 0, z)] + [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z) for i in range(seg)]
    faces = [(0, i + 1, (i + 1) % seg + 1) if up else (0, (i + 1) % seg + 1, i + 1) for i in range(seg)]
    uvs = [(v[0] / r * .5 + .5, v[1] / r * .5 + .5) for v in verts]
    return mesh_obj(name, verts, faces, uvs)


def rounded(r, h, b=.18, z0=0.0, steps=5):
    """Perfil de un cilindro con cantos redondeados."""
    p = [(0, z0)]
    for k in range(steps + 1):
        a = -math.pi / 2 + (math.pi / 2) * k / steps
        p.append((r - b + b * math.cos(a), z0 + b + b * math.sin(a)))
    for k in range(steps + 1):
        a = (math.pi / 2) * k / steps
        p.append((r - b + b * math.cos(a), z0 + h - b + b * math.sin(a)))
    p.append((0, z0 + h))
    return p


def parent(objs, name):
    e = link(bpy.data.objects.new(name, None))
    for o in objs:
        o.parent = e
    return e


# ------------------------------------------------------------------ materiales
def principled(name, color=(.8, .8, .8, 1), rough=.5, metal=0., trans=0., ior=1.45, sss=0., sss_scale=.2, coat=0.):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans
    b.inputs['IOR'].default_value = ior
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Scale'].default_value = sss_scale
    b.inputs['Coat Weight'].default_value = coat
    return m


def tex_material(name, path, rough=.55, sss=0., coat=0.):
    m = principled(name, rough=rough, sss=sss, coat=coat)
    nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path) if isinstance(path, str) else path
    t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m


def add_bump(m, scale=120, strength=.25):
    nt = m.node_tree
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 6
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
    return m


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return obj


MAT = {}


def materials():
    MAT['amber'] = principled('vidrio ámbar', (0.95, 0.52, 0.2, 1), rough=.02, trans=1, ior=1.5)
    MAT['clear'] = principled('vidrio', (0.97, 0.97, 0.96, 1), rough=.02, trans=1, ior=1.5)
    MAT['serum'] = principled('sérum', (1.0, 0.42, 0.04, 1), rough=.04, trans=1, ior=1.36)
    MAT['gold'] = principled('dorado', (0.92, 0.68, 0.38, 1), rough=.2, metal=1)
    MAT['rubber'] = principled('goma', srgb('#F1E8DC'), rough=.55, sss=.15, sss_scale=.1)
    MAT['label_serum'] = tex_material('etiqueta sérum', os.path.join(TEX, 'serum.png'))
    MAT['label_jar'] = tex_material('etiqueta crema', os.path.join(TEX, 'jar.png'))
    MAT['label_pump'] = tex_material('etiqueta gel', os.path.join(TEX, 'pump.png'))
    MAT['porcelain'] = principled('porcelana', srgb('#F7F2EA'), rough=.18, sss=.05, coat=.4)
    MAT['pump'] = principled('plástico naranja', srgb('#EE8636'), rough=.42, sss=.08)
    MAT['cream_plastic'] = principled('plástico crema', srgb('#F3ECE2'), rough=.35)
    MAT['peel'] = add_bump(principled('cáscara', srgb('#E8690A'), rough=.42, sss=.12, sss_scale=.3), 160, .35)
    MAT['flesh'] = flesh_material()
    MAT['leaf'] = principled('hoja', srgb('#3C6A35'), rough=.4, sss=.1)
    MAT['podium'] = principled('podio', srgb('#EFE3D3'), rough=.75)
    MAT['podium2'] = principled('podio 2', srgb('#F6D2B0'), rough=.75)


def slice_texture(n=2048):
    """Textura de una rodaja de naranja generada con numpy: gajos, vesículas de jugo, membranas y cáscara."""
    rng = np.random.default_rng(3)
    y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    seg = 11
    # Vesículas: ruido en coordenadas polares, estirado en sentido radial
    nr, nt = 34, 900
    field = rng.random((nr + 1, nt + 1))
    field[:, -1] = field[:, 0]
    fr = np.clip(r, 0, 1) * nr
    ft = (th + math.pi) / (2 * math.pi) * nt
    r0, t0 = np.floor(fr).astype(int).clip(0, nr - 1), np.floor(ft).astype(int).clip(0, nt - 1)
    dr, dt = fr - r0, ft - t0
    sdr, sdt = dr * dr * (3 - 2 * dr), dt * dt * (3 - 2 * dt)
    v = (field[r0, t0] * (1 - sdr) * (1 - sdt) + field[r0 + 1, t0] * sdr * (1 - sdt)
         + field[r0, t0 + 1] * (1 - sdr) * sdt + field[r0 + 1, t0 + 1] * sdr * sdt)
    fine = rng.random((n, n))
    for _ in range(2):
        fine = (fine + np.roll(fine, 1, 0) + np.roll(fine, -1, 0) + np.roll(fine, 1, 1) + np.roll(fine, -1, 1)) / 5
    fine = (fine - fine.min()) / (fine.max() - fine.min())
    ang = (th + math.pi) % (2 * math.pi / seg)
    dist = np.minimum(ang, 2 * math.pi / seg - ang) * r          # distancia a la membrana más cercana
    shade = (.62 + .45 * v) * (.9 + .2 * fine)
    shade *= np.clip(.78 + dist * 9, .78, 1.0)                   # más oscuro junto a las membranas
    shade *= np.clip(.8 + r * .35, .8, 1.0)                      # y hacia el centro
    img = np.stack([.98 * shade, .47 * shade, .045 * shade], -1)
    memb = np.array([.97, .74, .42])
    w = .0035 + .004 * r
    m = np.clip(1 - (dist - w) / .004, 0, 1)[..., None]
    img = img * (1 - m) + memb * m
    core = np.clip(1 - (r - .045) / .02, 0, 1)[..., None]
    img = img * (1 - core) + memb * core
    pith = np.array([.98, .87, .66])
    pm = np.clip((r - .905) / .012, 0, 1)[..., None]
    img = img * (1 - pm) + pith * pm
    peel = np.array([.9, .4, .04])
    km = np.clip((r - .958) / .008, 0, 1)[..., None]
    img = img * (1 - km) + peel * km
    img = np.clip(img, 0, 1) ** 2.2  # a lineal
    rgba = np.concatenate([img, np.ones((n, n, 1))], -1).astype(np.float32)
    im = bpy.data.images.new('rodaja', n, n, float_buffer=True)
    im.colorspace_settings.name = 'Linear Rec.709'
    im.pixels.foreach_set(rgba.ravel())
    # Una imagen generada se regenera en negro al renderizar: se guarda y se vuelve a cargar.
    path = os.path.join(TEX, 'orange_slice.exr')
    im.filepath_raw = path
    im.file_format = 'OPEN_EXR'
    im.save()
    loaded = bpy.data.images.load(path, check_existing=False)
    loaded.colorspace_settings.name = 'Linear Rec.709'
    return loaded


def flesh_material():
    """Pulpa: la textura también se usa como relieve para que las vesículas atrapen la luz."""
    m = tex_material('pulpa', slice_texture(), rough=.22, sss=.25, coat=.35)
    nt = m.node_tree
    tex = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexImage')
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .45
    bump.inputs['Distance'].default_value = .02
    nt.links.new(tex.outputs['Color'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
    return m


# ------------------------------------------------------------------ productos
def serum_bottle():
    outer = [(0, 0), (1.45, 0), (1.57, .05), (1.62, .2), (1.62, 4.6), (1.59, 4.95), (1.47, 5.25), (1.18, 5.5),
             (.82, 5.64), (.7, 5.76), (.7, 6.45), (.64, 6.5)]
    glass = assign(revolve('frasco', outer), MAT['amber'])
    sol = glass.modifiers.new('espesor', 'SOLIDIFY')
    sol.thickness = .13
    sol.offset = -1
    sol.use_even_offset = True
    liquid = assign(revolve('sérum', [(0, .16), (1.46, .16), (1.475, .25), (1.475, 4.35), (0, 4.35)]), MAT['serum'])
    pip = assign(revolve('pipeta', [(0, 1.0), (.1, 1.03), (.17, 1.12), (.2, 1.3), (.2, 6.6)], seg=48), MAT['clear'])
    ps = pip.modifiers.new('espesor', 'SOLIDIFY')
    ps.thickness = .035
    ps.offset = -1
    collar = assign(revolve('aro', [(0, 6.15), (.78, 6.15), (.83, 6.2), (.84, 6.3), (.84, 7.0), (.8, 7.08), (.7, 7.11), (0, 7.11)]), MAT['gold'])
    bulb = assign(revolve('gotero', [(0, 7.1), (.56, 7.1), (.6, 7.2), (.61, 7.5), (.58, 7.9), (.54, 8.35), (.47, 8.7),
                                     (.36, 8.94), (.2, 9.08), (0, 9.12)], sharp=None), MAT['rubber'])
    label = assign(band('etiqueta', 1.637, 1.0, 4.0, 260), MAT['label_serum'])
    parts = [glass, liquid, pip, collar, bulb, label]
    for o in parts:
        o.cycles.is_caustics_caster = o in (glass, liquid)
    return parent(parts, 'sérum vitamina C')


def cream_jar():
    body = assign(revolve('pote', [(0, 0), (2.2, 0), (2.32, .1), (2.36, .3), (2.36, 2.15), (2.28, 2.28), (2.1, 2.32), (0, 2.32)]), MAT['porcelain'])
    lid = assign(revolve('tapa', rounded(2.44, 1.0, .14, z0=2.28)), MAT['gold'])
    label = assign(band('etiqueta', 2.372, .62, 1.96, 300), MAT['label_jar'])
    return parent([body, lid, label], 'crema iluminadora')


def pump_bottle():
    body = assign(revolve('envase', [(0, 0), (1.5, 0), (1.6, .1), (1.63, .3), (1.63, 6.8), (1.56, 7.2), (1.3, 7.46),
                                     (.9, 7.6), (.6, 7.65), (.6, 7.9), (0, 7.9)]), MAT['pump'])
    label = assign(band('etiqueta', 1.645, 1.4, 5.6, 240), MAT['label_pump'])
    collar = assign(revolve('aro', rounded(.82, .75, .1, z0=7.6)), MAT['cream_plastic'])
    stem = assign(revolve('vástago', [(0, 8.3), (.2, 8.3), (.2, 8.95), (0, 8.95)], seg=48), MAT['cream_plastic'])
    head = assign(revolve('cabezal', rounded(.62, .55, .14, z0=8.9)), MAT['cream_plastic'])
    nozzle = assign(revolve('pico', [(0, 0), (.15, 0), (.15, 1.25), (0, 1.25)], seg=32), MAT['cream_plastic'])
    nozzle.rotation_euler = (0, math.radians(90), 0)
    nozzle.location = (.2, 0, 9.2)
    return parent([body, label, collar, stem, head, nozzle], 'gel limpiador')


def orange_half(R=1.4):
    prof = [(R * math.cos(a), R * math.sin(a)) for a in np.linspace(-math.pi / 2, 0, 24)]
    prof[0] = (0, -R)
    peel = assign(revolve('cáscara', prof, seg=96, sharp=None), MAT['peel'])
    face = assign(disk('pulpa', R * .995, z=0.0), MAT['flesh'])
    face.location.z = .002
    return parent([peel, face], 'media naranja')


def orange_slice(R=1.4, h=.28):
    side = assign(revolve('cáscara', [(R, 0), (R, h)], seg=96), MAT['peel'])
    top = assign(disk('pulpa', R, z=h), MAT['flesh'])
    bot = assign(disk('pulpa', R, z=0, up=False), MAT['flesh'])
    return parent([side, top, bot], 'rodaja')


def leaf(L=6, W=1.3):
    ts = np.linspace(0, 1, 40)
    top = [(t * L, W * math.sin(math.pi * t) ** .8 * (1 - .3 * t), 0) for t in ts]
    bot = [(t * L, -W * math.sin(math.pi * t) ** .8 * (1 - .3 * t), 0) for t in ts[::-1][1:-1]]
    verts = top + bot
    o = mesh_obj('hoja', verts, [tuple(range(len(verts)))], smooth=False)
    s = o.modifiers.new('espesor', 'SOLIDIFY')
    s.thickness = .05
    return assign(o, MAT['leaf'])


def podium(r, h, mat):
    o = assign(revolve('podio', rounded(r, h, .14)), mat)
    o.cycles.is_caustics_receiver = True
    return o


def cyclorama(color, width=160, depth=80, wall_y=22, radius=16, height=80):
    prof = [(-depth, 0)]
    for a in np.linspace(-math.pi / 2, 0, 24):
        prof.append((wall_y - radius + radius * math.cos(a), radius + radius * math.sin(a)))
    prof.append((wall_y, height))
    verts, faces = [], []
    for y, z in prof:
        verts += [(-width / 2, y, z), (width / 2, y, z)]
    for j in range(len(prof) - 1):
        a = 2 * j
        faces.append((a, a + 1, a + 3, a + 2))
    o = assign(mesh_obj('fondo', verts, faces), principled('fondo', color, rough=.9))
    o.cycles.is_caustics_receiver = True
    return o


def terrazzo_floor(size=120):
    o = mesh_obj('terrazo', [(-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0)], [(0, 1, 2, 3)])
    m = principled('terrazo', rough=.35, coat=.2)
    nt = m.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    base = srgb('#EFE6DA')
    mix = None
    for scale, thr in ((1.1, .16), (2.6, .12)):
        v = nt.nodes.new('ShaderNodeTexVoronoi')
        v.inputs['Scale'].default_value = scale
        nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
        lt = nt.nodes.new('ShaderNodeMath')
        lt.operation = 'LESS_THAN'
        lt.inputs[1].default_value = thr
        nt.links.new(v.outputs['Distance'], lt.inputs[0])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        els = ramp.color_ramp.elements
        els[0].color = srgb('#C9622E')
        els[1].position = .3
        els[1].color = srgb('#EE9A4C')
        for pos, col in ((.55, '#6E4A35'), (.78, '#D8CBBB')):
            e = els.new(pos)
            e.color = srgb(col)
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(v.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Red'], ramp.inputs['Fac'])
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        nt.links.new(lt.outputs['Value'], mx.inputs['Factor'])
        # ShaderNodeMix RGBA: entradas de color en 6 (A) y 7 (B), salida de color en 2
        if mix is None:
            mx.inputs[6].default_value = base
        else:
            nt.links.new(mix.outputs[2], mx.inputs[6])
        nt.links.new(ramp.outputs['Color'], mx.inputs[7])
        mix = mx
    nt.links.new(mix.outputs[2], nt.nodes['Principled BSDF'].inputs['Base Color'])
    assign(o, m)
    o.cycles.is_caustics_receiver = True
    return o


# ------------------------------------------------------------------ luces y cámara
def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def area(loc, target, energy, size, color=(1, 1, 1)):
    li = bpy.data.lights.new('área', 'AREA')
    li.energy = energy
    li.size = size
    li.color = color
    o = link(bpy.data.objects.new('área', li))
    o.location = loc
    aim(o, target)
    return o


def sun_blinds(direction, target=(0, 0, 4), strength=4.0, angle=1.4, period=2.2, open_=.55, roll=20, dist=40,
               color=(1, .88, .72), caustics=False):
    """Sol que entra por una persiana: proyecta franjas de luz y sombra."""
    d = Vector(direction).normalized()
    li = bpy.data.lights.new('sol', 'SUN')
    li.energy = strength
    li.angle = math.radians(angle)
    li.color = color
    li.cycles.is_caustics_light = caustics
    sun = link(bpy.data.objects.new('sol', li))
    sun.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()
    plane = mesh_obj('persiana', [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [(0, 1, 2, 3)], smooth=False)
    plane.location = Vector(target) - d * dist
    plane.rotation_euler = ((-d).to_track_quat('Z', 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'Z').to_quaternion()).to_euler()
    for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter'):
        setattr(plane, attr, False)
    m = bpy.data.materials.new('persiana')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    mod = nt.nodes.new('ShaderNodeMath')
    mod.operation = 'PINGPONG'
    mod.inputs[1].default_value = period / 2
    nt.links.new(sep.outputs['X'], mod.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = period / 2 * open_
    nt.links.new(mod.outputs['Value'], gt.inputs[0])
    mixs = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gt.outputs['Value'], mixs.inputs['Fac'])
    nt.links.new(nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0], mixs.inputs[1])
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    diff.inputs['Color'].default_value = (0, 0, 0, 1)
    nt.links.new(diff.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    assign(plane, m)
    return sun


def camera(loc, target, lens=70, fstop=None):
    cam = bpy.data.cameras.new('cámara')
    cam.lens = lens
    o = link(bpy.data.objects.new('cámara', cam))
    o.location = loc
    aim(o, target)
    if fstop:
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = fstop
        cam.dof.focus_distance = (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = o
    return o


def studio(target, key=9000, fill=3200, rim=7000):
    area((-16, -20, 16), target, key, 12)
    area((18, -16, 9), target, fill, 14, (1, .97, .94))
    area((7, 14, 20), target, rim, 9)


def render(name):
    s = bpy.context.scene
    s.render.filepath = os.path.join(OUT, f'{name}{"_preview" if PREVIEW else ""}.jpg')
    bpy.ops.render.render(write_still=True)
    print('->', s.render.filepath)


# ------------------------------------------------------------------ tomas
def shot_hero_orange():
    reset((1600, 2000), 128)
    materials()
    cyclorama(srgb('#EE8A2C'))
    podium(3.7, 2.2, MAT['podium'])
    b = serum_bottle()
    b.location = (0, .2, 2.2)
    b.rotation_euler.z = math.radians(-8)
    h1 = orange_half(1.25)
    h1.location = (2.25, -1.55, 2.2 + 1.25 * .97)
    h1.rotation_euler = (math.radians(62), math.radians(-14), 0)
    h2 = orange_half(1.6)
    h2.location = (-3.9, -3.2, 1.6 * .97)
    h2.rotation_euler = (math.radians(55), math.radians(18), 0)
    studio((0, 0, 5))
    sun_blinds((.62, .42, -.66), target=(0, 0, 5), strength=3.2, roll=28)
    camera((0, -36, 6.4), (0, 0, 5.2), lens=72, fstop=8)
    render('hero_orange')


def shot_hero_cream():
    reset((1080, 1920), 128)
    materials()
    cyclorama(srgb('#F3E6D7'))
    podium(4.2, 1.3, MAT['podium2'])
    p2 = podium(2.7, 2.4, MAT['podium'])
    p2.location = (.5, .9, 1.3)
    b = serum_bottle()
    b.location = (.5, .7, 3.7)
    b.rotation_euler.z = math.radians(6)
    h = orange_half(1.35)
    h.location = (-2.6, -2.9, 1.35 * .97)
    h.rotation_euler = (math.radians(50), math.radians(10), 0)
    s = orange_slice(1.25, .3)
    s.location = (2.9, -3.6, 0)
    s.rotation_euler = (math.radians(-8), 0, 0)
    studio((0, 0, 6), key=8000, fill=3200)
    sun_blinds((-.55, .5, -.67), target=(0, 0, 6), strength=3.0, roll=-25, period=2.6)
    camera((.5, -44, 7.6), (.5, 0, 5.6), lens=80, fstop=8)
    render('hero_cream')


def shot_family():
    reset((1600, 1600), 128)
    materials()
    cyclorama(srgb('#F6D3B0'))
    pl = podium(2.6, 1.0, MAT['podium'])
    pl.location = (-5.2, .6, 0)
    pc = podium(3.0, 2.6, MAT['podium'])
    pc.location = (0, 1.2, 0)
    pr = podium(3.3, .7, MAT['podium'])
    pr.location = (5.4, .2, 0)
    pump = pump_bottle()
    pump.location = (-5.2, .6, 1.0)
    pump.rotation_euler.z = math.radians(10)
    b = serum_bottle()
    b.location = (0, 1.2, 2.6)
    jar = cream_jar()
    jar.location = (5.4, .2, .7)
    jar.rotation_euler.z = math.radians(-6)
    for x, y, R, rx in ((-2.4, -3.2, 1.2, 60), (2.6, -3.6, 1.0, 48)):
        h = orange_half(R)
        h.location = (x, y, R * .97)
        h.rotation_euler = (math.radians(rx), math.radians(10), 0)
    lf = leaf(6.5, 1.3)
    lf.location = (-9.5, -2.2, .03)
    lf.rotation_euler.z = math.radians(25)
    studio((0, 0, 4.5), key=10000, fill=3800)
    sun_blinds((.6, .45, -.66), target=(0, 0, 4.5), strength=3.0, roll=30, period=2.8)
    camera((0, -46, 9.5), (0, 0, 4.4), lens=62, fstop=9)
    render('family')


def shot_flatlay():
    reset((1600, 1600), 128)
    materials()
    terrazzo_floor()
    # sérum acostado con la etiqueta hacia arriba
    b = serum_bottle()
    b.location = (-1.2, .4, 1.62)
    best = None
    for k in range(4):
        rot = Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(90 * k), 4, 'Z')
        n = (rot.to_3x3() @ Vector((0, -1, 0)))
        if best is None or n.z > best[0]:
            best = (n.z, k)
    b.rotation_euler = (Matrix.Rotation(math.radians(-28), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'Y')
                        @ Matrix.Rotation(math.radians(90 * best[1]), 4, 'Z')).to_euler()
    jar = cream_jar()
    jar.location = (5.2, 4.0, 0)
    for x, y, R in ((4.6, -3.4, 1.45), (-4.6, -4.6, 1.2)):
        h = orange_half(R)  # boca arriba: la cáscara queda abajo
        h.location = (x, y, R)
    for x, y in ((-2.4, 5.0), (8.4, .6)):
        s = orange_slice(1.3, .25)
        s.location = (x, y, 0)
    for x, y, rz, L in ((-11.5, 4.0, -30, 6), (9.5, 7.5, 205, 5.5), (-9.0, -7.0, 35, 5)):
        lf = leaf(L, L * .21)
        lf.location = (x, y, .02)
        lf.rotation_euler.z = math.radians(rz)
    area((-20, -20, 40), (0, 0, 0), 11000, 20)
    area((20, 10, 35), (0, 0, 0), 3500, 20, (1, .97, .94))
    sun_blinds((.45, .35, -.82), target=(0, 0, 0), strength=3.4, roll=40, period=3.0, dist=45)
    camera((0, -1.0, 36), (0, 0, 0), lens=50, fstop=11)
    render('flatlay')


SHOTS = {'hero_orange': shot_hero_orange, 'hero_cream': shot_hero_cream, 'family': shot_family, 'flatlay': shot_flatlay}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name in (ARGS or SHOTS):
        SHOTS[name]()
