"""Build the chasm rev3 scene from design.json + keys_8.json.

    blender -b --factory-startup --python-exit-code 1 --python blender/build_scene.py -- \
        [--pose flat|tented|together|underside] [--save blender/chasm_v3.blend]

Importable: build(design) -> ctx; set_pose(name, support_z_mm=0).
Geometry is generated in mm in the half frame (x right, y back, z up, z=0 = case
bottom face), converted to metres on object creation. Pose matrices are mm-space,
assigned to L_root/R_root/hub_root with translation scaled.
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import outline as ol
import rev2_keycaps
import rev2_case

MM = 0.001
RAD = math.radians
CTX = None


def V3(p, z=0.0):
    return (p[0] * MM, p[1] * MM, (p[2] * MM if len(p) > 2 else z * MM))


def new_obj(name, verts_mm, faces, coll, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([V3(v) for v in verts_mm], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def recalc_normals(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def flat_shade(ob):
    for p in ob.data.polygons:
        p.use_smooth = False


def prism(name, pts_ccw, z0, z1, coll, mat=None):
    """Closed prism: CCW plan polygon extruded z0..z1."""
    n = len(pts_ccw)
    verts = [(x, y, z0) for x, y in pts_ccw] + [(x, y, z1) for x, y in pts_ccw]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return new_obj(name, verts, faces, coll, mat)


def rounded_rect(w, d, r, n_arc=4, cx=0.0, cy=0.0):
    """CCW rounded-rect plan points centred (cx,cy); n_arc pts per corner."""
    pts = []
    for ccx, ccy, a0 in ((w / 2 - r, -d / 2 + r, -90), (w / 2 - r, d / 2 - r, 0),
                         (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180)):
        for j in range(n_arc):
            a = RAD(a0 + 90.0 * j / n_arc)
            pts.append((cx + ccx + r * math.cos(a), cy + ccy + r * math.sin(a)))
    return pts


def eval_apply(obj):
    """Evaluate modifier stack, replace object data with the result, drop modifiers."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    mats = list(obj.data.materials)
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    obj.data = me
    obj.modifiers.clear()


def bool_diff(obj, cutter):
    # XZ-plane rings (port cutters) come in with flipped caps -> recalc first,
    # else EXACT leaves the wall face behind and the port reads as a pill (H1)
    recalc_normals(cutter.data)
    m = obj.modifiers.new("cut", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.solver = 'EXACT'
    m.object = cutter
    eval_apply(obj)
    bpy.data.objects.remove(cutter)


def stadium_ring(name, o_pts, i_pts, d0, d1, to_v, coll, mat):
    """Hollow open stadium tube (USB-C receptacle): outer+inner rings at two
    depths, no end caps - the port opening must pass through to the dark
    interior, not stop on a solid front face (H7)."""
    n = len(o_pts)
    assert len(i_pts) == n
    verts = ([to_v(*p, d0) for p in o_pts] + [to_v(*p, d0) for p in i_pts] +
             [to_v(*p, d1) for p in o_pts] + [to_v(*p, d1) for p in i_pts])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((3 * n + i, 3 * n + j, 2 * n + j, 2 * n + i))
        faces.append((j, i, 2 * n + i, 2 * n + j))
        faces.append((n + i, n + j, 3 * n + j, 3 * n + i))
    ob = new_obj(name, verts, faces, coll, mat)
    recalc_normals(ob.data)
    return ob


def bevel(obj, width_mm, segments=3):
    m = obj.modifiers.new("bevel", 'BEVEL')
    m.limit_method = 'ANGLE'
    m.width = width_mm * MM
    m.segments = segments
    eval_apply(obj)


def box(name, cx, cy, z0, z1, w, d, coll, mat=None, rot_z=0.0):
    ob = prism(name, [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)],
               z0, z1, coll, mat)
    ob.location.x, ob.location.y = cx * MM, cy * MM
    if rot_z:
        ob.rotation_euler.z = RAD(rot_z)
    return ob


