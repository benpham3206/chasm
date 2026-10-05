"""Rev 2 Cherry/X-Ray keycaps. Importable by build_scene as a helper module.

Geometry is expressed in millimetres and converted to metres at mesh creation.
Meshes remain local to the cap object so the scene's root pose/explode transforms
continue to work without special handling.
"""
import math


def _mm(v):
    return float(v) * 0.001


def _round_rect(w, d, r, steps=8, cx=0.0, cy=0.0):
    r = max(0.01, min(r, w / 2 - 0.01, d / 2 - 0.01))
    pts = []
    for x, y, a0 in ((w / 2 - r, -d / 2 + r, -90),
                     (w / 2 - r, d / 2 - r, 0),
                     (-w / 2 + r, d / 2 - r, 90),
                     (-w / 2 + r, -d / 2 + r, 180)):
        for j in range(steps + 1):
            a = math.radians(a0 + 90.0 * j / steps)
            pts.append((cx + x + r * math.cos(a), cy + y + r * math.sin(a)))
    return pts


def _mesh(name, verts_mm, faces, bs):
    me = bs.bpy.data.meshes.new(name)
    me.from_pydata([bs.V3(v) for v in verts_mm], [], faces)
    me.update()
    bs.recalc_normals(me)
    for face in me.polygons:
        face.use_smooth = True
    return me


def _surface_z(x, y, row, kc, tw, shift):
    h = row["h_mm"]
    tilt = math.tan(math.radians(row["tilt_deg"]))
    dish = max(0.001, kc.get("rev2", {}).get("dish_depth_mm", kc.get("dish_mm", 0.5)))
    radius = ((tw / 2) ** 2 + dish ** 2) / (2 * dish)
    # The original model uses a cylinder whose axis is parallel to Y.
    return h + (y - shift) * tilt + (radius - math.sqrt(max(radius * radius - x * x, 0.0))) - dish


