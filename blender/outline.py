"""Case outlines from keys_8.json + design.json (pure Python, no bpy).

Rev3 case edges carry a ``rounded_rectangle`` record derived from the complete key,
encoder and logo keepout field.  That record produces four straight sides and four
equal-radius tangent arcs.  Legacy support-line edge lists remain supported.

    python blender/outline.py   -> self-check + blender/tmp/outline_check.png
"""
import json, math, os
import rev3_plan

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load():
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    keys = json.load(open(os.path.join(ROOT, design["inputs"]["keys"]), encoding="utf-8"))
    if design.get("case", {}).get("plan"):
        rev3_plan.synchronize_plan(design, keys)
    kv = knob_virtual_key(design, keys)
    if kv:
        keys["keys"].append(kv)
    lv = logo_virtual_key(design, keys)
    if lv:
        keys["keys"].append(lv)
    return design, keys


def knob_xy(design, keys):
    """Keyboard knob centre from the layout's authoritative encoder slot."""
    kb = design.get("knob_kb")
    if not kb:
        return None
    enc = next(e for e in keys["encoders"] if e["half"] == kb["half"])
    return enc["half"], enc["x_mm"], enc["y_mm"]


def logo_xy(design, keys):
    lg = design["logo"]
    right = next(k for k in keys["keys"] if k["id"] == lg["right_key"])
    up = next(k for k in keys["keys"] if k["id"] == lg["up_key"])
    return right["x_mm"] + lg["vertex_x_offset_mm"], up["y_mm"] + lg["vertex_y_offset_mm"]


def logo_virtual_key(design, keys):
    """Solid top reserved above Right; this keepout never enters the opening."""
    if not design["logo"].get("full_right"):
        return None
    x, y = logo_xy(design, keys)
    return {"id": "RLOGO", "half": "R", "label": "LOGO", "w_u": design["logo"]["keepout_mm"] / keys["unit_mm"],
            "x_mm": x, "y_mm": y + design["logo"]["keepout_y_offset_mm"], "rot_deg": 0.0,
            "stab": False, "virtual": True, "solid_top": True}


def knob_virtual_key(design, keys):
    """Square 'key' the size of the knob keepout so case outline + opening wrap the knob."""
    kxy = knob_xy(design, keys)
    if not kxy:
        return None
    half, x, y = kxy
    return {"id": "RKNOB" if half == "R" else "LKNOB", "half": half, "label": "KNOB",
            "w_u": design["knob_kb"]["box_mm"] / keys["unit_mm"], "x_mm": x, "y_mm": y,
            "rot_deg": 0.0, "stab": False, "virtual": True}


