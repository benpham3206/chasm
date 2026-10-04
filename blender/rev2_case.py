"""Parametric case, spring-mount, flex-cut and SolidWorks handoff helpers.

All geometry inputs and return metadata are in millimetres in the half frame.
The shell/pose/stack owners remain in build_scene.py; this module keeps the
derived lower-case and mount geometry deterministic from design.json values.
"""
import json
import math
import os


def _unit(v):
    d = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / d, v[1] / d)


def _mean(poly):
    return (sum(p[0] for p in poly) / len(poly),
            sum(p[1] for p in poly) / len(poly))


def _lerp(a, b, t):
    return a + (b - a) * t


def _new_mesh(name, verts_mm, faces, coll, mat, bs):
    ob = bs.new_obj(name, verts_mm, faces, coll, mat)
    if hasattr(bs, "recalc_normals"):
        bs.recalc_normals(ob.data)
    return ob


def _loft_solid(name, rings, coll, mat, bs):
    """Closed ring loft. Rings are equally sampled (x,y,z) loops in mm."""
    if len(rings) < 2 or any(len(r) != len(rings[0]) for r in rings):
        raise ValueError("loft rings must have matching point counts")
    n = len(rings[0])
    verts = [p for ring in rings for p in ring]
    faces = [tuple(reversed(range(n))),
             tuple((len(rings) - 1) * n + i for i in range(n))]
    for layer in range(len(rings) - 1):
        a0, b0 = layer * n, (layer + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    return _new_mesh(name, verts, faces, coll, mat, bs)


def _loft_skirt(name, outer_rings, inner_rings, coll, mat, bs):
    """Closed perimeter-band loft with an open center for the PCB/weight stack."""
    n = len(outer_rings[0])
    if len(inner_rings) != len(outer_rings) or any(len(r) != n for r in inner_rings):
        raise ValueError("inner and outer case loft rings must match")
    verts = [p for ring in outer_rings for p in ring] + \
            [p for ring in inner_rings for p in ring]
    layers = len(outer_rings)
    faces = []
    # Outer wall, then reversed inner wall.
    for layer in range(layers - 1):
        o0, o1 = layer * n, (layer + 1) * n
        i0, i1 = layers * n + layer * n, layers * n + (layer + 1) * n
        for j in range(n):
            k = (j + 1) % n
            faces.append((o0 + j, o0 + k, o1 + k, o1 + j))
            faces.append((i0 + k, i0 + j, i1 + j, i1 + k))
    # Close the upper seam and lower edge while leaving the inside open.
    for j in range(n):
        k = (j + 1) % n
        faces.append((j, layers * n + j, layers * n + k, k))
        ob, ib = (layers - 1) * n, layers * n + (layers - 1) * n
        faces.append((ob + j, ob + k, ib + k, ib + j))
    return _new_mesh(name, verts, faces, coll, mat, bs)


def create_lower_base(half, poly, D, keys, coll, mats, bs, desk_z=None):
    """Build one clear lower shell as a soft, tucked loft beneath the upper box.

    ``poly`` is the already radiused CCW plan outline in half-frame mm. ``desk_z``
    may be a case-frame ``z(x,y)`` function for the flat pose. Without it, the
    explicit design stations set the bottom plane. The returned dict contains
    the object and an inspectable profile record; callers may use ``["object"]``.
    """
    c = D["case"]["lower_base"]
    ymin = min(p[1] for p in poly)
    ymax = max(p[1] for p in poly)
    depth = max(ymax - ymin, 1e-6)
    import outline as ol
    edges = D["case"]["outline"][half]
    unit_mm = keys["unit_mm"]

    def z_bottom(p):
        # Circle arc with a horizontal tangent at its start; it uses the radius
        # that is also written to the CAD handoff. The final arc meets the rear
        # edge with a shallow rising tangent (Evo75 graduated-side cue).
        start_y = ymin + c["curve_start_fraction"] * depth
        x = max(0.0, p[1] - start_y)
        radius = c["graduated_curve_radius_mm"]
        arc_x = min(x, depth - (start_y - ymin))
        arc_x = min(arc_x, radius - 1e-6)
        rise = radius - math.sqrt(radius * radius - arc_x * arc_x)
        if x > arc_x:
            slope = arc_x / math.sqrt(radius * radius - arc_x * arc_x)
            rise += (x - arc_x) * slope
        # The desk callback gives the lower floor's local absolute datum. The
        # case pose translation makes its range line up with the 19.3 mm front
        # height; do not clamp it to the local seam plane.
        base = (desk_z(p[0], p[1]) + c["desk_clearance_mm"]
                if desk_z is not None else c["bottom_front_z_mm"])
        return base + rise

    outer_rings, inner_rings = [], []
    floor_outline = None
    for station in c["stations"]:
        inset = station["inset_mm"]
        z_offset = station["z_offset_mm"]
        outer2d, _, _ = ol.outline(edges, keys["keys"], half, unit_mm, inset=inset)
        inner2d, _, _ = ol.outline(edges, keys["keys"], half, unit_mm,
                                   inset=inset + c["wall_t_mm"])
        if len(outer2d) != len(inner2d) or (outer_rings and len(outer2d) != len(outer_rings[0])):
            raise ValueError("outline offset changed sample count; use matching plan arcs")
        floor_outline = outer2d
        outer_rings.append([(x, y, z_bottom((x, y)) + z_offset) for x, y in outer2d])
        inner_rings.append([(x, y, z_bottom((x, y)) + z_offset) for x, y in inner2d])
        if station["name"] != "seam" and any(
                z > c["seam_z_mm"] - c["seam_clearance_mm"]
                for _x, _y, z in outer_rings[-1]):
            raise ValueError(f"{half} {station['name']} exceeds lower-shell seam clearance")

    # The outer seam ring is tied to the shared shell datum; the lower stations
    # descend toward the case bottom and are inset to form the clean reveal.
    seam_z = c["seam_z_mm"]
    outer_rings[0] = [(x, y, seam_z) for x, y, _z in outer_rings[0]]
    inner_rings[0] = [(x, y, seam_z) for x, y, _z in inner_rings[0]]
    ob = _loft_skirt(f"{half}_lower_base", outer_rings, inner_rings, coll,
                     mats[c["material"]], bs)
    profile = [{"station": s["name"], "inset_mm": s["inset_mm"],
                "z_offset_mm": s["z_offset_mm"]} for s in c["stations"]]
    curve_run = depth * (1.0 - c["curve_start_fraction"])
    curve_r = c["graduated_curve_radius_mm"]
    curve_rise = curve_r - math.sqrt(max(curve_r * curve_r - curve_run * curve_run, 0.0))
    return {"object": ob, "profile": profile,
            "seam_z_mm": seam_z, "bottom_front_z_mm": c["bottom_front_z_mm"],
            "bottom_rear_rise_mm": curve_rise, "curve_run_mm": curve_run,
            "curve_radius_mm": curve_r, "bottom_z": z_bottom,
            "floor_outline": floor_outline}


def _leaf_strip(name, path, width, thickness, coll, mat, bs):
    """Bent constant-width metal strip with a raised crown; path is XYZ mm."""
    left, right = [], []
    for i, p in enumerate(path):
        a, b = path[max(0, i - 1)], path[min(len(path) - 1, i + 1)]
        tx, ty = _unit((b[0] - a[0], b[1] - a[1]))
        left.append((p[0] - ty * width / 2, p[1] + tx * width / 2, p[2]))
        right.append((p[0] + ty * width / 2, p[1] - tx * width / 2, p[2]))
    n = len(path)
    verts = left + right + \
            [(x, y, z - thickness) for x, y, z in left] + \
            [(x, y, z - thickness) for x, y, z in right]
    L, R, LB, RB = 0, n, 2 * n, 3 * n
    faces = []
    for i in range(n - 1):
        j = i + 1
        faces += [(L + i, L + j, R + j, R + i),
                  (LB + j, LB + i, RB + i, RB + j),
                  (L + i, LB + i, LB + j, L + j),
                  (R + j, RB + j, RB + i, R + i)]
    faces += [(L, R, RB, LB),
              (L + n - 1, LB + n - 1, RB + n - 1, R + n - 1)]
    return _new_mesh(name, verts, faces, coll, mat, bs)


def add_leaf_mount(half, tab_centers, D, coll, mats, bs, plate_z=None):
    """Add paired butterfly leaf springs and silicone contact pads.

    Each tab may be ``(x,y)`` or ``{"xy":(x,y), "tangent":(x,y),
    "normal":(x,y)}``; absent directions are derived from the outline centroid.
    Geometry represents an explicitly estimated, render-readable layout, not an
    unpublished Evo75 manufacturing drawing. Returns station metadata.
    """
    m = D["gasket"]["leaf_mount"]
    pz = plate_z or D["stack"]["plate_z"]
    plate_bottom = pz[0]
    centroid = _mean(D["case"]["outline_poly_for_mount"]) if "outline_poly_for_mount" in D["case"] else None
    if centroid is None:
        # Tab positions normally surround the key field; their average is a
        # stable local origin for outward normal estimates.
        points = [t["xy"] if isinstance(t, dict) else t for t in tab_centers]
        centroid = _mean(points)
    result = []
    for i, item in enumerate(tab_centers):
        if isinstance(item, dict):
            x, y = item["xy"]
            normal = _unit(item.get("normal", (x - centroid[0], y - centroid[1])))
            tangent = _unit(item.get("tangent", (-normal[1], normal[0])))
        else:
            x, y = item
            normal = _unit((x - centroid[0], y - centroid[1]))
            tangent = (-normal[1], normal[0])
        pad_z0 = plate_bottom - m["pad_top_gap_mm"] - m["pad_t_mm"]
        pad_xy = (x, y)
        pad_angle = math.degrees(math.atan2(tangent[1], tangent[0]))
        pad = bs.box(f"{half}_leaf_pad{i}", x, y, pad_z0,
                     pad_z0 + m["pad_t_mm"], m["pad_w_mm"], m["pad_d_mm"],
                     coll, mats[m["pad_material"]], rot_z=pad_angle)
        if m.get("pad_edge_mm", 0) and hasattr(bs, "bevel"):
            bs.bevel(pad, m["pad_edge_mm"], 2)
        spring_z = pad_z0 - m["leaf_contact_gap_mm"] - m["leaf_t_mm"]
        pair_meta = []
        for side in (-1, 1):
            # Two mirrored shallow S/V leaves cradle each silicone pad. The
            # controlled stations make the flex profile easy to reproduce in CAD.
            sep = m["pair_sep_mm"] / 2 * side
            p0 = (x - normal[0] * m["leaf_span_mm"] / 2 + tangent[0] * sep,
                  y - normal[1] * m["leaf_span_mm"] / 2 + tangent[1] * sep,
                  spring_z)
            p1 = (x - normal[0] * m["leaf_span_mm"] * 0.12 + tangent[0] * sep * 0.5,
                  y - normal[1] * m["leaf_span_mm"] * 0.12 + tangent[1] * sep * 0.5,
                  spring_z + m["leaf_crown_h_mm"])
            p2 = (x + normal[0] * m["leaf_span_mm"] * 0.18 + tangent[0] * sep * 1.2,
                  y + normal[1] * m["leaf_span_mm"] * 0.18 + tangent[1] * sep * 1.2,
                  spring_z + m["leaf_crown_h_mm"] * 0.72)
            p3 = (x + normal[0] * m["leaf_span_mm"] / 2 + tangent[0] * sep * 1.5,
                  y + normal[1] * m["leaf_span_mm"] / 2 + tangent[1] * sep * 1.5,
                  spring_z)
            path = (p0, p1, p2, p3)
            ob = _leaf_strip(f"{half}_leaf{i}_{'a' if side < 0 else 'b'}",
                            path, m["leaf_w_mm"], m["leaf_t_mm"], coll,
                            mats[m["leaf_material"]], bs)
            pair_meta.append({"side": side, "path_mm": path, "object": ob})
        result.append({"xy_mm": pad_xy, "normal": normal, "tangent": tangent,
                       "pad_z_mm": pad_z0, "pad": pad, "leaves": pair_meta})
    return result


def cut_pcb_flex(pcb, half, centers, D, coll, bs):
    """Boolean narrow paired slots through the 1.2 mm PCB at spring stations."""
    cfg = D["pcb"]["flex_cut"]
    z0, z1 = D["stack"]["pcb_z"]
    cutouts = []
    for i, item in enumerate(centers):
        if isinstance(item, dict):
            x, y = item["xy"]
            tangent = _unit(item.get("tangent", (1.0, 0.0)))
        else:
            x, y = item
            tangent = (1.0, 0.0)
        angle = math.degrees(math.atan2(tangent[1], tangent[0]))
        for side in (-1, 1):
            along_n = (tangent[1], -tangent[0])
            sx = x + along_n[0] * cfg["pair_offset_mm"] * side
            sy = y + along_n[1] * cfg["pair_offset_mm"] * side
            ob = bs.box(f"{half}_pcb_flex{i}_{'a' if side < 0 else 'b'}",
                        sx, sy, z0 - 0.1, z1 + 0.1,
                        cfg["slot_length_mm"], cfg["slot_width_mm"],
                        coll, None, rot_z=angle)
            bs.bool_diff(pcb, ob)
            cutouts.append({"xy_mm": (sx, sy), "length_mm": cfg["slot_length_mm"],
                            "width_mm": cfg["slot_width_mm"], "angle_deg": angle})
    return cutouts


def write_solidworks_handoff(D, keys, geom, derived, path):
    """Write line/arc-ready plan and an estimated side section in mm."""
    import outline as ol

    unit = keys["unit_mm"]
    plans = {}
    for half in "LR":
        edges = D["case"]["outline"][half]
        line_data = ol.lines(edges, keys["keys"], half, unit)
        plans[half] = {
            "units": "mm",
            "origin": "keys_8 half frame",
            "closed_profile": True,
            "entities": [{"type": "line", "name": e["name"],
                          "normal_deg": e["n_deg"],
                          "line_offset_mm": round(line_data[i][1], 4),
                          "end_fillet_radius_mm": e["r"]}
                         for i, e in enumerate(edges)],
            "filleted_outline_vertices_mm": [[round(x, 4), round(y, 4)]
                                              for x, y in geom[half]["outline"]],
            "note": "Line normals/offsets and tangent end radii are the editable CAD recipe; sampled vertices are a check only."
        }
    case = D["case"]["lower_base"]
    handoff = {
        "_doc": "Draft SolidWorks rebuild data derived from blender/design.json. All geometry is estimated render intent until reviewed in CAD.",
        "units": "mm",
        "typing_angle_deg": D["feet"]["typing_angle_deg"],
        "front_case_height_mm": D["case"]["height_mm"],
        "plan_outlines": plans,
        "case_section": {
            "axis": "front_to_back (local +y), z up",
            "profile_stations": case["stations"],
            "entities": [
                {"type": "line", "from": "front_base_tangent", "to": "curve_start", "slope": 0.0},
                {"type": "arc", "from": "curve_start", "to": "rear_tangent", "radius_mm": case["graduated_curve_radius_mm"], "start_y_fraction": case["curve_start_fraction"]},
                {"type": "line", "from": "rear_tangent", "to": "rear_base_edge", "slope": "arc tangent at rear_tangent"}
            ],
            "seam_z_mm": case["seam_z_mm"],
            "lower_loft_stations": case["stations"],
            "actual_per_half_profiles": {
                h: {
                    "loft_stations": derived.get(f"{h}_lower_profile", []),
                    "plan_depth_mm": round(max(p[1] for p in geom[h]["outline"]) - min(p[1] for p in geom[h]["outline"]), 4),
                    "curve_start_fraction": case["curve_start_fraction"],
                    "curve_radius_mm": case["graduated_curve_radius_mm"],
                    "curve_run_mm": round((max(p[1] for p in geom[h]["outline"]) - min(p[1] for p in geom[h]["outline"])) * (1.0 - case["curve_start_fraction"]), 4),
                    "arc_rise_mm": round(case["graduated_curve_radius_mm"] - math.sqrt(case["graduated_curve_radius_mm"] ** 2 - ((max(p[1] for p in geom[h]["outline"]) - min(p[1] for p in geom[h]["outline"])) * (1.0 - case["curve_start_fraction"])) ** 2), 4)
                } for h in "LR"
            }
        },
        "mount": D["gasket"]["leaf_mount"],
        "pcb_flex": D["pcb"]["flex_cut"],
        "derived": derived
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(handoff, f, indent=2)
    return handoff