def build_cap_mesh(name, w_u, row, kc, bs):
    """Build a hollow, drafted Cherry-style shell with a dished top.

    Local frame is compatible with build_scene: origin at key centre, z=0 at
    skirt bottom. The smooth concavity is cylindrical across X. `bs` is the
    build_scene module, passed explicitly to avoid a circular import.
    """
    cfg = kc.get("rev2", {})
    unit = kc["_unit"]
    bw = w_u * unit - (unit - kc["base_1u_mm"])
    bd = kc["base_1u_mm"]
    wall = cfg.get("shell_wall_mm", kc.get("wall_mm", 1.3))
    rbase = cfg.get("base_corner_mm", kc.get("r_base_mm", 0.8))
    rtop = cfg.get("top_corner_mm", kc.get("r_top_mm", 1.6))
    shrink = cfg.get("top_shrink_mm", kc.get("top_shrink_mm", [5.3, 3.6]))
    tw, td = bw - shrink[0], bd - shrink[1]
    shift = kc.get("top_back_shift_mm", 0.5)
    steps = int(cfg.get("corner_segments", 8))
    # Cherry wall profile: a slight belly below the shoulder and a restrained
    # inward draft; concentric rounded rings preserve the plan corner radii.
    profile = cfg.get("wall_profile", [
        [0.00, 0.00, 0.00], [0.035, 0.10, 0.10], [0.12, 0.02, 0.02],
        [0.58, -0.04, -0.03], [0.88, -0.16, -0.10], [0.965, -0.10, -0.06],
        [1.00, 0.00, 0.00]])
    h = row["h_mm"]
    tilt = math.tan(math.radians(row["tilt_deg"]))

    outer, inner = [], []
    for t, expand_x, expand_y in profile:
        rw = bw + (tw - bw) * t + 2 * expand_x
        rd = bd + (td - bd) * t + 2 * expand_y
        rr = max(0.25, rbase + (rtop - rbase) * t)
        pts = _round_rect(rw, rd, rr, steps, 0.0, shift * t)
        outer.append([(x, y, t * (h + (y - shift) * tilt)) for x, y in pts])
        iw, id_ = rw - 2 * wall, rd - 2 * wall
        ipts = _round_rect(iw, id_, max(0.25, rr - wall), steps,
                           0.0, shift * t)
        inner_ring = []
        for x, y in ipts:
            if t >= 0.999:
                z = _surface_z(x, y, row, kc, tw, shift) - wall
            else:
                z = t * (h + (y - shift) * tilt) - wall * t
            inner_ring.append((x, y, z))
        inner.append(inner_ring)

    # Join the wall to the rolled finger-surface perimeter with shared vertices.
    rim_rise = cfg['top_edge_profile'][0][1]
    outer[-1] = [(x,y,_surface_z(x,y,row,kc,tw,shift)+rim_rise) for x,y,_ in outer[-1]]
    m = len(outer[0])
    assert all(len(r) == m for r in outer + inner)
    verts = [v for ring in outer for v in ring] + [v for ring in inner for v in ring]
    faces = []
    nr = len(profile)
    for layer in range(nr - 1):
        for i in range(m):
            j = (i + 1) % m
            a, b = layer * m + i, layer * m + j
            faces.append((a, b, b + m, a + m))
            ia, ib = nr * m + layer * m + i, nr * m + layer * m + j
            faces.append((ia, ia + m, ib + m, ib))
    # Exposed skirt lip is an annulus; the inverted inner face closes the roof.
    for i in range(m):
        j = (i + 1) % m
        faces.append((i, nr * m + i, nr * m + j, j))

    # Multi-ring top skin: a rounded edge rolls into the cylindrical dish.
    top_profiles = cfg.get("top_edge_profile", [
        [1.00, 0.00], [0.992, 0.00], [0.975, 0.00], [0.945, 0.00],
        [0.90, 0.00], [0.82, 0.00], [0.70, 0.00], [0.54, 0.00],
        [0.36, 0.00], [0.20, 0.00], [0.08, 0.00]])
    top_rings = []
    for scale, rise in top_profiles:
        ring = _round_rect(tw * scale, td * scale,
                           max(0.25, rtop * scale), steps, 0, shift)
        top_rings.append([(x, y, _surface_z(x, y, row, kc, tw, shift) + rise)
                          for x, y in ring])
    offset = len(verts)
    verts.extend(v for ring in top_rings[1:] for v in ring)
    for layer in range(len(top_rings) - 1):
        a0 = (nr-1)*m if layer == 0 else offset+(layer-1)*m
        b0 = offset+layer*m
        for i in range(m):
            j = (i + 1) % m
            faces.append((a0 + i, b0 + i, b0 + j, a0 + j))
    faces.append(tuple(offset + (len(top_rings) - 2) * m + i for i in range(m)))
    # The inside roof must follow the cylindrical dish as well. A single
    # nonplanar n-gon bridges over the dish and hides surface legends in glass.
    inner_offset = len(verts)
    inner_roof = []
    for scale, _rise in top_profiles[1:]:
        ring = _round_rect((tw-2*wall)*scale,(td-2*wall)*scale,
                           max(0.25,(rtop-wall)*scale),steps,0,shift)
        inner_roof.append([(x,y,_surface_z(x,y,row,kc,tw,shift)-wall) for x,y in ring])
    verts.extend(v for ring in inner_roof for v in ring)
    for layer in range(len(inner_roof)):
        a0 = nr*m+(nr-1)*m if layer == 0 else inner_offset+(layer-1)*m
        b0 = inner_offset+layer*m
        for i in range(m):
            j=(i+1)%m
            faces.append((a0+j,b0+j,b0+i,a0+i))
    faces.append(tuple(inner_offset+(len(inner_roof)-1)*m+i for i in reversed(range(m))))
    return _mesh(name, verts, faces, bs)


def _object(name, mesh, coll, material, cap, bs):
    ob = bs.bpy.data.objects.new(name, mesh)
    coll.objects.link(ob)
    if material:
        mesh.materials.append(material)
    ob.parent = cap
    ob.matrix_parent_inverse = bs.Matrix.Identity(4)
    return ob


def _poly_extrusion(name, outline, z0, z1, coll, mat, cap, bs, bevel_mm=0.0):
    ob = bs.prism(name, outline, z0, z1, coll, mat)
    ob.parent = cap
    ob.matrix_parent_inverse = bs.Matrix.Identity(4)
    if bevel_mm:
        mod = ob.modifiers.new("edge radius", 'BEVEL')
        mod.width = _mm(bevel_mm)
        mod.segments = 3
    return ob


def _font_scale(font, bs):
    # Use the existing scene calibration where available; this is important for
    # Segoe's unusually deep ascent/descent metrics and keeps cap heights stable.
    fn = getattr(bs, "font_cap_scale", None)
    if fn:
        return fn(font)
    return 1.0