def key_rect(k, unit, cap=None):
    """Key footprint corners (pitch box, or cap base of depth `cap` if given), half frame, mm."""
    w = k["w_u"] * unit - (unit - cap if cap else 0)
    h = cap or unit
    a = math.radians(k["rot_deg"]); c, s = math.cos(a), math.sin(a)
    return [(k["x_mm"] + c * x - s * y, k["y_mm"] + s * x + c * y)
            for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def select(keys, half, sel):
    ks = [k for k in keys if k["half"] == half]
    if sel == "all": return ks
    if sel == "straight": return [k for k in ks if abs(k["rot_deg"]) < 1e-6]
    if sel == "angled": return [k for k in ks if abs(k["rot_deg"]) > 1e-6]
    if sel.startswith("not:"): return [k for k in ks if k["id"] not in sel[4:].split(",")]
    return [k for k in ks if k["id"] in sel.split(",")]


def lines(edges, keys, half, unit, inset=0.0):
    """[(unit normal, offset)] per edge; an edge may give a fixed offset `d` instead of keys."""
    out = []
    for e in edges:
        a = math.radians(e["n_deg"]); n = (math.cos(a), math.sin(a))
        if "d" in e:
            out.append((n, e["d"] - inset)); continue
        sup = max(p[0] * n[0] + p[1] * n[1] for k in select(keys, half, e["keys"]) for p in key_rect(k, unit))
        out.append((n, sup + e["bezel"] - inset))
    return out


def _rounded_rectangle_record(edges):
    if not edges:
        return None
    record = edges[0].get("rounded_rectangle")
    if record and len(edges) != record.get("semantic_edge_count", len(edges)):
        # Derived profiles such as the cropped stainless weight deliberately
        # remove/replace support edges; retain their established line recipe.
        return None
    return record


def _rounded_rectangle(edges, half, inset, seg_deg, r_min):
    """Return a fixed-cardinality CCW rounded rectangle and semantic stations.

    Arc cardinality is taken from the outer plan rather than recomputed from an
    inset radius.  Shell, cavity, plate, PCB and lower-loft rings therefore stay
    vertex-compatible even at the largest configured inset.
    """
    q = _rounded_rectangle_record(edges)
    cx, cy = q["center_mm"]
    width = q["width_mm"] - 2.0 * inset
    depth = q["depth_mm"] - 2.0 * inset
    radius = max(q["corner_radius_mm"] - inset, r_min)
    if width <= 2.0 * radius or depth <= 2.0 * radius:
        raise ValueError("rounded rectangle inset collapses its straight runs")
    nseg = int(q.get("arc_segments", max(2, math.ceil(90.0 / seg_deg))))
    if nseg < 2:
        raise ValueError("rounded rectangle needs at least two segments per corner")
    xmin, xmax = cx - width / 2.0, cx + width / 2.0
    ymin, ymax = cy - depth / 2.0, cy + depth / 2.0
    centers = ((xmin + radius, ymin + radius, math.pi, 1.5 * math.pi),
               (xmax - radius, ymin + radius, -0.5 * math.pi, 0.0),
               (xmax - radius, ymax - radius, 0.0, 0.5 * math.pi),
               (xmin + radius, ymax - radius, 0.5 * math.pi, math.pi))
    pts = []
    for x, y, a0, a1 in centers:
        pts.extend((x + radius * math.cos(a0 + (a1 - a0) * j / nseg),
                    y + radius * math.sin(a0 + (a1 - a0) * j / nseg))
                   for j in range(nseg + 1))

    # build_scene assigns feet and a legacy logo construction from these eight
    # stations.  Keep those semantic roles without introducing extra plan edges.
    if half == "L":
        V = [(xmin, ymin), (cx, ymin), (xmax, ymin), (xmax, cy),
             (xmax, ymax), (cx, ymax), (xmin, ymax), (xmin, cy)]
    else:
        V = [(xmin, ymin), (cx, ymin), (xmax, ymin), (xmax, cy),
             (xmax, ymax), (xmax, ymax), (cx, ymax), (xmin, ymax)]
    return pts, V


def intersect(l1, l2):
    (a1, b1), d1 = l1; (a2, b2), d2 = l2
    det = a1 * b2 - a2 * b1
    return ((d1 * b2 - d2 * b1) / det, (a1 * d2 - a2 * d1) / det)


def outline(edges, keys, half, unit, inset=0.0, seg_deg=3.0, r_min=0.0):
    """CCW closed polyline [(x, y)] mm with filleted vertices. `inset` pulls every edge in
    (convex radii shrink by inset, concave grow, so the inset curve stays parallel)."""
    L = lines(edges, keys, half, unit, inset)
    if _rounded_rectangle_record(edges):
        pts, V = _rounded_rectangle(edges, half, inset, seg_deg, r_min)
        return pts, V, L
    m = len(L)
    V = [intersect(L[i], L[(i + 1) % m]) for i in range(m)]
    pts = []
    for i in range(m):
        n_a, n_b = L[i][0], L[(i + 1) % m][0]
        da, db = (-n_a[1], n_a[0]), (-n_b[1], n_b[0])  # CCW travel directions
        turn = math.atan2(da[0] * db[1] - da[1] * db[0], da[0] * db[0] + da[1] * db[1])
        r = max(edges[i]["r"] + (inset if turn < 0 else -inset), r_min)
        t = r * math.tan(abs(turn) / 2)
        vx, vy = V[i]
        ta = (vx - da[0] * t, vy - da[1] * t)
        sgn = 1 if turn > 0 else -1
        cx, cy = ta[0] - sgn * da[1] * r, ta[1] + sgn * da[0] * r
        a0 = math.atan2(ta[1] - cy, ta[0] - cx)
        nseg = max(2, int(abs(math.degrees(turn)) / seg_deg) + 1)
        pts += [(cx + r * math.cos(a0 + turn * j / nseg), cy + r * math.sin(a0 + turn * j / nseg)) for j in range(nseg + 1)]
    return pts, V, L


def point_in(poly, p):
    x, y = p; inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): inside = not inside
    return inside


def dist_to_poly(poly, p):
    best = 1e9
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((p[0] - x1) * dx + (p[1] - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(p[0] - x1 - t * dx, p[1] - y1 - t * dy))
    return best


def opening(design, keys, half, px=None):
    """Key-stagger opening, generated with bundled NumPy and standard Python."""
    from rev2_opening import opening as generate
    return generate(design, keys, half, px)


def check(design, keys):
    """Every key pitch box inside its outline with >= bezel_min; no fillet overruns its edge."""
    unit = keys["unit_mm"]; report = {}
    for half in "LR":
        edges = design["case"]["outline"][half]
        poly, V, L = outline(edges, keys["keys"], half, unit)
        corners = [p for k in select(keys["keys"], half, "all") if not k.get("solid_top") for p in key_rect(k, unit)]
        assert all(point_in(poly, p) for p in corners), f"{half}: key outside outline"
        bez = min(dist_to_poly(poly, p) for p in corners)
        assert bez >= design["case"]["bezel_min_mm"] - 0.05, f"{half}: bezel {bez:.2f} < min"
        for (x1, y1), (x2, y2), (x3, y3) in zip(poly, poly[1:] + poly[:1], poly[2:] + poly[:2]):
            assert (x2 - x1) * (x3 - x2) + (y2 - y1) * (y3 - y2) > -1e-9, f"{half}: fillet overruns an edge near ({x2:.1f},{y2:.1f})"
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        report[half] = {"bbox_mm": [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2)],
                        "size_mm": [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)],
                        "min_bezel_mm": round(bez, 2),
                        "vertices_mm": [[e["name"], round(x, 3), round(y, 3), e["r"]] for e, (x, y) in zip(edges, V)]}
        if _rounded_rectangle_record(edges):
            q = _rounded_rectangle_record(edges)
            report[half]["rounded_rectangle"] = {
                "center_mm": q["center_mm"], "width_mm": q["width_mm"],
                "depth_mm": q["depth_mm"], "corner_radius_mm": q["corner_radius_mm"],
                "sample_count": len(poly)}
    return report


if __name__ == "__main__":
    import importlib.util
    import subprocess
    import sys
    script = os.path.join(HERE, 'regenerate_opening.py')
    if importlib.util.find_spec('numpy') is None:
        sys.exit(subprocess.call(['D:/Apps/Blender/current/blender.exe', '-b', '--factory-startup',
            '--python-exit-code', '1', '--python', script]))
    import runpy
    runpy.run_path(script, run_name='__main__')