def disc(name, cx, cy, z0, z1, r, coll, mat=None, seg=24):
    pts = [(cx + r * math.cos(2 * math.pi * i / seg),
            cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    return prism(name, pts, z0, z1, coll, mat)


# ---------------------------------------------------------------- materials

BSDF_MAP = {"metallic": "Metallic", "roughness": "Roughness", "ior": "IOR",
            "transmission": "Transmission Weight", "coat": "Coat Weight",
            "subsurface": "Subsurface Weight", "specular": "Specular IOR Level"}


def build_materials(spec):
    mats = {}
    for name, s in spec.items():
        if name.startswith("_"):
            continue
        m = bpy.data.materials.new(name)
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if "base" in s:
            bsdf.inputs["Base Color"].default_value = (*s["base"], 1.0)
        for k, inp in BSDF_MAP.items():
            if k in s and inp in bsdf.inputs:
                bsdf.inputs[inp].default_value = s[k]
        if s.get("emission_w"):
            for nm in ("Emission Color", "Emission"):
                if nm in bsdf.inputs:
                    bsdf.inputs[nm].default_value = (1.0, 1.0, 1.0, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = s["emission_w"]
        if s.get("volume_scatter_density_per_m"):
            vs = nt.nodes.new("ShaderNodeVolumeScatter")
            vs.inputs["Density"].default_value = s["volume_scatter_density_per_m"]
            nt.links.new(vs.outputs["Volume"],
                         nt.nodes.get("Material Output").inputs["Volume"])
        if "shadow_transmit" in s:
            # shadow-ray trick: direct light passes through clear/frost shells
            # (tint for diffuse-looking transmission behind them)
            tp = nt.nodes.new("ShaderNodeBsdfTransparent")
            tp.inputs["Color"].default_value = (s["shadow_transmit"],) * 3 + (1.0,)
            lp = nt.nodes.new("ShaderNodeLightPath")
            mix = nt.nodes.new("ShaderNodeMixShader")
            mo = nt.nodes.get("Material Output")
            nt.links.new(bsdf.outputs[0], mix.inputs[1])
            nt.links.new(tp.outputs[0], mix.inputs[2])
            nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs[0])
            nt.links.new(mix.outputs[0], mo.inputs["Surface"])
        if name == "lipo_silver":  # soft pouch bump
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = 6.0
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.25
            bump.inputs["Distance"].default_value = 0.4 * MM
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        mats[name] = m
    return mats


def emissive_mat(name, image_path, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(os.path.join(ROOT, image_path))
    img.colorspace_settings.name = "sRGB"
    tex.image = img
    em.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- keycap mesh

def cap_mesh(name, w_u, row, kc):
    """Hollow lofted cap, local frame: origin = key centre, z=0 = skirt bottom."""
    unit = kc["_unit"]
    bw = w_u * unit - (unit - kc["base_1u_mm"])
    bd = kc["base_1u_mm"]
    tw = bw - kc["top_shrink_mm"][0]
    td = bd - kc["top_shrink_mm"][1]
    shift = kc["top_back_shift_mm"]
    h = row["h_mm"]
    tilt = math.tan(RAD(row["tilt_deg"]))
    wall = kc["wall_mm"]
    dish = kc["dish_mm"]
    n = 4                                        # 16 pts/ring
    Rdish = ((tw / 2) ** 2 + dish ** 2) / (2 * dish) if dish else 1e9

    def plane_z(y):
        return h + (y - shift) * tilt

    def surf_z(x, y):
        return plane_z(y) - (Rdish - math.sqrt(max(Rdish ** 2 - x * x, 0.0)))

    base = rounded_rect(bw, bd, kc["r_base_mm"], n)
    top = rounded_rect(tw, td, kc["r_top_mm"], n, 0, shift)
    ibase = rounded_rect(bw - 2 * wall, bd - 2 * wall,
                         max(kc["r_base_mm"] - wall, 0.3), n)
    itop = rounded_rect(tw - 2 * wall, td - 2 * wall,
                        max(kc["r_top_mm"] - wall, 0.3), n, 0, shift)
    ts = (0.0, 0.45, 0.8, 1.0)

    def ring(t, a_pts, b_pts, drop=0.0):
        out = []
        for (ax, ay), (bx, by) in zip(a_pts, b_pts):
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            out.append((x, y, (plane_z(y) - drop) * t))
        return out

    rings = [ring(t, base, top) for t in ts]
    irings = [ring(t, ibase, itop, wall) for t in ts]
    strip_f = (0.68, 0.42, 0.18)
    strips = [[(x * f, y, surf_z(x * f, y)) for x, y in top] for f in strip_f]

    m = len(top)
    verts = [v for r in rings for v in r] + [v for r in irings for v in r] + \
            [v for r in strips for v in r]
    O, I, S = 0, 4 * m, 8 * m
    faces = []
    for k in range(3):                                   # outer + inner walls
        for i in range(m):
            a, b = O + k * m + i, O + k * m + (i + 1) % m
            faces.append((a, b, b + m, a + m))
            a, b = I + k * m + i, I + k * m + (i + 1) % m
            faces.append((a, b, b + m, a + m))
    for i in range(m):                                   # bottom rim
        a, b = O + i, O + (i + 1) % m
        faces.append((a, I + i, I + (i + 1) % m, b))
    faces.append(tuple(I + 3 * m + i for i in reversed(range(m))))  # ceiling
    for k in range(len(strip_f)):                        # dished top strips
        prev = O + 3 * m if k == 0 else S + (k - 1) * m
        cur = S + k * m
        for i in range(m):
            faces.append((prev + i, cur + i, cur + (i + 1) % m, prev + (i + 1) % m))
    faces.append(tuple(S + (len(strip_f) - 1) * m + i for i in range(m)))

    me = bpy.data.meshes.new(name)
    me.from_pydata([V3(v) for v in verts], [], faces)
    me.update()
    recalc_normals(me)
    return me


# ---------------------------------------------------------------- gull ribbon

def bez(t, c1, c2, tip):
    u = 1 - t
    return (3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * tip[0],
            3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * tip[1])


def wing_pts(design, side, span_mm, seg=24):
    """side=+1 right wing, -1 left (mirrored). Centreline pts in gull frame."""
    c1, c2, tip = (design["inputs"][k] for k in ("gull_c1", "gull_c2", "gull_tip"))
    s = span_mm / tip[0]
    return [(side * bez(t / seg, c1, c2, tip)[0] * s,
             bez(t / seg, c1, c2, tip)[1] * s) for t in range(seg + 1)]


def decimate(pts, tol=0.05):
    """Douglas-Peucker: simplify a closed polyline to <= tol mm deviation."""
    n = len(pts)
    if n < 4:
        return pts
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        x1, y1 = pts[a]
        x3, y3 = pts[b]
        dx, dy = x3 - x1, y3 - y1
        d = math.hypot(dx, dy) or 1e-9
        imax, dmax = -1, tol
        for i in range(a + 1, b):
            x2, y2 = pts[i]
            dev = abs((x2 - x1) * dy - (y2 - y1) * dx) / d
            if dev > dmax:
                dmax, imax = dev, i
        if imax >= 0:
            keep[imax] = True
            stack += [(a, imax), (imax, b)]
    return [p for p, k in zip(pts, keep) if k]


def ribbon(name, pts2, w, z0, z1, coll, mat, end_discs=True):
    """Flat ribbon of width w along a 2D centreline, extruded z0..z1.
    End caps are semicircles centred exactly on the curve endpoints."""
    n = len(pts2)
    left, right = [], []
    for i, p in enumerate(pts2):
        pa = pts2[max(0, i - 1)]; pb = pts2[min(n - 1, i + 1)]
        tx, ty = pb[0] - pa[0], pb[1] - pa[1]
        l = math.hypot(tx, ty) or 1
        left.append((p[0] - ty / l * w / 2, p[1] + tx / l * w / 2))
        right.append((p[0] + ty / l * w / 2, p[1] - tx / l * w / 2))
    if end_discs:
        def cap(p, d_, back):
            a0 = math.atan2(d_[1], d_[0])
            return [(p[0] + w / 2 * math.cos(a0 + back + (-math.pi / 2 + math.pi * j / 8)),
                     p[1] + w / 2 * math.sin(a0 + back + (-math.pi / 2 + math.pi * j / 8)))
                    for j in range(9)]
        d0 = (pts2[1][0] - pts2[0][0], pts2[1][1] - pts2[0][1])
        d1 = (pts2[-1][0] - pts2[-2][0], pts2[-1][1] - pts2[-2][1])
        outline = right + cap(pts2[-1], d1, 0) + left[::-1] + cap(pts2[0], d0, math.pi)
    else:
        outline = left + right[::-1]
    ob = prism(name, outline, z0, z1, coll, mat)
    recalc_normals(ob.data)
    return ob


# ---------------------------------------------------------------- text legends

_CAP_SCALE = {}


def font_cap_scale(font):
    """G2 fix: Blender normalises some fonts (Segoe UI) by their full ascent/descent box,
    so a capital is only ~0.42 x size instead of ~0.70. Measure 'H' once per font and
    return the factor that makes cap height = 0.70 x the design size."""
    key = font.name if font else None
    if key in _CAP_SCALE:
        return _CAP_SCALE[key]
    cu = bpy.data.curves.new("_capprobe", 'FONT')
    cu.body = "H"
    cu.size = 1.0
    if font:
        cu.font = font
    ob = bpy.data.objects.new("_capprobe", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ys = [v.co.y for v in me.vertices]
    h = (max(ys) - min(ys)) if ys else 0.7
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.curves.remove(cu)
    _CAP_SCALE[key] = 0.70 / h if h > 1e-6 else 1.0
    return _CAP_SCALE[key]


def add_legend(cap, k, rowcfg, kc, mat, coll, fonts):
    label = k["label"]
    txt = kc["legend"].get("text", {}).get(label, label)
    if txt == "":
        return
    single = len(label) == 1 or label in ("M1", "M2", "M3", "M4")
    arrows = label in ("Up", "Down", "Left", "Right")
    mod = not single and not arrows
    size = kc["legend"]["mod_size_mm"] if mod else kc["legend"]["alpha_size_mm"]
    cu = bpy.data.curves.new(f"leg_{k['id']}", 'FONT')
    cu.body = txt
    font = fonts["sym"] if arrows else fonts["main"]
    if font:
        cu.font = font
    cu.size = size * MM * font_cap_scale(font if font else None)
    cu.extrude = kc["legend"]["thickness_mm"] * MM
    cu.align_x = 'CENTER' if arrows else 'LEFT'
    cu.align_y = 'CENTER' if arrows else ('BOTTOM' if mod else 'TOP')
    ob = bpy.data.objects.new(f"{cap.name}_leg", cu)
    coll.objects.link(ob)

    unit = kc["_unit"]
    bw = k["w_u"] * unit - (unit - kc["base_1u_mm"])
    tw = bw - kc["top_shrink_mm"][0]
    td = kc["base_1u_mm"] - kc["top_shrink_mm"][1]
    shift = kc["top_back_shift_mm"]
    mx, my = kc["legend"]["margin_mm"]
    if arrows:
        gx, gy = 0.0, shift
    elif mod:
        gx, gy = -tw / 2 + mx, shift - td / 2 + my
    else:
        gx, gy = -tw / 2 + mx, shift + td / 2 - my
    tilt = math.tan(RAD(rowcfg["tilt_deg"]))
    Rdish = ((tw / 2) ** 2 + kc["dish_mm"] ** 2) / (2 * kc["dish_mm"])
    surf = rowcfg["h_mm"] + (gy - shift) * tilt - \
        (Rdish - math.sqrt(max(Rdish ** 2 - gx * gx, 0.0)))
    z = surf - kc["legend"]["depth_below_top_mm"] - kc["legend"]["thickness_mm"]
    ob.location = (gx * MM, gy * MM, z * MM)
    ob.rotation_euler.x = RAD(rowcfg["tilt_deg"])

    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.materials.append(mat)
    mob = bpy.data.objects.new(f"{cap.name}_leg", me)
    mob.matrix_world = ob.matrix_world
    coll.objects.link(mob)
    bpy.data.objects.remove(ob)
    mob.parent = cap
    mob.matrix_parent_inverse = Matrix.Identity(4)


# ---------------------------------------------------------------- pose math

def desk_plane(M):
    """z = (c - nx*x - ny*y)/nz : the desk (world z=0) expressed in case coords."""
    n = (M[2][0], M[2][1], M[2][2])
    c = -M[2][3]
    return n, c


def roll_M(g, D, M, beta):
    """Roll the posed half about its inner front-pad / inner rear-bar contact line."""
    pad_h = D["feet"]["front_pad"]["h_mm"]
    c0 = M @ Vector((g["pads"]["inner"][0], g["pads"]["inner"][1], -pad_h))
    n, c = desk_plane(M)
    bi = g["bars"]["inner"]
    bz = (c - n[0] * bi[0] - n[1] * bi[1]) / n[2]
    c1 = M @ Vector((bi[0], bi[1], bz))
    ax = (c1 - c0).normalized()
    probe = M @ Vector((g["corners"]["back_outer"][0], g["corners"]["back_outer"][1], 0))
    def lift(s):
        return (Matrix.Rotation(s * beta, 3, ax) @ (probe - c0)).z
    s = 1 if lift(1) > lift(-1) else -1
    return (Matrix.Translation(c0) @ Matrix.Rotation(s * beta, 4, ax)
            @ Matrix.Translation(-c0)) @ M


def pose_flat_M(g, D, gap_mm, yaw_deg, level=False):
    """align inner edge || world y at x=-/+gap/2, yaw about the logo vertex, tilt, rest."""
    half = g["half"]
    n_i, d_i = g["inner"]
    target = 0.0 if half == "L" else 180.0
    ang = math.degrees(math.atan2(n_i[1], n_i[0]))
    theta = (target - ang + 180) % 360 - 180
    R = Matrix.Rotation(RAD(theta), 4, 'Z')
    n2 = R @ Vector((n_i[0], n_i[1], 0))
    line_x = d_i * n2.x
    goal_x = -gap_mm / 2 if half == "L" else gap_mm / 2
    v = R @ Vector((g["vertex"][0], g["vertex"][1], 0))
    M = Matrix.Translation((goal_x - line_x, -v.y, 0)) @ R
    vw = M @ Vector((g["vertex"][0], g["vertex"][1], 0))
    sgn = -1 if half == "L" else 1
    M = (Matrix.Translation(vw) @ Matrix.Rotation(RAD(sgn * yaw_deg), 4, 'Z')
         @ Matrix.Translation(-vw)) @ M
    if not level:
        # typing tilt about the (world) front pad line, then drop to desk
        pad_h = D["feet"]["front_pad"]["h_mm"]
        alpha = RAD(D["feet"]["typing_angle_deg"])
        aw_a = M @ Vector((g["pads"]["outer"][0], g["pads"]["outer"][1], -pad_h))
        aw_b = M @ Vector((g["pads"]["inner"][0], g["pads"]["inner"][1], -pad_h))
        adir = (aw_b - aw_a).normalized()
        probe = M @ Vector((g["corners"]["back_outer"][0],
                            g["corners"]["back_outer"][1], 0))
        def lift(s):
            return (Matrix.Rotation(s * alpha, 3, adir) @ (probe - aw_a)).z
        s = 1 if lift(1) > lift(-1) else -1
        M = (Matrix.Translation(aw_a) @ Matrix.Rotation(s * alpha, 4, adir)
             @ Matrix.Translation(-aw_a)) @ M
        M = Matrix.Translation((0, 0, pad_h)) @ M
        if D["case"].get("lower_base"):
            front_z = min((M @ Vector((x,y,D["case"]["height_mm"]))).z for x,y in g["outline"])
            M = Matrix.Translation((0,0,D["case"]["height_mm"]-front_z)) @ M
        return M
    return M


def _m_assign(obj, M_mm):
    M = M_mm.copy()
    M.translation = M_mm.translation * MM
    obj.matrix_world = M


def set_pose(name, support_z_mm=0.0, ctx=None):
    ctx = ctx or CTX
    D, geom = ctx["design"], ctx["geom"]
    P = D["poses"]
    beta = RAD(D["tent"]["angle_deg"])
    for half in "LR":
        g = geom[half]
        for nm, base in g["basis0"].items():
            bpy.data.objects[nm].matrix_basis = base.copy()
        deployed = False
        for nm, (st, dep) in g["link_bases"].items():
            bpy.data.objects[nm].matrix_basis = st
        for nm, (st, dep) in g["u_bases"].items():
            bpy.data.objects[nm].matrix_basis = st
        if name in ("flat", "plinth"):
            M = pose_flat_M(g, D, P["flat"]["gap_mm"], P["flat"]["yaw_deg"])
        elif name == "together":
            M = pose_flat_M(g, D, P["together"]["seam_mm"], 0.0)
        elif name == "tented":
            tp = P["tented"]
            M = pose_flat_M(g, D, tp["gap_mm"], 0.0)
            if tp["half"] == half:
                M = roll_M(g, D, M, beta)
                deployed = True                   # deploy the U-frame
                for nm, (st, dep) in g["link_bases"].items():
                    bpy.data.objects[nm].matrix_basis = dep
                for nm, (st, dep) in g["u_bases"].items():
                    bpy.data.objects[nm].matrix_basis = dep
        elif name == "underside":
            if P["underside"]["half"] == half:
                M = pose_flat_M(g, D, P["flat"]["gap_mm"], P["flat"]["yaw_deg"])
                # highest cap-top point in world (pre-flip)
                kc = D["keycap"]
                zmax = 0.0
                for k in g["keys"]:
                    row = g["row_of"](k["label"])
                    rc = D["keycap"]["rows"][row]
                    td = kc["base_1u_mm"] - kc["top_shrink_mm"][1]
                    zz = D["stack"]["cap_bottom_z"] + rc["h_mm"] + \
                        (td / 2 + kc["top_back_shift_mm"]) * math.tan(RAD(abs(rc["tilt_deg"])))
                    zmax = max(zmax, (M @ Vector((k["x_mm"], k["y_mm"], zz))).z)
                xs = [p[0] for p in g["outline"]]; ys = [p[1] for p in g["outline"]]
                ctr = M @ Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))
                F = (Matrix.Translation(ctr) @ Matrix.Rotation(math.pi, 4, 'X')
                     @ Matrix.Translation(-ctr))
                M = F @ M
                M = Matrix.Translation((0, 0, zmax)) @ M
            else:
                M = pose_flat_M(g, D, P["flat"]["gap_mm"], P["flat"]["yaw_deg"])
        elif name == "exploded":
            M = pose_flat_M(g, D, P["exploded"]["gap_mm"],
                            P["exploded"]["yaw_deg"], level=True)
        else:
            raise ValueError(name)
        M = Matrix.Translation((0, 0, support_z_mm)) @ M
        _m_assign(g["root"], M)
        if name == "exploded":
            for nm, off in g["explode_off"].items():
                ob = bpy.data.objects[nm]
                ob.matrix_basis = Matrix.Translation(
                    (0, 0, off * MM)) @ g["basis0"][nm]
            for nm, detail in D['explode'].get('inspect_caps',{}).items():
                if not nm.startswith(half+'_'): continue
                ob=bpy.data.objects[nm]
                ob.location += Vector(detail['offset_mm'])*MM
                ob.rotation_euler.x=RAD(detail['tilt_x_deg'])
    for nm, base in geom["hub_basis0"].items():
        bpy.data.objects[nm].matrix_basis = base.copy()
    if name == "exploded":
        for nm, off in geom["hub_explode_off"].items():
            ob = bpy.data.objects[nm]
            ob.matrix_basis = Matrix.Translation(
                (0, 0, off * MM)) @ geom["hub_basis0"][nm]
    hp = P.get(name, P["flat"])
    hxy = hp.get("hub_xy", P["flat"]["hub_xy"])
    hyaw = hp.get("hub_yaw_deg", 0.0)
    ctx["geom"]["hub_root"].matrix_world = Matrix.Translation(
        (hxy[0] * MM, hxy[1] * MM, support_z_mm * MM)) @ Matrix.Rotation(RAD(hyaw), 4, 'Z')


# ---------------------------------------------------------------- main build

def build(design):
    global CTX
    for ob in list(bpy.data.objects):          # factory-startup Cube/Light/Camera
        bpy.data.objects.remove(ob)
    keys = json.load(open(os.path.join(ROOT, design["inputs"]["keys"]), encoding="utf-8"))
    ol.rev3_plan.synchronize_plan(design, keys)
    kv = ol.knob_virtual_key(design, keys)  # keyboard knob keepout: outlines grow around it
    if kv:
        keys["keys"].append(kv)
    lv = ol.logo_virtual_key(design, keys)
    if lv:
        keys["keys"].append(lv)
    unit = keys["unit_mm"]
    D = design
    derived = {"unit_mm": unit}
    mats = build_materials(D["materials"])
    frost=mats[D["keycap"]["material"]]
    nt=frost.node_tree
    grain=nt.nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value=D["keycap"]["rev2"]["skin_grain_scale_per_m"]
    grain.inputs['Detail'].default_value=2.0
    coord=nt.nodes.new('ShaderNodeTexCoord')
    bump=nt.nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value=D["keycap"]["rev2"]["skin_grain_bump_mm"]*MM
    bump.inputs['Strength'].default_value=D["keycap"]["rev2"]["skin_grain_strength"]
    nt.links.new(coord.outputs['Object'],grain.inputs['Vector'])
    nt.links.new(grain.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])
    rough=nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value=0.35
    rough.inputs['From Max'].default_value=0.65
    rough.inputs['To Min'].default_value=D['keycap']['rev2']['skin_roughness_range'][0]
    rough.inputs['To Max'].default_value=D['keycap']['rev2']['skin_roughness_range'][1]
    nt.links.new(grain.outputs['Fac'],rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'],nt.nodes['Principled BSDF'].inputs['Roughness'])

    # stagger-hugging top opening, generated offline by outline.py (needs scipy/cv2)
    import hashlib
    ops = json.load(open(os.path.join(HERE, "out", "opening.json"), encoding="utf-8"))
    src = hashlib.sha1(json.dumps([D["case"], keys["keys"]],
                                  sort_keys=True).encode()).hexdigest()
    assert ops["source_sha1"] == src, \
        "opening.json is stale — run `python blender/outline.py` first"

    scene_coll = bpy.context.scene.collection
    colls = {}
    for nm in ("L", "R", "Hub", "Studio", "Cut"):
        c = bpy.data.collections.new(nm)
        scene_coll.children.link(c)
        colls[nm] = c

    row_of = {}
    for rname, r in D["keycap"]["rows"].items():
        if rname.startswith("_") or r["labels"] == "rest":
            continue
        for lab in r["labels"]:
            row_of[lab] = rname

    def get_row(label):
        return row_of.get(label, "R4")

    fonts = {}
    for key, path in (("main", D["keycap"]["legend"]["font"]),
                      ("sym", D["keycap"]["legend"]["font_symbols"])):
        try:
            fonts[key] = bpy.data.fonts.load(path)
        except Exception:
            fonts[key] = None

    kc = dict(D["keycap"]); kc["_unit"] = unit
    cap_meshes = {}
    geom = {}
    logs = []

    corner_idx = {"L": {"front_outer": 0, "front_inner": 2, "back_inner": 4,
                        "back_outer": 6},
                  "R": {"front_inner": 0, "front_outer": 2, "back_outer": 5,
                        "back_inner": 7}}

    for half in "LR":
        coll = colls[half]
        edges = D["case"]["outline"][half]
        out_pts, V, L = ol.outline(edges, keys["keys"], half, unit)
        open_pts = decimate([tuple(p) for p in ops[half]])
        # R3: the plate must cover the opening (no sight-line into the cavity):
        # every opening vertex sits at least plate_inset+0.1 inboard
        oclr = min(ol.dist_to_poly(out_pts, p) for p in open_pts)
        assert oclr >= D["plate"]["inset_mm"] + 0.1,             f"{half} opening {oclr:.2f} mm from outline (< plate inset + 0.1)"
        cav_pts, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                 inset=D["case"]["wall_t_mm"])
        cav1_pts, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                  inset=D["case"]["wall_t_mm"] + 1.0)
        plate_pts, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                   inset=D["plate"]["inset_mm"])
        pcb_pts, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                 inset=D["pcb"]["inset_mm"])
        hks = [k for k in keys["keys"] if k["half"] == half and not k.get("virtual")]

        i_idx = next(i for i, e in enumerate(edges) if e["name"] == "inner")
        n_i, d_i = L[i_idx]
        inner_dir = (-n_i[1], n_i[0])
        seg = (V[i_idx - 1], V[i_idx])
        back_end = max(seg, key=lambda p: p[1])
        anchor = next(k for k in hks if k["id"] == D["logo"]["anchor"][half])
        t = (anchor["x_mm"], anchor["y_mm"])
        proj = (t[0] + n_i[0] * (d_i - (n_i[0] * t[0] + n_i[1] * t[1])),
                t[1] + n_i[1] * (d_i - (n_i[0] * t[0] + n_i[1] * t[1])))
        inward = (-n_i[0], -n_i[1])
        e_b = inner_dir if inner_dir[1] > 0 else (-inner_dir[0], -inner_dir[1])
        vertex = (proj[0] + inward[0] * D["logo"]["vertex_inset_mm"]
                        + e_b[0] * D["logo"]["vertex_offset_mm"],
                  proj[1] + inward[1] * D["logo"]["vertex_inset_mm"]
                        + e_b[1] * D["logo"]["vertex_offset_mm"])

        ci = corner_idx[half]
        fc = {role: V[idx] for role, idx in ci.items()}
        g = {"half": half, "outline": out_pts, "inner": (n_i, d_i),
             "vertex": vertex, "corners": fc, "keys": hks, "row_of": get_row}
        geom[half] = g

        # ---- feet positions on the outline inset
        f = D["feet"]
        pad_in, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                  inset=f["front_pad"]["inset_mm"])
        rear_in, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                   inset=f["rear"]["inset_mm"])
        near = lambda poly, p: min(poly, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)
        pad_pts = {"inner": near(pad_in, fc["front_inner"]),
                   "outer": near(pad_in, fc["front_outer"])}
        bar_pts = {"inner": near(rear_in, fc["back_inner"]),
                   "outer": near(rear_in, fc["back_outer"])}
        g["pads"], g["bars"] = pad_pts, bar_pts
        for role, p in pad_pts.items():
            assert ol.dist_to_poly(out_pts, p) >= f["front_pad"]["d_mm"] / 2 - 0.5, \
                f"{half} front pad {role} outside outline"

        # ---- desk plane of the full flat pose (for wedge-cut feet bottoms)
        M_flat = pose_flat_M(g, D, D["poses"]["flat"]["gap_mm"],
                             D["poses"]["flat"]["yaw_deg"])
        n_d, c_d = desk_plane(M_flat)
        dz = lambda x, y: (c_d - n_d[0] * x - n_d[1] * y) / n_d[2]
        pad_h = f["front_pad"]["h_mm"]
        for role, p in pad_pts.items():
            ring = [(p[0] + f["front_pad"]["d_mm"] / 2 * math.cos(2 * math.pi * i / 24),
                     p[1] + f["front_pad"]["d_mm"] / 2 * math.sin(2 * math.pi * i / 24))
                    for i in range(24)]
            verts = [(x, y, 0.0) for x, y in ring] + [(x, y, dz(x, y)) for x, y in ring]
            m24 = len(ring)
            faces = [tuple(range(m24)), tuple(reversed(range(m24, 2 * m24)))]
            faces += [(i, (i + 1) % m24, (i + 1) % m24 + m24, i + m24) for i in range(m24)]
            ob = new_obj(f"{half}_pad_{role}", verts, faces, coll,
                         mats[f["front_pad"]["material"]])
            recalc_normals(ob.data)
        bw, bd = f["rear"]["size_mm"]
        adir = (Vector((*pad_pts["inner"], 0)) - Vector((*pad_pts["outer"], 0)))
        adir = (adir / adir.length) if adir.length > 1 else Vector((1, 0, 0))
        perp = Vector((-adir[1], adir[0], 0))
        cx0 = sum(p[0] for p in out_pts) / len(out_pts)
        cy0 = sum(p[1] for p in out_pts) / len(out_pts)
        for role, p in bar_pts.items():
            px, py = p
            for _ in range(40):                       # slide inward until it fits
                cnr = [(px + adir[0] * bw / 2 * sx + perp[0] * bd / 2 * sy,
                        py + adir[1] * bw / 2 * sx + perp[1] * bd / 2 * sy)
                       for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                if all(ol.point_in(out_pts, cpt) for cpt in cnr):
                    break
                px += (cx0 - px) * 0.08
                py += (cy0 - py) * 0.08
            else:
                raise AssertionError(f"{half} rear bar {role} cannot fit outline")
            bar_pts[role] = (px, py)
            verts = [(x, y, 0.0) for x, y in cnr] + [(x, y, dz(x, y)) for x, y in cnr]
            ob = new_obj(f"{half}_bar_{role}", verts,
                         [tuple(range(4)), tuple(reversed(range(4, 8)))] +
                         [(i, (i + 1) % 4, (i + 1) % 4 + 4, i + 4) for i in range(4)],
                         coll, mats[f["rear"]["material"]])
            recalc_normals(ob.data)
        g["bar_h"] = -dz(*bar_pts["outer"])
        logs.append(f"{half} rear bar height {g['bar_h']:.2f} mm")

        # ---- frost shell
        bt, hh = D["case"]["bottom_t_mm"], D["case"]["height_mm"]
        lip = D["case"]["lip_bottom_z_mm"]
        seam_z = D["case"]["lower_base"]["seam_z_mm"]
        shell = prism(f"{half}_shell", out_pts, seam_z, hh, coll, mats["frost_acrylic"])
        bool_diff(shell, prism(f"{half}_c_open", open_pts, lip, hh + 0.1, colls["Cut"]))
        bool_diff(shell, prism(f"{half}_c_cav", cav_pts, seam_z - 0.1, lip, colls["Cut"]))

        # ---- USB-C on the inner edge
        u = D["internals"]["usb_c"]
        other = seg[0] if seg[1] == back_end else seg[1]
        along = Vector((other[0] - back_end[0], other[1] - back_end[1])).normalized()
        port_c = Vector(back_end) + along * u["from_back_mm"]
        g["usb_port_c"] = port_c                      # for raycast_ports.py
        stad = rounded_rect(u["opening_mm"][0], u["opening_mm"][1],
                            min(u["r_mm"], u["opening_mm"][1] / 2), 4)
        nn = len(stad)
        nvec = Vector((n_i[0], n_i[1]))
        cverts = []
        # G6: cutter must cross the whole wall (was +-3 on a 4 mm wall -> blind dimple)
        for dpt in (-(D["case"]["wall_t_mm"] + 1.5), 3.0):
            for sx, sy in stad:
                p = port_c + along * sx + nvec * dpt
                cverts.append((p.x, p.y, u["z_mm"] + sy))
        cfaces = [tuple(reversed(range(nn))), tuple(range(nn, 2 * nn))]
        cfaces += [(i, (i + 1) % nn, (i + 1) % nn + nn, i + nn) for i in range(nn)]
        bool_diff(shell, new_obj(f"{half}_c_usb", cverts, cfaces, colls["Cut"]))
        # H7: hollow receptacle ring recessed behind the wall face
        dep = 4.5
        front = port_c - nvec * u["recess_mm"]
        o_pts = rounded_rect(u["shell_mm"][0], u["shell_mm"][1],
                             min(1.4, u["shell_mm"][1] / 2), 4)
        i_pts = rounded_rect(u["shell_mm"][0] - 0.6, u["shell_mm"][1] - 0.6,
                             min(1.1, (u["shell_mm"][1] - 0.6) / 2), 4)
        def _ring_v(sx, sy, d):
            p = front + along * sx + nvec * d
            return (p.x, p.y, u["z_mm"] + sy)
        stadium_ring(f"{half}_usb_shell", o_pts, i_pts, 0.0, -dep,
                     _ring_v, coll, mats[u["material_shell"]])
        iverts = []
        for sx, sy in rounded_rect(u["opening_mm"][0] - 0.5, u["opening_mm"][1] - 0.5,
                                   1.2, 3):
            p = front + along * sx - nvec * (dep + 0.05)
            iverts.append((p.x, p.y, u["z_mm"] + sy))
        new_obj(f"{half}_usb_dark", iverts, [tuple(range(len(iverts)))], coll,
                mats["usb_dark"])
        tp = rounded_rect(6.7, 0.7, 0.3, 3)
        tverts = []
        for dpt in (-1.0, -3.0):
            for sx, sy in tp:
                p = front + along * sx + nvec * dpt
                tverts.append((p.x, p.y, u["z_mm"] + sy))
        ntp = len(tp)
        tfaces = [tuple(reversed(range(ntp))), tuple(range(ntp, 2 * ntp))]
        tfaces += [(i, (i + 1) % ntp, (i + 1) % ntp + ntp, i + ntp) for i in range(ntp)]
        new_obj(f"{half}_usb_tongue", tverts, tfaces, coll, mats["pom_white"])

        # ---- clear bottom (leg pocket cut after the leg is sized, below)
        profile = rev2_case.create_lower_base(half, out_pts, D, keys, coll, mats, sys.modules[__name__], desk_z=dz)
        bottom = prism(f"{half}_bottom", profile["floor_outline"], 0.0, bt, coll, mats["clear_acrylic"])
        flat_shade(bottom)
        derived[f"{half}_lower_profile"] = profile["profile"]
        # Thin clear floor follows the underside desk plane inside the tapered skirt.
        for v in bottom.data.vertices:
            x,y=v.co.x/MM,v.co.y/MM
            v.co.z=(profile["bottom_z"]((x,y))+v.co.z/MM)*MM
        # Rubber contacts sit in the lower case; avoid tall stand-in rear pillars.
        for ob in coll.objects:
            if ob.name.startswith((f"{half}_pad_",f"{half}_bar_")):
                for v in ob.data.vertices:
                    x,y=v.co.x/MM,v.co.y/MM
                    v.co.z=(profile["bottom_z"]((x,y))+D["feet"]["front_pad"]["h_mm"] if abs(v.co.z)<1e-8 else dz(x,y))*MM

        # ---- plate + switch holes, pcb
        plate = prism(f"{half}_plate", plate_pts, D["stack"]["plate_z"][0],
                      D["stack"]["plate_z"][1], coll, mats[D["plate"]["material"]])
        hw = D["plate"]["switch_hole_mm"] / 2
        hverts, hfaces = [], []
        for k in hks:
            a = RAD(k["rot_deg"]); c, s = math.cos(a), math.sin(a)
            bi = len(hverts)
            for zz in (D["stack"]["plate_z"][0] - 0.4, D["stack"]["plate_z"][1] + 0.4):
                for x, y in ((-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)):
                    hverts.append((k["x_mm"] + c * x - s * y,
                                   k["y_mm"] + s * x + c * y, zz))
            hfaces += [(bi, bi + 1, bi + 2, bi + 3), (bi + 7, bi + 6, bi + 5, bi + 4),
                       (bi, bi + 4, bi + 5, bi + 1), (bi + 1, bi + 5, bi + 6, bi + 2),
                       (bi + 2, bi + 6, bi + 7, bi + 3), (bi + 3, bi + 7, bi + 4, bi)]
        bool_diff(plate, new_obj(f"{half}_c_holes", hverts, hfaces, colls["Cut"]))
        pcb = prism(f"{half}_pcb", pcb_pts, D["stack"]["pcb_z"][0],
              D["stack"]["pcb_z"][1], coll, mats[D["pcb"]["material"]])

        # ---- internals
        rf = D["internals"]["rf_module"]
        rfp = rf[half]
        rf_w, rf_d = rf["size_mm"]
        box(f"{half}_rf", rfp["xy"][0], rfp["xy"][1],
            D["stack"]["rf_module_z"][0], D["stack"]["rf_module_z"][1],
            rf_w, rf_d, coll, mats[rf["material"]], rot_z=rfp["rot"])
        ar = RAD(rfp["rot"])
        a_dir = Vector((-math.sin(ar), math.cos(ar)))
        a_c = Vector(rfp["xy"]) + a_dir * (rf_d / 2 + rf["antenna_len_mm"] / 2)
        box(f"{half}_ant", a_c.x, a_c.y,
            D["stack"]["rf_module_z"][0] + 0.4, D["stack"]["rf_module_z"][0] + 0.9,
            rf_w - 3, rf["antenna_len_mm"], coll, mats["antenna_fr4"],
            rot_z=rfp["rot"])
        bat = D["internals"]["battery"]
        bp = bat[half]
        bob = box(f"{half}_batt", bp["xy"][0], bp["xy"][1],
                  D["stack"]["battery_z"][0], D["stack"]["battery_z"][1],
                  bat["size_mm"][0], bat["size_mm"][1], coll, mats[bat["material"]],
                  rot_z=bp["rot"])
        bevel(bob, bat["r_mm"], 2)

        wcfg = D["internals"]["weight"]
        idxs = [i for i, e in enumerate(edges) if 60 <= e["n_deg"] <= 120]
        w_edges = [dict(e) for i, e in enumerate(edges) if not (60 <= e["n_deg"] <= 120)]
        w_edges.insert(idxs[0], {"n_deg": 90, "d": wcfg["back_y_mm"], "r": 25.0,
                                 "keys": "all", "bezel": 0})
        w_pts, _, _ = ol.outline(w_edges, keys["keys"], half, unit,
                                 inset=wcfg["inset_mm"], r_min=wcfg["r_min_mm"])
        wob = prism(f"{half}_weight", w_pts, D["stack"]["weight_z"][0],
                    D["stack"]["weight_z"][1], coll, mats[wcfg["material"]])
        bevel(wob, 1.0, 2)
        flat_shade(wob)   # R4: n-gon bevel normals -> X shading; flat faces

        def rect_pts(cx, cy, w, d, rot):
            a2 = RAD(rot); c2, s2 = math.cos(a2), math.sin(a2)
            return [(cx + c2 * x - s2 * y, cy + s2 * x + c2 * y) for x, y in
                    ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        for name, (cx, cy, w, d, rot) in {
            "rf": (rfp["xy"][0], rfp["xy"][1], rf_w,
                   rf_d + rf["antenna_len_mm"], rfp["rot"]),
            "battery": (bp["xy"][0], bp["xy"][1], *bat["size_mm"], bp["rot"]),
        }.items():
            for p in rect_pts(cx, cy, w, d, rot):
                assert ol.point_in(cav1_pts, p), f"{half} {name} outside cavity: {p}"
        def seg_poly_dist(p, poly):
            return min(point_seg_dist(p, a, b)
                       for a, b in zip(poly, poly[1:] + poly[:1]))
        a_end = Vector(rfp["xy"]) + a_dir * (rf_d / 2 + rf["antenna_len_mm"])
        d_ant = seg_poly_dist(a_end, w_pts)
        assert d_ant >= 10.0, f"{half} weight {d_ant:.1f} mm from RF antenna end (<10)"
        bpts = rect_pts(bp["xy"][0], bp["xy"][1], *bat["size_mm"], bp["rot"])
        d_bat = min(seg_poly_dist(p, w_pts) for p in bpts)
        overlap = any(ol.point_in(w_pts, p) for p in bpts) or \
            any(ol.point_in(bpts, p) for p in w_pts)
        assert not overlap and d_bat > 0.2, f"{half} weight overlaps battery"
        logs.append(f"{half} weight->antenna {d_ant:.1f} mm, weight->battery {d_bat:.1f} mm")

        # ---- case foam: PCB outline between weight/batt top and PCB;
        #      holes for the RF module + antenna and the battery
        fo = D["foam"]
        hc_ = fo["hole_clear_mm"]
        foam_pts, _, _ = ol.outline(edges, keys["keys"], half, unit,
                                    inset=D["pcb"]["inset_mm"])
        foam = prism(f"{half}_foam", foam_pts, fo["z_mm"][0], fo["z_mm"][1],
                     coll, mats[fo["material"]])
        holes = {
            "rf": rect_pts(rfp["xy"][0], rfp["xy"][1], rf_w + 2 * hc_,
                           rf_d + rf["antenna_len_mm"] + 2 * hc_, rfp["rot"]),
            "battery": rect_pts(bp["xy"][0], bp["xy"][1],
                                bat["size_mm"][0] + 2 * hc_,
                                bat["size_mm"][1] + 2 * hc_, bp["rot"]),
        }
        for hname, hpts in holes.items():
            assert all(ol.point_in(foam_pts, p) for p in hpts), \
                f"{half} foam hole {hname} outside outline"
            bool_diff(foam, prism(f"{half}_c_foam_{hname}", hpts,
                                  fo["z_mm"][0] - 0.1, fo["z_mm"][1] + 0.1,
                                  colls["Cut"]))

        # ---- gasket mount tabs: plate-material tabs on the plate edge with
        #      poron pads above + below; spaced by arc length on the plate outline
        gz = D["gasket"]
        tab_w, tab_d = gz["tab_mm"]
        pl_in, pl_out = D["plate"]["inset_mm"], gz["edge_inset_mm"]
        pz0, pz1 = D["stack"]["plate_z"]
        # keep-outs: stab housings + RF module footprint
        keepout = [rect_pts(rfp["xy"][0], rfp["xy"][1], rf_w + 6.0,
                            rf_d + rf["antenna_len_mm"] + 6.0, rfp["rot"])]
        for k in hks:
            if k.get("stab"):
                a3 = RAD(k["rot_deg"]); c3, s3 = math.cos(a3), math.sin(a3)
                sp = D["stab"]["spacing_mm"].get(f"{k['w_u']:g}", 23.8)
                hx, hy, _hz = D["stab"]["housing_mm"]
                for sgn3 in (-1, 1):
                    keepout.append(rect_pts(
                        k["x_mm"] + c3 * (sp / 2 * sgn3),
                        k["y_mm"] + s3 * (sp / 2 * sgn3),
                        hx + 6.0, hy + 6.0, k["rot_deg"]))

        # arc-length walk on the plate outline
        pl = plate_pts + [plate_pts[0]]
        clen = [0.0]
        for p2a, p2b in zip(pl, pl[1:]):
            clen.append(clen[-1] + math.hypot(p2b[0] - p2a[0], p2b[1] - p2a[1]))
        perim = clen[-1]
        n_tab = min(max(round(perim / gz["spacing_mm"]), gz["count_min"]),
                    gz["count_max"])

        def edge_at(s_):
            """point + outward normal on the plate outline at arc pos s_."""
            s_ = s_ % perim
            i = max(0, min(len(clen) - 2,
                           next(j for j, c_ in enumerate(clen) if c_ > s_) - 1))
            t2 = (s_ - clen[i]) / (clen[i + 1] - clen[i])
            pa, pb = pl[i], pl[i + 1]
            pt = (pa[0] + (pb[0] - pa[0]) * t2, pa[1] + (pb[1] - pa[1]) * t2)
            dv = (pb[0] - pa[0], pb[1] - pa[1])
            dl_ = math.hypot(*dv)
            return pt, (dv[1] / dl_, -dv[0] / dl_)   # CCW -> outward = right side

        def tab_poly(s_):
            pt, nrm = edge_at(s_)
            cx2 = pt[0] + nrm[0] * (pl_in - pl_out - tab_d / 2)
            cy2 = pt[1] + nrm[1] * (pl_in - pl_out - tab_d / 2)
            tx_, ty_ = -nrm[1], nrm[0]
            return [(cx2 + tx_ * tab_w / 2 * sx2 + nrm[0] * tab_d / 2 * sy2,
                     cy2 + ty_ * tab_w / 2 * sx2 + nrm[1] * tab_d / 2 * sy2)
                    for sx2 in (-1, 1) for sy2 in (-1, 1)]

        def tab_clear(s_):
            tp2 = tab_poly(s_)
            return min(seg_poly_dist(p, tp2) for kp in keepout for p in kp)

        tab_pos = []
        leaf_centers = []
        for i in range(n_tab):
            s0 = perim * i / n_tab
            best, bs_ = s0, tab_clear(s0)
            for dlt in range(1, 20):                    # nudge along the outline
                for sd_ in (s0 + dlt * 0.5, s0 - dlt * 0.5):
                    c_ = tab_clear(sd_)
                    if c_ > bs_:
                        best, bs_ = sd_, c_
                    if bs_ >= 6.0:
                        break
                if bs_ >= 6.0:
                    break
            assert bs_ >= 0.5, f"{half} gasket tab {i} buried in keepout"
            tab_pos.append(round(best % perim, 2))
            tp2 = tab_poly(best)
            ep,en=edge_at(best)
            inboard=D['gasket']['leaf_mount']['station_inboard_mm']
            leaf_centers.append({"xy":(ep[0]-en[0]*inboard,ep[1]-en[1]*inboard),"normal":en,"tangent":(-en[1],en[0])})
            # Retain a small PP mounting tongue at the plate edge.
            center=(sum(p[0] for p in tp2)/4,sum(p[1] for p in tp2)/4)
            tp2=sorted(tp2,key=lambda p:math.atan2(p[1]-center[1],p[0]-center[0]))
            prism(f"{half}_gasket{i}",tp2,pz0,pz1,coll,mats[D["plate"]["material"]])
        mounts=rev2_case.add_leaf_mount(half,leaf_centers,D,coll,mats,sys.modules[__name__])
        derived[f"{half}_leaf_stations"]=[{"xy_mm":m["xy_mm"],"normal":m["normal"],"tangent":m["tangent"]} for m in mounts]
        derived[f"{half}_pcb_flex_slots"]=rev2_case.cut_pcb_flex(pcb,half,leaf_centers,D,colls["Cut"],sys.modules[__name__])
        logs.append(f"{half} gasket tabs {n_tab} at {tab_pos}, "
                    f"min keepout clearance {bs_:.1f} mm")
        derived[f"{half}_gasket_arc_mm"] = tab_pos

        # ---- switches, stabs, caps
        n_leg = 0
        sh = D["switch"]
        cap_bottom_z = D["stack"]["cap_bottom_z"]
        for k in hks:
            kid = k["id"]
            a = RAD(k["rot_deg"]); c, s = math.cos(a), math.sin(a)
            box(f"{half}_{kid}_swb", k["x_mm"], k["y_mm"],
                D["stack"]["pcb_z"][1], D["stack"]["plate_z"][1],
                sh["bottom_w_mm"], sh["bottom_w_mm"], coll,
                mats[sh["material_housing"]], rot_z=k["rot_deg"])
            tb, (tx, ty), th = sh["top_base_mm"], sh["top_top_mm"], sh["top_h_mm"]
            fr = []
            for x, y, z in ((-tb / 2, -tb / 2, 0), (tb / 2, -tb / 2, 0), (tb / 2, tb / 2, 0),
                            (-tb / 2, tb / 2, 0), (-tx / 2, -ty / 2, th), (tx / 2, -ty / 2, th),
                            (tx / 2, ty / 2, th), (-tx / 2, ty / 2, th)):
                fr.append((k["x_mm"] + c * x - s * y, k["y_mm"] + s * x + c * y,
                           D["stack"]["plate_z"][1] + z))
            new_obj(f"{half}_{kid}_swt", fr,
                    [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                     (2, 6, 7, 3), (3, 7, 4, 0)], coll, mats[sh["material_housing"]])
            sx, sy, shz = sh["stem_mm"]
            box(f"{half}_{kid}_stem", k["x_mm"], k["y_mm"],
                D["stack"]["plate_z"][1] + th, D["stack"]["plate_z"][1] + th + shz,
                sx, sy, coll, mats[sh["material_stem"]], rot_z=k["rot_deg"])
            if k.get("stab"):
                sp = D["stab"]["spacing_mm"].get(f"{k['w_u']:g}", 23.8)
                hx, hy, hz = D["stab"]["housing_mm"]
                for sgn3 in (-1, 1):
                    box(f"{half}_{kid}_stab{sgn3}",
                        k["x_mm"] + c * (sp / 2 * sgn3), k["y_mm"] + s * (sp / 2 * sgn3),
                        D["stack"]["plate_z"][1], D["stack"]["plate_z"][1] + hz,
                        hx, hy, coll, mats[D["stab"]["material"]], rot_z=k["rot_deg"])
                wy = D["stab"]["wire_y_mm"]
                p1 = (k["x_mm"] + c * (-sp / 2) - s * wy, k["y_mm"] + s * (-sp / 2) + c * wy)
                p2 = (k["x_mm"] + c * (sp / 2) - s * wy, k["y_mm"] + s * (sp / 2) + c * wy)
                ribbon(f"{half}_{kid}_wire", [p1, p2], D["stab"]["wire_d_mm"],
                       D["stack"]["plate_z"][1] + 1.5,
                       D["stack"]["plate_z"][1] + 1.5 + D["stab"]["wire_d_mm"],
                       coll, mats[D["stab"]["wire_material"]], end_discs=False)

            row = get_row(k["label"])
            rcfg = D["keycap"]["rows"][row]
            key_cm = (k["w_u"], row)
            if key_cm not in cap_meshes:
                cap_meshes[key_cm] = rev2_keycaps.build_cap_mesh(f"cap_{row}_{k['w_u']:g}", k["w_u"], rcfg, kc, sys.modules[__name__])
                cap_meshes[key_cm].materials.append(mats[kc["material"]])
            cap = bpy.data.objects.new(f"{half}_{kid}_cap", cap_meshes[key_cm])
            coll.objects.link(cap)
            cap.location = (k["x_mm"] * MM, k["y_mm"] * MM, cap_bottom_z * MM)
            cap.rotation_euler.z = a
            rev2_keycaps.add_details(cap,k,rcfg,kc,mats,coll,fonts,sys.modules[__name__])
            if kc["legend"].get("text", {}).get(k["label"], k["label"]) != "":
                n_leg += 1

        # Full variant C inlay on the right arrow shoulder.
        lg = D["logo"]
        clr = 0.0
        if half == "R":
            lx, ly = ol.logo_xy(D, keys)
            top = hh + lg["proud_mm"]
            clearances = []
            for side in (-1, 1):
                world_pts = [(lx + px, ly + py) for px, py in wing_pts(D, side, lg["wing_span_mm"])]
                assert all(ol.point_in(out_pts, p) and not ol.point_in(open_pts, p) for p in world_pts), "Right gull must sit on solid top"
                ribbon(f"R_gull{'L' if side < 0 else 'R'}_groove", world_pts,
                       lg["stroke_mm"] + lg["groove_margin_mm"], top - lg["inlay_depth_mm"] - lg["groove_depth_mm"],
                       top - lg["groove_recess_mm"], coll, mats["black_glass"])
                ribbon(f"R_gull{'L' if side < 0 else 'R'}", world_pts, lg["stroke_mm"],
                       top - lg["inlay_depth_mm"], top, coll, mats[lg["material"]])
                clearances.append(min(min(ol.dist_to_poly(open_pts,p),ol.dist_to_poly(out_pts,p)) for p in world_pts) - lg["stroke_mm"] / 2)
            clr = min(clearances)
            assert clr >= lg["min_clear_to_opening_mm"], f"Right gull edge clearance {clr:.2f} mm"
            derived["right_gull_vertex_mm"] = [lx, ly, top]
        logs.append(f"{half} full gull clearance {clr:.2f} mm, legends {n_leg}")
        # Keyboard knob follows encoders[] in the layout.
        kxy = ol.knob_xy(D, keys)
        if kxy and kxy[0] == half:
            kb = D["knob_kb"]
            kstyle = dict(D["hub"]["knob"], d_mm=kb["d_mm"])
            disc(f"{half}_knob_enc", kxy[1], kxy[2], D["stack"]["plate_z"][1],
                 hh + kb["z_gap_mm"] - 0.2, 6.0, coll, mats["rf_can"], seg=24)
            kob = knob_mesh(f"{half}_knob", kstyle, mats[kstyle["material"]], coll)
            kob.location = (kxy[1] * MM, kxy[2] * MM, (hh + kb["z_gap_mm"]) * MM)
            logs.append(f"{half} knob at ({kxy[1]:.1f}, {kxy[2]:.1f}) mm, d {kb['d_mm']}")
        g["logo_clear"] = clr
        g["open_pts"] = open_pts
        g["anchor_proj"] = proj
        g["inward"] = inward
        g["e_back"] = e_b

        g["link_bases"], g["u_bases"] = {}, {}
        g["u_center_mm"] = 0.0
        if D["tent"].get("enabled", True):
            # ---- tent U-frame: flat bar + arms + skewed hinge + over-centre links.
            # The case keeps its 6 deg typing slope, so the hinge line is skewed in
            # the pocket plane (front arm shorter, back longer, mean = arm_len_mm);
            # phi + arm lengths are solved so BOTH bar-end corners touch the desk.
            tc = D["tent"]; uf = tc["u_frame"]
            oi = [i for i, e in enumerate(edges)
                  if e["name"] in uf["outer_edges"][half]]
            ie = min(oi, key=lambda i: L[i][1])            # innermost edge line
            n_out, d_edge = L[ie]
            tdir = Vector((-n_out[1], n_out[0]))            # tangent along the edge
            cy = uf["center_mm"][half]
            W = uf["width_mm"]                              # bar length along edge
            PW, T = uf["profile_mm"]                        # bar width x thickness
            AL, EI = uf["arm_len_mm"], uf["edge_inset_mm"]  # AL = mean arm length
            pk = uf["pocket_clear_mm"]
            bw2, iw2 = W / 2, W / 2 - PW                     # 35, 27 for 70/8
            # hinge frame: x' along the edge (t_dir), y' outward (n_out), z' up.
            # frame origin at the nominal hinge line (EI + AL inboard of the edge).
            H0 = (n_out[0] * (d_edge - EI - AL) + tdir.x * cy,
                  n_out[1] * (d_edge - EI - AL) + tdir.y * cy)
            A4 = Matrix((Vector((tdir.x, tdir.y, 0)),
                         Vector((n_out[0], n_out[1], 0)),
                         Vector((0, 0, 1)))).transposed().to_4x4()
            def hc(px, py):
                """hinge-frame mm -> case-frame mm (z=0 plane)."""
                return Vector((H0[0] + tdir.x * px + n_out[0] * py,
                               H0[1] + tdir.y * px + n_out[1] * py))
            def h3(px, py, pz=0.0):
                return Vector((hc(px, py).x, hc(px, py).y, pz))
            xarm = bw2 - PW / 2                              # 31: arm centrelines
            x_f = xarm if tdir.y < 0 else -xarm              # front arm centreline
            x_b = -x_f

            M_tent = roll_M(g, D,
                            pose_flat_M(g, D, D["poses"]["tented"]["gap_mm"], 0.0),
                            RAD(tc["angle_deg"]))

            # hinge axis through the arm-end hinge points; arm length a_s puts the
            # hinge point at y' = AL - a_s on the arm centreline
            def axis_pts(a_f, a_b):
                Hf = h3(x_f, AL - a_f)
                Hb = h3(x_b, AL - a_b)
                return Hf, (Hb - Hf).normalized()

            def end_z(a_f, a_b, th):
                """world z of both bar-end bottom-outer corners after deploy."""
                Hf, u3 = axis_pts(a_f, a_b)
                R = Matrix.Rotation(th, 4, u3)
                out = []
                for xe in (x_f + PW / 2 * (1 if tdir.y < 0 else -1),
                           x_b - PW / 2 * (1 if tdir.y < 0 else -1)):
                    P = h3(xe, AL)
                    out.append((M_tent @ (Hf + R @ (P - Hf))).z)
                return out

            sgn = 1.0 if sum(end_z(AL, AL, RAD(1.0))) < \
                         sum(end_z(AL, AL, 0.0)) else -1.0

            def solve_phi(af_):
                """bisect deploy angle so the FRONT bar end touches the desk."""
                lo, hi = 0.0, RAD(85)
                for _ in range(45):
                    mid = (lo + hi) / 2
                    if front_z(af_, sgn * mid) > 0:
                        lo = mid
                    else:
                        hi = mid
                return sgn * (lo + hi) / 2

            def front_z(af_, th_):
                return end_z(af_, 2 * AL - af_, th_)[0]
            def back_z(af_, th_):
                return end_z(af_, 2 * AL - af_, th_)[1]

            lo_a, hi_a = AL * 0.5, AL                     # front arm shorter
            for _ in range(45):
                amid = (lo_a + hi_a) / 2
                th_ = solve_phi(amid)
                if back_z(amid, th_) > 0:
                    hi_a = amid   # back floats -> smaller a_f -> longer back arm
                else:
                    lo_a = amid
            a_f = (lo_a + hi_a) / 2
            a_b = 2 * AL - a_f
            th = solve_phi(a_f)
            zf, zb = end_z(a_f, a_b, th)
            assert abs(zf) < 0.05 and abs(zb) < 0.05, \
                f"{half} U bar ends off desk: {zf:.3f}/{zb:.3f} mm"
            g["u_theta"], g["u_arms"] = th, (a_f, a_b)
            skew = math.degrees(math.atan((a_b - a_f) / (2 * xarm)))
            logs.append(f"{half} U-frame arms front {a_f:.1f} / back {a_b:.1f} mm, "
                        f"hinge skew {skew:.1f} deg, phi {math.degrees(th):.1f} deg, "
                        f"desk contact z {zf:.3f}/{zb:.3f} mm")

            # in the tented pose the OUTER feet must be off the desk
            pad_h = D["feet"]["front_pad"]["h_mm"]
            z_po = (M_tent @ Vector((*g["pads"]["outer"], -pad_h))).z
            z_bo = (M_tent @ Vector((*g["bars"]["outer"], -g["bar_h"]))).z
            assert z_po > 0.05 and z_bo > 0.05, \
                f"{half} outer foot touches desk in tent pose ({z_po:.2f}/{z_bo:.2f})"

            # hinge-side height of the U profile at x' (arm ends follow the skew)
            def yh(x2):
                return AL - (a_f + (a_b - a_f) * (x2 - x_f) / (x_b - x_f))

            # deploy transform: rotate about the skewed axis. Prot_mm works on mm
            # points (link pivots); Prot on metre-space object bases (mesh verts
            # are metres after new_obj's V3 scaling).
            Hf3, u3 = axis_pts(a_f, a_b)
            Prot_mm = (Matrix.Translation(Hf3) @ Matrix.Rotation(th, 4, u3)
                       @ Matrix.Translation(-Hf3))
            Prot = (Matrix.Translation(V3(Hf3)) @ Matrix.Rotation(th, 4, u3)
                    @ Matrix.Translation(
                        (-Hf3.x * MM, -Hf3.y * MM, -Hf3.z * MM)))
            B0 = Matrix.Translation(Vector((H0[0] * MM, H0[1] * MM, 0.0))) @ A4
            dep_b = Prot @ B0
            g["u_bases"] = {}

            # U polygon: bar band + arms; hinge side follows the skewed line
            cr = uf["corner_r_mm"]
            arc = [(iw2 - cr + cr * math.cos(math.pi / 2 * j / 4),
                    AL - PW - cr + cr * math.sin(math.pi / 2 * j / 4))
                   for j in range(5)]
            arc2 = [(-x, y) for x, y in reversed(arc)]
            upoly = ([(-bw2, yh(-bw2)), (-bw2, AL), (bw2, AL),
                      (bw2, yh(bw2)), (iw2, yh(iw2)), (iw2, AL - PW - cr)]
                     + arc + arc2
                     + [(-iw2, yh(-iw2))])
            uverts = [(p[0], p[1], 0.0) for p in upoly] + \
                     [(p[0], p[1], T) for p in upoly]
            nn = len(upoly)
            ufaces = [tuple(reversed(range(nn))), tuple(range(nn, 2 * nn))]
            ufaces += [(i, (i + 1) % nn, (i + 1) % nn + nn, i + nn)
                       for i in range(nn)]
            uob = new_obj(f"{half}_u_frame", uverts, ufaces, coll,
                          mats[uf["material"]])
            recalc_normals(uob.data)
            flat_shade(uob)     # R4
            uob.matrix_basis = B0
            g["u_bases"][uob.name] = (B0.copy(), dep_b.copy())

            # hinge knuckles on the skewed axis at each arm end
            ux2, uy2 = x_b - x_f, yh(x_b) - yh(x_f)
            ul2 = math.hypot(ux2, uy2)
            uax = (ux2 / ul2, uy2 / ul2)
            for si, xs2 in enumerate((-xarm, xarm)):
                ys2 = yh(xs2)
                ring = [(T / 2 * math.cos(2 * math.pi * j / 12),
                         T / 2 * math.sin(2 * math.pi * j / 12)) for j in range(12)]
                kverts = []
                for ds2 in (-PW / 2, PW / 2):
                    for ry2, rz2 in ring:
                        kverts.append((xs2 + uax[0] * ds2 - uax[1] * ry2,
                                       ys2 + uax[1] * ds2 + uax[0] * ry2,
                                       T / 2 + rz2))
                nk = len(ring)
                kfaces = [tuple(reversed(range(nk))), tuple(range(nk, 2 * nk))]
                kfaces += [(i, (i + 1) % nk, (i + 1) % nk + nk, i + nk)
                           for i in range(nk)]
                kob = new_obj(f"{half}_u_kn{si}", kverts, kfaces, coll,
                              mats[uf["material"]])
                kob.matrix_basis = B0
                g["u_bases"][kob.name] = (B0.copy(), dep_b.copy())

            # over-centre stay per arm: pivot at 0.6 * arm length from the hinge
            lw, lt = uf["link_mm"]
            off_lat = PW / 2 + lw / 2 + 0.5                  # inner side of the arm
            g["link_bases"] = {}
            t3 = Vector((tdir.x, tdir.y, 0.0))               # hinge x' dir in case

            def link_basis(p0c, p1c):
                """basis for a link spanning case-frame mm points p0c -> p1c."""
                u_ = p1c - p0c
                u_.normalize()
                w_ = t3.copy()
                v_ = u_.cross(w_).normalized()
                w_ = u_.cross(v_).normalized()
                L4 = Matrix((u_, v_, w_)).transposed().to_4x4()
                return Matrix.Translation(V3((p0c + p1c) / 2)) @ L4

            for sgn2, xs2 in ((-1, -xarm), (1, xarm)):
                a_s = a_f if xs2 == x_f else a_b
                xlk = xs2 - sgn2 * off_lat
                ypv = yh(xs2) + uf["link_pos_frac"] * a_s
                Pc = h3(xlk, ypv, T / 2)
                Pa = Prot_mm @ Pc                            # arm pivot rides the U
                chord = (Pa - Pc).length
                l = chord / 2 / math.cos(RAD(uf["over_center_deg"]))
                dl = Pa - Pc
                perp = dl.cross(t3)
                if perp.length < 1e-9:
                    perp = Vector((0.0, 0.0, 1.0))
                perp.normalize()
                K = (Pc + Pa) / 2 + perp * (l * math.sin(RAD(uf["over_center_deg"])))
                if K.z < (Pc.z + Pa.z) / 2:
                    K = (Pc + Pa) / 2 - perp * (l * math.sin(RAD(uf["over_center_deg"])))
                lv = [(sx2 * l / 2, sy2 * lw / 2, sz2 * lt / 2)
                      for sx2 in (-1, 1) for sy2 in (-1, 1) for sz2 in (-1, 1)]
                lf = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                      (0, 2, 6, 4), (1, 5, 7, 3)]
                p_stow = [(h3(xlk, ypv, lt / 2), h3(xlk, ypv - l, lt / 2)),
                          (h3(xlk + sgn2 * lt, ypv, lt * 1.5),
                           h3(xlk + sgn2 * lt, ypv - l, lt * 1.5))]
                for li, (p0, p1) in enumerate(((Pc, K), (K, Pa))):
                    lob = new_obj(f"{half}_ulink{sgn2}{li}", lv, lf, coll,
                                  mats["stainless_polished"])
                    recalc_normals(lob.data)
                    st_b, dp_b = link_basis(*p_stow[li]), link_basis(p0, p1)
                    lob.matrix_basis = st_b
                    g["link_bases"][lob.name] = (st_b, dp_b)
                derived[f"{half}_u_link_{'front' if xs2 == x_f else 'back'}_mm"] = \
                    round(l, 2)

            # pocket through the clear bottom = offset U footprint + link corridors
            hb = T * abs(math.sin(th)) + 0.2 + pk            # swing clearance

            def offset_poly(pts, dists):
                """offset each edge outward (right of CCW winding), miter corners."""
                n2 = len(pts)
                ar = sum(pts[i][0] * pts[(i + 1) % n2][1] -
                         pts[(i + 1) % n2][0] * pts[i][1] for i in range(n2)) / 2
                s2 = 1.0 if ar > 0 else -1.0
                keep = []
                for i in range(n2):
                    a2, b2 = pts[i], pts[(i + 1) % n2]
                    if math.hypot(b2[0] - a2[0], b2[1] - a2[1]) >= 1e-9:
                        keep.append(i)
                pts = [pts[i] for i in keep]
                dists = [dists[i] for i in keep]
                n2 = len(pts)
                lines = []
                for i in range(n2):
                    a2, b2 = pts[i], pts[(i + 1) % n2]
                    dx, dy = b2[0] - a2[0], b2[1] - a2[1]
                    dl2 = math.hypot(dx, dy)
                    nx, ny = s2 * dy / dl2, -s2 * dx / dl2
                    d_ = dists[i]
                    lines.append(((a2[0] + nx * d_, a2[1] + ny * d_),
                                  (b2[0] + nx * d_, b2[1] + ny * d_)))
                out2 = []
                for i in range(n2):
                    (a1, b1), (a2, b2) = lines[(i - 1) % n2], lines[i]
                    d1x, d1y = b1[0] - a1[0], b1[1] - a1[1]
                    d2x, d2y = b2[0] - a2[0], b2[1] - a2[1]
                    den = d1x * d2y - d1y * d2x
                    if abs(den) < 1e-9:
                        out2.append(b1)
                        continue
                    tt = ((a2[0] - a1[0]) * d2y - (a2[1] - a1[1]) * d2x) / den
                    out2.append((a1[0] + d1x * tt, a1[1] + d1y * tt))
                return out2

            nd = len(upoly)
            dists = []
            for i in range(nd):
                a2, b2 = upoly[i], upoly[(i + 1) % nd]
                my, mx = (a2[1] + b2[1]) / 2, (a2[0] + b2[0]) / 2
                hinge_side = my < min(yh(-bw2), yh(bw2)) + 2 and abs(mx) > iw2 - 1
                dists.append(hb if hinge_side else pk)
            pkc = [(hc(px, py).x, hc(px, py).y)
                   for px, py in offset_poly(upoly, dists)]

            # link corridors beside each arm (rect cutters, overlap the U pocket)
            for sgn2, xs2 in ((-1, -xarm), (1, xarm)):
                xlk = xs2 - sgn2 * off_lat
                xlo = min(xlk - lw / 2 - pk, xs2 - PW / 2 - pk)
                xhi = max(xlk + lw / 2 + pk, xs2 + PW / 2 + pk)
                crd = [(hc(xlo, yh(xlo) - hb).x, hc(xlo, yh(xlo) - hb).y),
                       (hc(xhi, yh(xhi) - hb).x, hc(xhi, yh(xhi) - hb).y),
                       (hc(xhi, AL - PW + pk).x, hc(xhi, AL - PW + pk).y),
                       (hc(xlo, AL - PW + pk).x, hc(xlo, AL - PW + pk).y)]
                pkc += crd
                bool_diff(bottom, prism(f"{half}_c_pocket_l{sgn2}", crd,
                                        -0.2, bt + 0.2, colls["Cut"]))
            assert all(ol.point_in(out_pts, p) for p in pkc) and \
                min(ol.dist_to_poly(out_pts, p) for p in pkc) >= 2.0, \
                f"{half} U-pocket outside outline"
            for p_name, fp, hw, hh in (("pad", g["pads"]["outer"], 5.0, 5.0),
                                       ("bar", g["bars"]["outer"], 14.0, 4.0)):
                cnr = [(fp[0] + hw * sx2, fp[1] + hh * sy2)
                       for sx2 in (-1, 1) for sy2 in (-1, 1)]
                md = min(ol.dist_to_poly(pkc, p) for p in cnr)
                inside = any(ol.point_in(pkc, p) for p in cnr) or \
                    any(ol.point_in(cnr, p) for p in pkc)
                logs.append(f"{half} pocket->{p_name} clearance {md:.2f} mm")
                assert not inside and md >= 0.8, \
                    f"{half} U-pocket overlaps outer {p_name} ({md:.2f})"
            bool_diff(bottom, prism(f"{half}_c_pocket", pkc, -0.2, bt + 0.2,
                                    colls["Cut"]))
            g["u_center_mm"] = cy
            derived[f"{half}_u_deploy_deg"] = round(math.degrees(th), 2)
            derived[f"{half}_u_arms_mm"] = [round(a_f, 2), round(a_b, 2)]
            derived[f"{half}_u_skew_deg"] = round(skew, 2)

        bevel(shell, D["case"]["edge_fillet_mm"], 3)
        bevel(bottom, D["case"]["edge_fillet_mm"], 3)

        root = bpy.data.objects.new(f"{half}_root", None)
        scene_coll.objects.link(root)
        for ob in list(coll.objects):
            if ob.parent is None and ob != root:
                ob.parent = root
        g["root"] = root

        xs = [p[0] for p in out_pts]; ys = [p[1] for p in out_pts]
        derived[f"{half}_size_mm"] = [round(max(xs) - min(xs), 2),
                                     round(max(ys) - min(ys), 2)]
        derived[f"{half}_rear_bar_h_mm"] = round(g["bar_h"], 2)
        derived[f"{half}_logo_clear_mm"] = round(clr, 2)
        derived[f"{half}_u_center_mm"] = g["u_center_mm"]
        # store un-posed bases so set_pose can restore/explode layers
        g["basis0"] = {ob.name: ob.matrix_basis.copy() for ob in coll.objects}

    build_hub(D, mats, colls["Hub"], colls["Cut"], scene_coll, geom)
    build_studio(D, mats, colls["Studio"])

    # ---- exploded view: classify every mesh/object into exactly one layer,
    #      compute per-layer z offsets so consecutive layer bboxes clear by gap
    import re
    ex = D["explode"]
    gap = ex["gap_mm"]

    def classify(coll_name):
        lmap = ex["layers"]["L|R" if coll_name in ("L", "R") else "Hub"]
        out = {}
        for ob in colls[coll_name].all_objects:
            if ob.name.endswith("_root"):
                continue
            hits = [ly for ly, pat in lmap.items() if re.search(pat, ob.name)]
            if ob.type == 'MESH':
                assert len(hits) == 1, \
                    f"{coll_name}/{ob.name} maps to layers {hits} (need exactly 1)"
            elif not hits:
                hits = ["u_frame"] if "_u_" in ob.name else []
            if hits:
                out[ob.name] = hits[0]
        return out

    bpy.context.view_layer.update()

    def layer_extent(coll_name, layer_objs):
        """z extent (mm, build frame) over every object mapped to the layer,
        including children of mapped empties."""
        lo, hi = 1e9, -1e9
        for ob in colls[coll_name].all_objects:
            if layer_objs.get(ob.name) is None:
                continue
            Meff = ob.matrix_world.copy()     # roots are identity at build time
            if ob.type == 'MESH':
                for c2 in ob.bound_box:
                    z2 = (Meff @ Vector(c2)).z / MM
                    lo, hi = min(lo, z2), max(hi, z2)
            else:
                lo, hi = min(lo, Meff.translation.z / MM), \
                    max(hi, Meff.translation.z / MM)
        return lo, hi

    ex_off = {}
    for coll_name, order in (("L", ex["order_bottom_to_top"]),
                             ("R", ex["order_bottom_to_top"]),
                             ("Hub", ex["hub_order"])):
        amap = classify(coll_name)
        by_layer = {}
        for nm, ly in amap.items():
            by_layer.setdefault(ly, {})[nm] = True
        tops = [o for o in colls[coll_name].all_objects
                if o.parent is None or o.parent.name.endswith("_root")]
        top_layer = {o.name: amap[o.name] for o in tops if o.name in amap}
        offs = {}
        cur_top = None
        for ly in order:
            lo, hi = layer_extent(coll_name, by_layer.get(ly, {}))
            if cur_top is None:
                off = 0.0
            else:
                off = cur_top + gap - lo
            cur_top = hi + off
            for nm in by_layer.get(ly, {}):
                if nm in top_layer:
                    offs[nm] = off
        ex_off[coll_name] = {ly: round(cur_top - hi + off, 1) and round(off, 1)
                             for ly in order}
        # store per-object offsets on the geom dicts used by set_pose
        if coll_name in "LR":
            geom[coll_name]["explode_off"] = offs
        else:
            geom["hub_explode_off"] = offs
            geom["hub_basis0"] = {ob.name: ob.matrix_basis.copy()
                                  for ob in colls["Hub"].all_objects}
    # simple readable record: layer -> offset per collection
    rec = {}
    for coll_name, order in (("L", ex["order_bottom_to_top"]),
                             ("R", ex["order_bottom_to_top"]),
                             ("Hub", ex["hub_order"])):
        if coll_name in "LR":
            offs = geom[coll_name]["explode_off"]
        else:
            offs = geom["hub_explode_off"]
        amap = classify(coll_name)
        by_ly = {}
        for nm, ly in amap.items():
            by_ly.setdefault(ly, offs.get(nm, 0.0))
        rec[coll_name] = {ly: round(by_ly.get(ly, 0.0), 1) for ly in order}
    derived["explode_offsets_mm"] = rec
    logs.append(f"explode offsets {json.dumps(rec)}")

    rep = ol.check(D, keys)
    derived["outline_vertices"] = {h: rep[h]["vertices_mm"] for h in "LR"}
    derived["min_bezel_mm"] = {h: rep[h]["min_bezel_mm"] for h in "LR"}

    for l in logs:
        print("[geom]", l)
    bpy.context.scene["chasm_geom_log"] = "\n".join(logs)

    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "derived.json"), "w") as fp:
        json.dump(derived, fp, indent=1)
    rev2_case.write_solidworks_handoff(D,keys,geom,derived,os.path.join(HERE,"out","solidworks_handoff.json"))

    CTX = {"design": D, "keys": keys, "geom": geom, "colls": colls,
           "derived": derived, "mats": mats}
    return CTX