def _legend_mesh(cap, text, size_mm, pos, row, kc, material, coll, fonts, bs,
                 suffix="legend", symbolic=False, anchor="top-left", w_u=1.0):
    if not text:
        return None
    bpy = bs.bpy
    font = fonts.get("sym" if symbolic else "main")
    cu = bpy.data.curves.new(f"{cap.name}_{suffix}_curve", 'FONT')
    cu.body = text
    if font:
        cu.font = font
    cu.size = _mm(size_mm) * _font_scale(font, bs)
    cfg = kc.get("rev2", {})
    # The white second shot is a column, not a decal: it starts inside the
    # opaque core and passes through a matching opening in the clear skin.
    legend_thickness = (cfg.get("skin_thickness_mm", cfg.get("shell_wall_mm", 0.8)) +
                        cfg.get("legend_core_embed_mm", 0.28) +
                        cfg.get("legend_proud_mm", 0.04))
    cu.extrude = _mm(legend_thickness)
    cu.align_x = 'LEFT'
    cu.align_y = 'BOTTOM'
    temp = bpy.data.objects.new(f"{cap.name}_{suffix}_tmp", cu)
    coll.objects.link(temp)
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(temp.evaluated_get(dg))
    if material:
        mesh.materials.append(material)
    # Measure actual font bounds, then align the requested edge. This avoids
    # relying on font ascent metrics for top-left and lower-left kit placement.
    xs = [v.co.x / 0.001 for v in mesh.vertices]
    ys = [v.co.y / 0.001 for v in mesh.vertices]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    if anchor == "center":
        dx = pos[0] - (x0 + x1) / 2
        dy = pos[1] - (y0 + y1) / 2
    elif anchor == "bottom-left":
        dx, dy = pos[0] - x0, pos[1] - y0
    else:
        dx, dy = pos[0] - x0, pos[1] - y1
    proud = cfg.get("legend_proud_mm", 0.04)
    thickness = legend_thickness
    zmin = min(v.co.z / 0.001 for v in mesh.vertices)
    zmax = max(v.co.z / 0.001 for v in mesh.vertices)
    for v in mesh.vertices:
        x = v.co.x / 0.001 + dx
        y = v.co.y / 0.001 + dy
        original_z_mm = (v.co.z / 0.001 - zmin) / (zmax - zmin) * thickness
        v.co.x, v.co.y = _mm(x), _mm(y)
        bw = w_u * kc["_unit"] - (kc["_unit"] - kc["base_1u_mm"])
        v.co.z = _mm(_surface_z(x, y, row, kc,
                                bw - kc["top_shrink_mm"][0],
                                kc.get("top_back_shift_mm", 0.5)) - thickness +
                       proud + original_z_mm)
    mesh.update()
    ob = bpy.data.objects.new(f"{cap.name}_{suffix}", mesh)
    coll.objects.link(ob)
    bpy.data.objects.remove(temp, do_unlink=True)
    bpy.data.curves.remove(cu)
    ob.parent = cap
    ob.matrix_parent_inverse = bs.Matrix.Identity(4)
    return ob


def _icon_paths(icon):
    """Compact kit-shaped vector paths in a normalized [-.5,.5] square."""
    line = lambda *pts: list(pts)
    if icon == "left_arrow":
        return [line((.40, 0), (-.40, 0)), line((-.40, 0), (-.08, .30)),
                line((-.40, 0), (-.08, -.30))]
    if icon == "tab_arrows":
        return [line((-.42, .20), (.40, .20)), line((-.42, .20), (-.20, .40)),
                line((-.42, .20), (-.20, 0)), line((.42, -.20), (-.40, -.20)),
                line((.42, -.20), (.20, 0)), line((.42, -.20), (.20, -.40))]
    if icon == "caps_lock":
        return [line((-.34, -.30), (.34, -.30), (.34, .15), (-.34, .15), (-.34, -.30)),
                line((-.22, .15), (-.22, .26), (-.12, .42), (0, .47),
                     (.12, .42), (.22, .26), (.22, .15))]
    if icon == "shift":
        return [line((-.16,-.44),(.16,-.44),(.16,-.05),(.38,-.05),
                     (0,.40),(-.38,-.05),(-.16,-.05),(-.16,-.44))]
    if icon == "up":
        return [line((0,-.4),(0,.4)),line((0,.4),(-.3,.08)),line((0,.4),(.3,.08))]
    if icon == "command":
        path=[]
        for cx,cy,a0 in [(-.3,.3,0),(.3,.3,-90),(.3,-.3,180),(-.3,-.3,90)]:
            path.extend([(cx+.12*math.cos(math.radians(a0+i*270/12)),
                          cy+.12*math.sin(math.radians(a0+i*270/12))) for i in range(13)])
        path.append(path[0])
        return [path]
    if icon == "ctrl":
        return [line((-.38, -.20), (0, .26), (.38, -.20))]
    if icon in ("diamond", "win"):
        return [line((0, .45), (.36, 0), (0, -.45), (-.36, 0), (0, .45))]
    if icon == "alt":
        return [line((-.38, .30), (-.24, -.30), (0, -.30), (.15, .18),
                     (.34, -.30)), line((-.18, .05), (.20, .05))]
    if icon == "menu":
        return [line((-.36, .30), (.36, .30)), line((-.36, 0), (.36, 0)),
                line((-.36, -.30), (.36, -.30))]
    if icon in ("enter", "return"):
        return [line((-.35, .28), (.35, .28), (.35, -.12), (-.28, -.12)),
                line((-.28, -.12), (-.03, .12)), line((-.28, -.12), (-.03, -.36))]
    if icon in ("circle_return", "circle_arrow"):
        arc = [(0.26 * math.cos(math.radians(42 + i * 270 / 24)),
                0.26 * math.sin(math.radians(42 + i * 270 / 24))) for i in range(25)]
        return [arc, line(arc[-1], (arc[-1][0] - .25, arc[-1][1] + .02),
                          (arc[-1][0] - .04, arc[-1][1] + .25))]
    if icon == "chevrons":
        return [line((-.34, .25), (0, .02), (.34, .25)),
                line((-.34, -.18), (0, -.41), (.34, -.18))]
    if icon == "framed_grid":
        return [line((-.42, -.42), (.42, -.42), (.42, .42), (-.42, .42), (-.42, -.42)),
                line((0, -.34), (0, .34)), line((-.34, 0), (.34, 0))]
    if icon == "right_arrow":
        return [line((-.40, 0), (.40, 0)), line((.40, 0), (.08, .30)),
                line((.40, 0), (.08, -.30))]
    if icon == "down":
        return [line((0, .40), (0, -.40)), line((0, -.40), (-.30, -.08)),
                line((0, -.40), (.30, -.08))]
    return []


def _icon_mesh(cap, icon, size_mm, pos, row, kc, material, coll, bs,
               w_u=1.0, anchor="bottom-left", suffix="icon"):
    """Raised white vector legend, conforming every stroke to the key dish."""
    paths = _icon_paths(icon)
    if not paths:
        return None
    cfg = kc.get("rev2", {})
    stroke = cfg.get("icon_stroke_mm", 0.19)
    width = size_mm
    height = size_mm
    if anchor == "top-left":
        left, top = pos
        ox, oy = left, top - height
    elif anchor == "center":
        ox, oy = pos[0] - width / 2, pos[1] - height / 2
    else:
        ox, oy = pos
    bw = w_u * kc["_unit"] - (kc["_unit"] - kc["base_1u_mm"])
    tw = bw - kc["top_shrink_mm"][0]
    shift = kc.get("top_back_shift_mm", 0.5)
    proud = cfg.get("legend_proud_mm", 0.035)
    thickness = (cfg.get("skin_thickness_mm", cfg.get("shell_wall_mm", 0.8)) +
                 cfg.get("legend_core_embed_mm", 0.28) + proud)
    verts, faces = [], []

    def add_segment(a, b):
        ax, ay = ox + (a[0] + 0.5) * width, oy + (a[1] + 0.5) * height
        bx, by = ox + (b[0] + 0.5) * width, oy + (b[1] + 0.5) * height
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length * stroke / 2, dx / length * stroke / 2
        pts = [(ax + nx, ay + ny), (ax - nx, ay - ny),
               (bx - nx, by - ny), (bx + nx, by + ny)]
        idx = len(verts)
        zbase = [(_surface_z(x, y, row, kc, tw, shift) - thickness + proud)
                 for x, y in pts]
        verts.extend((x, y, z) for (x, y), z in zip(pts, zbase))
        verts.extend((x, y, z + thickness)
                     for (x, y), z in zip(pts, zbase))
        faces.extend([(idx, idx + 1, idx + 2, idx + 3),
                      (idx + 4, idx + 7, idx + 6, idx + 5),
                      (idx, idx + 4, idx + 5, idx + 1),
                      (idx + 1, idx + 5, idx + 6, idx + 2),
                      (idx + 2, idx + 6, idx + 7, idx + 3),
                      (idx + 3, idx + 7, idx + 4, idx)])

    for path in paths:
        for a, b in zip(path, path[1:]):
            add_segment(a, b)
    mesh = _mesh(f"{cap.name}_{suffix}_mesh", verts, faces, bs)
    return _object(f"{cap.name}_{suffix}", mesh, coll, material, cap, bs)