# ---------------------------------------------------------------- hub

def build_hub(D, mats, coll, cut, scene_coll, geom):
    hc = D["hub"]
    W, Dd, H = hc["size_mm"]
    body_pts = rounded_rect(W, Dd, hc["r_plan_mm"], 6)
    cav_pts = rounded_rect(W - 2 * hc["wall_t_mm"], Dd - 2 * hc["wall_t_mm"],
                           max(hc["r_plan_mm"] - hc["wall_t_mm"], 1.0), 6)
    shell = prism("hub_shell", body_pts, hc["bottom_t_mm"], H, coll, mats["frost_acrylic"])
    bool_diff(shell, prism("hub_c_cav", cav_pts, hc["bottom_t_mm"] - 0.1,
                           H - hc["lip_t_mm"], cut))
    o = hc["oled"]
    win_pts = rounded_rect(o["window_mm"][0], o["window_mm"][1], 1.5, 4,
                           o["window_xy"][0], o["window_xy"][1])
    bool_diff(shell, prism("hub_c_oled", win_pts, H - hc["lip_t_mm"] - 0.5,
                           H + 0.1, cut))

    u = D["internals"]["usb_c"]
    nn = len(rounded_rect(u["opening_mm"][0], u["opening_mm"][1], 1.0, 4))
    for i, x in enumerate(hc["usb_c"]["x_mm"]):
        stad = rounded_rect(u["opening_mm"][0], u["opening_mm"][1],
                            min(u["r_mm"], u["opening_mm"][1] / 2), 4)
        nn = len(stad)
        cverts = []
        for dpt in (Dd / 2 - hc["wall_t_mm"] - 1.5, Dd / 2 + 2.0):  # G6: through the wall
            for sx, sy in stad:
                cverts.append((x + sx, dpt, hc["usb_c"]["z_mm"] + sy))
        cfaces = [tuple(reversed(range(nn))), tuple(range(nn, 2 * nn))]
        cfaces += [(i2, (i2 + 1) % nn, (i2 + 1) % nn + nn, i2 + nn) for i2 in range(nn)]
        bool_diff(shell, new_obj(f"hub_c_usb{i}", cverts, cfaces, cut))
        # H7: hollow receptacle ring, open front, tongue ~1 mm recessed
        fy = Dd / 2 - u["recess_mm"]
        o_pts = rounded_rect(u["shell_mm"][0], u["shell_mm"][1],
                             min(1.4, u["shell_mm"][1] / 2), 4)
        i_pts = rounded_rect(u["shell_mm"][0] - 0.6, u["shell_mm"][1] - 0.6,
                             min(1.1, (u["shell_mm"][1] - 0.6) / 2), 4)
        stadium_ring(f"hub_usb_shell{i}", o_pts, i_pts, 0.0, -4.0,
                     lambda sx, sy, d: (x + sx, fy + d,
                                        hc["usb_c"]["z_mm"] + sy),
                     coll, mats[u["material_shell"]])
        dark = [(x + sx, fy - 4.05, hc["usb_c"]["z_mm"] + sy)
                for sx, sy in rounded_rect(u["opening_mm"][0] - 0.5,
                                           u["opening_mm"][1] - 0.5, 1.2, 3)]
        new_obj(f"hub_usb_dark{i}", dark, [tuple(range(len(dark)))], coll,
                mats["usb_dark"])
        # tongue: small dark tab ~1 mm behind the shell front (visible in 06b)
        tp = rounded_rect(6.7, 0.7, 0.3, 3)
        tverts = []
        for dpt in (fy - 1.0, fy - 3.0):
            for sx2, sy2 in tp:
                tverts.append((x + sx2, dpt, hc["usb_c"]["z_mm"] + sy2))
        ntp = len(tp)
        tfaces = [tuple(reversed(range(ntp))), tuple(range(ntp, 2 * ntp))]
        tfaces += [(i2, (i2 + 1) % ntp, (i2 + 1) % ntp + ntp, i2 + ntp)
                   for i2 in range(ntp)]
        new_obj(f"hub_usb_tongue{i}", tverts, tfaces, coll, mats["usb_dark"])

    bevel(shell, hc["edge_fillet_mm"], 3)
    bottom = prism("hub_bottom", body_pts, 0.0, hc["bottom_t_mm"], coll,
                   mats["clear_acrylic"])
    bevel(bottom, hc["edge_fillet_mm"], 3)

    pcb_pts = rounded_rect(W - 2 * hc["wall_t_mm"] - 2, Dd - 2 * hc["wall_t_mm"] - 2,
                           2.0, 4)
    prism("hub_pcb", pcb_pts, hc["pcb_z"][0], hc["pcb_z"][1], coll, mats["pcb_white"])
    rf = D["internals"]["rf_module"]
    box("hub_rf", hc["rf_module_xy"][0], hc["rf_module_xy"][1],
        hc["pcb_z"][1], hc["pcb_z"][1] + 2.0, rf["size_mm"][0], rf["size_mm"][1],
        coll, mats["rf_can"])
    box("hub_oled_mod", o["window_xy"][0], o["window_xy"][1], hc["pcb_z"][1],
        H - hc["lip_t_mm"] - 0.7, o["window_mm"][0] - 2, o["window_mm"][1] - 2,
        coll, mats["black_glass"])

    # window prism: black glass all faces, top face carries the emissive OLED image
    win = prism("hub_oled_win", win_pts, H - 0.8, H + 0.02, coll)
    win.data.materials.append(mats[o["window_material"]])
    win.data.materials.append(emissive_mat("oled_emit", o["texture"], o["emission"]))
    uv = win.data.uv_layers.new()
    np2 = len(win_pts)
    for poly in win.data.polygons:
        if poly.index == 1:                     # top face: uv 0..1 = window rect
            poly.material_index = 1
            for li, vi in enumerate(poly.vertices):
                fx, fy = win_pts[vi - np2]
                uv.data[poly.loop_start + li].uv = (
                    (fx - (o["window_xy"][0] - o["window_mm"][0] / 2)) / o["window_mm"][0],
                    (fy - (o["window_xy"][1] - o["window_mm"][1] / 2)) / o["window_mm"][1])

    kn = hc["knob"]
    if hc.get("knob_enabled", True):  # 2026-10-02: knob moved to the keyboard
        disc("hub_enc", kn["xy"][0], kn["xy"][1], hc["pcb_z"][1],
             H + kn["gap_mm"] - 0.2, 6.0, coll, mats["rf_can"], seg=24)
        knob = knob_mesh("hub_knob", kn, mats[kn["material"]], coll)
        knob.location = (kn["xy"][0] * MM, kn["xy"][1] * MM, (H + kn["gap_mm"]) * MM)

    gl = hc["gull"]
    for side in (-1, 1):  # hub shows the full logo: both wings, real mirror
        wp = wing_pts(D, side, gl["wing_span_mm"])
        pts = [(gl["xy"][0] + px, gl["xy"][1] + py) for px, py in wp]
        ribbon(f"hub_gull{'L' if side < 0 else 'R'}_groove", pts,
               gl["stroke_mm"] + 0.3, H + 0.02 - 0.6 - 0.15, H + 0.02 - 0.05,
               coll, mats["black_glass"])
        ribbon(f"hub_gull{'L' if side < 0 else 'R'}", pts, gl["stroke_mm"],
               H + 0.02 - 0.6, H + 0.02, coll, mats["stainless_polished"])

    root = bpy.data.objects.new("hub_root", None)
    scene_coll.objects.link(root)
    for ob in list(coll.objects):
        if ob.parent is None:
            ob.parent = root
    geom["hub_root"] = root