def _cross_outline(arm, half):
    return [(-half, -arm), (half, -arm), (half, -half), (arm, -half),
            (arm, half), (half, half), (half, arm), (-half, arm),
            (-half, half), (-arm, half), (-arm, -half), (-half, -half)]


def _socket_mesh(name, cfg, bs):
    """Open-bottom hollow MX cross socket with a closed internal ceiling."""
    z0 = cfg["stem_z0_mm"]
    z1 = (cfg["_row_height_mm"] - cfg["body_top_recess_mm"] -
          cfg["body_dish_depth_mm"] - cfg["body_wall_mm"])
    outer = _cross_outline(cfg["stem_arm_mm"], cfg["stem_halfwidth_mm"])
    inner = _cross_outline(cfg["socket_arm_mm"], cfg["socket_halfwidth_mm"])
    n = len(outer)
    verts = ([(x, y, z0) for x, y in outer] +
             [(x, y, z1) for x, y in outer] +
             [(x, y, z0) for x, y in inner] +
             [(x, y, z1 - cfg["socket_roof_mm"]) for x, y in inner])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((2 * n + i, 3 * n + i, 3 * n + j, 2 * n + j))
        faces.append((i, 2 * n + i, 2 * n + j, j))
        faces.append((n + i, n + j, 3 * n + j, 3 * n + i))
    faces.append(tuple(3 * n + i for i in range(n)))
    me = _mesh(name, verts, faces, bs)
    return me


def _homing_bar(cap, row, kc, cfg, material, coll, bs):
    bw = kc["base_1u_mm"] - kc["top_shrink_mm"][0]
    td = kc["base_1u_mm"] - kc["top_shrink_mm"][1]
    shift = kc.get("top_back_shift_mm", 0.5)
    x = cfg["homing_x_mm"]
    y = shift + cfg["homing_y_mm"]
    z = _surface_z(x, y, row, kc, bw, shift)
    w, d, h = cfg["homing_width_mm"], cfg["homing_depth_mm"], cfg["homing_height_mm"]
    # Tie the tactile bar into the opaque core through the clear skin too.
    skin = cfg.get("skin_thickness_mm", cfg.get("shell_wall_mm", 0.8))
    embed = cfg.get("legend_core_embed_mm", 0.28)
    ob = bs.box(f"{cap.name}_homing", x, y, z - skin - embed, z + h,
                w, d, coll, material)
    ob.parent = cap
    ob.matrix_parent_inverse = bs.Matrix.Identity(4)
    mod = ob.modifiers.new("homing radius", 'BEVEL')
    mod.width = _mm(min(cfg["homing_radius_mm"], d / 2, h / 2))
    mod.segments = 3
    return ob