def knob_mesh(name, kn, mat, coll):
    d, h = kn["d_mm"] / 2, kn["h_mm"]
    m = kn["knurl_count"] * 2
    rings = [(0.0, d), (h - kn["top_chamfer_mm"], d), (h, d - kn["top_chamfer_mm"])]
    verts = []
    for z, rr in rings:
        for i in range(m):
            a = 2 * math.pi * i / m
            r2 = rr - (0.0 if z == rings[-1][0] or i % 2 == 0 else kn["knurl_depth_mm"])
            verts.append((r2 * math.cos(a), r2 * math.sin(a), z))
    faces = []
    for k in range(len(rings) - 1):
        for i in range(m):
            a, b = k * m + i, k * m + (i + 1) % m
            faces.append((a, b, b + m, a + m))
    faces.append(tuple(reversed(range(m))))
    faces.append(tuple((len(rings) - 1) * m + i for i in range(m)))
    ob = new_obj(name, verts, faces, coll, mat)
    recalc_normals(ob.data)
    # R8: top face brushed (machined look) so it doesn't mirror the dark world
    ob.data.materials.append(bpy.data.materials["stainless_brushed"])
    ob.data.polygons[-1].material_index = 1
    return ob


# ---------------------------------------------------------------- studio

def build_studio(D, mats, coll):
    st = D["studio"]
    sx, sy = st["seamless_size_m"]
    r = st["seamless_curve_r_m"]
    y_wall = sy * 0.34
    prof = [(-sy * 0.6, 0.0), (y_wall - r, 0.0)]
    for i in range(1, 12):
        a = -math.pi / 2 + (math.pi / 2) * i / 11
        prof.append((y_wall - r + r * math.cos(a), r + r * math.sin(a)))
    prof.append((y_wall, 2.6))
    verts = [(x, y, z) for x in (-sx / 2, sx / 2) for y, z in prof]
    np_ = len(prof)
    me = bpy.data.meshes.new("seamless")
    me.from_pydata(verts, [],
                   [(i, i + 1, np_ + i + 1, np_ + i) for i in range(np_ - 1)])
    me.materials.append(mats["studio_seamless"])
    ob = bpy.data.objects.new("seamless", me)
    coll.objects.link(ob)
    recalc_normals(me)

    pw, pd, ph = st["plinth_mm"]
    plinth = prism("plinth", rounded_rect(pw, pd, 12, 4), 0.0, ph, coll,
                   mats["studio_plinth"])
    bevel(plinth, 6.0, 3)
    plinth.hide_render = True
    plinth.hide_set(True)

    kl = st["key_light"]
    ld = bpy.data.lights.new("key", 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = kl["size_m"]
    ld.energy = kl["power_w"]
    l = bpy.data.objects.new("key", ld)
    coll.objects.link(l)
    l.location = (-1.1, -0.9, 1.7)
    l.rotation_euler = (Vector((0, 0, 0.1)) - l.location).to_track_quat('-Z', 'Y').to_euler()

    # soft wash on the backdrop so the wall doesn't fall into darkness
    bl = st.get("backdrop_light")
    if bl:
        ld2 = bpy.data.lights.new("backdrop", 'AREA')
        ld2.shape = 'DISK'
        ld2.size = bl["size_m"][0]
        ld2.energy = bl["power_w"]
        l2 = bpy.data.objects.new("backdrop", ld2)
        coll.objects.link(l2)
        l2.location = (-0.3, 0.2, 1.6)
        l2.rotation_euler = (Vector((0, 1.0, 1.4)) - l2.location).to_track_quat('-Z', 'Y').to_euler()

    # negative fill: dark card opposite the key, so frost walls/caps get
    # tonal separation; invisible to camera
    nf = st.get("neg_fill")
    if nf:
        nw, nh = nf["size_m"]
        me3 = bpy.data.meshes.new("neg_fill")
        me3.from_pydata([(-nw / 2, 0, -nh / 2), (nw / 2, 0, -nh / 2),
                         (nw / 2, 0, nh / 2), (-nw / 2, 0, nh / 2)],
                        [], [(0, 1, 2, 3)])
        nm = bpy.data.materials.new("neg_fill")
        b3 = nm.node_tree.nodes["Principled BSDF"]
        b3.inputs["Base Color"].default_value = (nf["colour"],) * 3 + (1.0,)
        b3.inputs["Roughness"].default_value = 0.9
        me3.materials.append(nm)
        card2 = bpy.data.objects.new("neg_fill", me3)
        coll.objects.link(card2)
        card2.location = nf["pos"]
        card2.rotation_euler = (Vector((0, 0, 0.1)) - card2.location).to_track_quat('-Z', 'Y').to_euler()
        card2.visible_camera = False
        card2.visible_shadow = False   # GI-only neg fill; no patch on the backdrop
        for attr in ("visible_glossy", "visible_transmission",
                     "visible_scatter", "visible_volume_scatter"):
            try:
                setattr(card2, attr, False)
            except AttributeError:
                pass

    # overhead scrim: big emissive plane so up-facing polished metal reflects
    # light grey (the alexotos window-light look); invisible to camera
    sc = st.get("scrim")
    if sc:
        sw, sh = sc["size_m"]
        me5 = bpy.data.meshes.new("scrim")
        me5.from_pydata([(-sw / 2, -sh / 2, 0), (sw / 2, -sh / 2, 0),
                         (sw / 2, sh / 2, 0), (-sw / 2, sh / 2, 0)],
                        [], [(0, 1, 2, 3)])
        sm = bpy.data.materials.new("scrim")
        nt5 = sm.node_tree
        nt5.nodes.clear()
        em5 = nt5.nodes.new("ShaderNodeEmission")
        em5.inputs["Strength"].default_value = sc["emission_w"]
        em5.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1)
        out5 = nt5.nodes.new("ShaderNodeOutputMaterial")
        nt5.links.new(em5.outputs[0], out5.inputs["Surface"])
        me5.materials.append(sm)
        scrim = bpy.data.objects.new("scrim", me5)
        coll.objects.link(scrim)
        scrim.location = sc["pos"]
        scrim.rotation_euler = (math.pi, 0, 0)   # face down
        recalc_normals(me5)
        scrim.visible_camera = False

    # H2: reflection card - big emissive ceiling for polished metal seen at
    # low angles (the stowed weight on the flipped underside); glossy rays only
    rc = st.get("reflect_card")
    if rc:
        rw, rh = rc["size_m"]
        me6 = bpy.data.meshes.new("reflect_card")
        me6.from_pydata([(-rw / 2, -rh / 2, 0), (rw / 2, -rh / 2, 0),
                         (rw / 2, rh / 2, 0), (-rw / 2, rh / 2, 0)],
                        [], [(0, 1, 2, 3)])
        rm = bpy.data.materials.new("reflect_card")
        nt6 = rm.node_tree
        nt6.nodes.clear()
        em6 = nt6.nodes.new("ShaderNodeEmission")
        em6.inputs["Strength"].default_value = rc["emission_w"]
        em6.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1)
        out6 = nt6.nodes.new("ShaderNodeOutputMaterial")
        nt6.links.new(em6.outputs[0], out6.inputs["Surface"])
        me6.materials.append(rm)
        card3 = bpy.data.objects.new("reflect_card", me6)
        coll.objects.link(card3)
        card3.location = rc["pos"]
        card3.rotation_euler = (math.pi, 0, 0)   # face down
        recalc_normals(me6)
        card3.visible_camera = False
        card3.visible_diffuse = False
        card3.visible_transmission = False
        card3.visible_shadow = False
        for attr in ("visible_scatter", "visible_volume_scatter"):
            try:
                setattr(card3, attr, False)
            except AttributeError:
                pass

    # H5: low front fill card - lifts the case shadow on the desk under the
    # tented half in 03b (the dark region was the seamless, not geometry)
    fl = st.get("fill_low")
    if fl:
        fw, fh = fl["size_m"]
        me7 = bpy.data.meshes.new("fill_low")
        me7.from_pydata([(-fw / 2, 0, -fh / 2), (fw / 2, 0, -fh / 2),
                         (fw / 2, 0, fh / 2), (-fw / 2, 0, fh / 2)],
                        [], [(0, 1, 2, 3)])
        fm = bpy.data.materials.new("fill_low")
        nt7 = fm.node_tree
        nt7.nodes.clear()
        em7 = nt7.nodes.new("ShaderNodeEmission")
        em7.inputs["Strength"].default_value = fl["emission_w"]
        em7.inputs["Color"].default_value = (0.93, 0.94, 0.96, 1)
        out7 = nt7.nodes.new("ShaderNodeOutputMaterial")
        nt7.links.new(em7.outputs[0], out7.inputs["Surface"])
        me7.materials.append(fm)
        card4 = bpy.data.objects.new("fill_low", me7)
        coll.objects.link(card4)
        card4.location = fl["pos"]
        # face the set centre (flat/together area)
        card4.rotation_euler = (Vector((0.0, 0.0, 0.03)) -
                              card4.location).to_track_quat('Z', 'Y').to_euler()
        card4.visible_camera = False

    # gradient card: emission ramp so polished metal reflects a gradient
    gc = st.get("grad_card")
    if gc:
        gw, gh = gc["size_m"]
        me4 = bpy.data.meshes.new("grad_card")
        me4.from_pydata([(-gw / 2, 0, -gh / 2), (gw / 2, 0, -gh / 2),
                         (gw / 2, 0, gh / 2), (-gw / 2, 0, gh / 2)],
                        [], [(0, 1, 2, 3)])
        gm = bpy.data.materials.new("grad_card")
        gm.use_nodes = True
        nt4 = gm.node_tree
        nt4.nodes.clear()
        em = nt4.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = gc["emission_w"]
        tc = nt4.nodes.new("ShaderNodeTexCoord")
        sp = nt4.nodes.new("ShaderNodeSeparateXYZ")
        cr = nt4.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (0.003, 0.003, 0.004, 1)
        cr.color_ramp.elements[1].color = (0.85, 0.85, 0.88, 1)
        out4 = nt4.nodes.new("ShaderNodeOutputMaterial")
        nt4.links.new(tc.outputs["Generated"], sp.inputs[0])
        nt4.links.new(sp.outputs["Z"], cr.inputs[0])
        nt4.links.new(cr.outputs["Color"], em.inputs["Color"])
        nt4.links.new(em.outputs[0], out4.inputs["Surface"])
        me4.materials.append(gm)
        gcard = bpy.data.objects.new("grad_card", me4)
        coll.objects.link(gcard)
        gcard.location = gc["pos"]
        gcard.rotation_euler = (Vector((0, 0.1, 0.1)) - gcard.location).to_track_quat('-Z', 'Y').to_euler()
        gcard.visible_camera = False
        gcard.visible_shadow = False

    # white bounce card, right side, facing the set
    cw, ch2 = st["fill"]["size_m"]
    cen = Vector((1.35, -0.05, 0.6))
    to_origin = Vector((-cen.x, -cen.y, 0)).normalized()
    wdir = Vector((0, 0, 1)).cross(to_origin).normalized()
    cv = [cen - wdir * cw / 2 - Vector((0, 0, ch2 / 2)),
          cen + wdir * cw / 2 - Vector((0, 0, ch2 / 2)),
          cen + wdir * cw / 2 + Vector((0, 0, ch2 / 2)),
          cen - wdir * cw / 2 + Vector((0, 0, ch2 / 2))]
    me2 = bpy.data.meshes.new("bounce")
    me2.from_pydata([tuple(v) for v in cv], [], [(0, 1, 2, 3)])
    me2.materials.append(mats["studio_plinth"])
    card = bpy.data.objects.new("bounce", me2)
    coll.objects.link(card)
    recalc_normals(me2)
    try:
        card.visible_camera = False          # bounce only, never in frame
        card.visible_shadow = False          # and never casts a shadow
    except AttributeError:
        pass

    w = bpy.data.worlds.new("world")
    bpy.context.scene.world = w
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.4, 0.42, 0.46, 1)
    bg.inputs["Strength"].default_value = st["world_strength"]


def point_seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    pose, save = "flat", None
    for i, a in enumerate(argv):
        if a == "--pose":
            pose = argv[i + 1]
        elif a == "--save":
            save = argv[i + 1]
    bpy.context.preferences.filepaths.temporary_directory = os.path.join(HERE, "tmp")
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    ctx = build(design)
    set_pose(pose, ctx=ctx)
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, save))
        print("[saved]", save)


if __name__ == "__main__":
    main()