def add_details(cap, k, rowcfg, kc, mats, coll, fonts, bs):
    """Add the opaque PBT body, hollow MX socket, homing bar and double-shot legends."""
    cfg = kc.get("rev2", {})
    body_mat = mats.get(cfg.get("body_material", "xray_pbt_white"),
                        mats.get(kc.get("legend_material")))
    legend_mat = mats.get(cfg.get("legend_material", kc.get("legend_material")))
    # The body is a second, hollow injection-moulded shell under a real clear
    # outer shell. Plan and roof offsets both equal the nominal skin thickness,
    # leaving an unambiguous refractive rim rather than two nearly coincident
    # surfaces.
    skin = cfg.get("skin_thickness_mm", cfg.get("shell_wall_mm", 0.8))
    corekc = dict(kc)
    corecfg = dict(cfg)
    corecfg["shell_wall_mm"] = cfg.get("body_wall_mm", 1.25)
    corecfg["dish_depth_mm"] = cfg.get("body_dish_depth_mm", cfg.get("dish_depth_mm", 0.47))
    base_inset = cfg.get("body_base_inset_mm", skin)
    top_inset = cfg.get("body_inset_mm", skin)
    # base_1u is already reduced by 2*base_inset. Adjust the shrink only by
    # the *difference* so the final top inset is exactly top_inset, not doubled.
    shrink_delta = 2 * (top_inset - base_inset)
    corecfg["top_shrink_mm"] = [v + shrink_delta for v in
                                cfg.get("top_shrink_mm", kc.get("top_shrink_mm", [5.3, 3.6]))]
    corekc["rev2"] = corecfg
    corekc["base_1u_mm"] = kc["base_1u_mm"] - 2 * base_inset
    core_row = dict(rowcfg)
    core_row["h_mm"] = rowcfg["h_mm"] - cfg.get("body_top_recess_mm", skin)
    core = build_cap_mesh(f"{cap.name}_white_core_mesh", k["w_u"], core_row, corekc, bs)
    core_ob = _object(f"{cap.name}_white_core", core, coll, body_mat, cap, bs)
    core_ob["xray_skin_mm"] = skin
    core_ob["xray_core_wall_mm"] = cfg.get("body_wall_mm", 1.1)

    socketcfg = dict(cfg)
    socketcfg["_row_height_mm"] = rowcfg["h_mm"]
    smesh = _socket_mesh(f"{cap.name}_socket_mesh", socketcfg, bs)
    _object(f"{cap.name}_mx_socket", smesh, coll, body_mat, cap, bs)

    label = k["label"]
    modifiers = cfg.get("modifier_icons", {})
    alphas = cfg.get("shifted_legends", {})
    legend = kc.get("legend", {})
    bw = k["w_u"] * kc["_unit"] - (kc["_unit"] - kc["base_1u_mm"])
    tw = bw - kc["top_shrink_mm"][0]
    td = kc["base_1u_mm"] - kc["top_shrink_mm"][1]
    mx, my = legend.get("margin_mm", [2.6, 2.4])
    shift = kc.get("top_back_shift_mm", 0.5)
    gx, gy = -tw / 2 + mx, shift + td / 2 - my

    # Two-line pairs follow the X-Ray kit: smaller shifted glyph over the base
    # symbol, aligned to the top-left corner. Modifiers occupy the bottom-left.
    legend_parts = []
    if label in alphas:
        shifted, base = alphas[label]
        pair_size = cfg.get("pair_base_size_mm", legend.get("alpha_size_mm", 3.6))
        small_size = cfg.get("pair_shift_size_mm", 1.45)
        legend_parts.append(_legend_mesh(cap, shifted, small_size, (gx, gy),
                            rowcfg, kc, legend_mat, coll, fonts, bs,
                            suffix="legend_shift", symbolic=True, w_u=k["w_u"]))
        legend_parts.append(_legend_mesh(cap, base, pair_size,
                            (gx, gy - small_size * 0.70 - cfg.get("pair_line_gap_mm", 0.22)),
                            rowcfg, kc, legend_mat, coll, fonts, bs,
                            suffix="legend_base", w_u=k["w_u"]))
    elif label in modifiers:
        icon = modifiers[label]
        size = cfg.get('icon_sizes_mm',{}).get(label,cfg.get("modifier_size_mm", legend.get("mod_size_mm", 2.2)))
        if label == "Tab":
            pos = (-tw / 2 + mx, shift + td / 2 - my)
            anchor = "top-left"
        else:
            pos = (-tw / 2 + mx, shift - td / 2 + my)
            anchor = "bottom-left"
        legend_parts.append(_icon_mesh(cap, icon, size, pos, rowcfg, kc,
                            legend_mat, coll, bs, w_u=k["w_u"],
                            anchor=anchor, suffix="legend_icon"))
    elif label in ("Up", "Down", "Left", "Right"):
        arrows = cfg.get("arrow_glyphs", {"Up": "up", "Down": "down",
                                           "Left": "left_arrow", "Right": "right_arrow"})
        legend_parts.append(_icon_mesh(cap, arrows[label], cfg.get("arrow_size_mm", 4.0),
                            (0.0, shift), rowcfg, kc, legend_mat, coll, bs,
                            w_u=k["w_u"], anchor="center", suffix="legend_arrow"))
    else:
        text = legend.get("text", {}).get(label, label)
        if text:
            size = cfg.get("single_size_mm", legend.get("alpha_size_mm", 3.6))
            legend_parts.append(_legend_mesh(cap, text, size, (gx, gy), rowcfg,
                                kc, legend_mat, coll, fonts, bs, suffix="legend",
                                w_u=k["w_u"]))

    if label in cfg.get("homing_labels", ["F", "J"]):
        legend_parts.append(_homing_bar(cap, rowcfg, kc, cfg, body_mat, coll, bs))
