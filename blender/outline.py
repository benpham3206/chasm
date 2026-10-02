"""Case outlines from keys_8.json + design.json edge lists (pure Python, no bpy).

Each outline edge = a straight line with outward normal `n_deg`, pushed out to touch the
furthest key of `keys` (support function) plus `bezel`. Consecutive lines intersect at
vertices; vertex i (end of edge i) gets a tangent arc of radius `r`. SolidWorks recipe:
sketch the lines, then sketch-fillet each vertex with the same radii.

    python blender/outline.py   -> self-check + blender/tmp/outline_check.png
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load():
    design = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    keys = json.load(open(os.path.join(ROOT, design["inputs"]["keys"]), encoding="utf-8"))
    return design, keys


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


def intersect(l1, l2):
    (a1, b1), d1 = l1; (a2, b2), d2 = l2
    det = a1 * b2 - a2 * b1
    return ((d1 * b2 - d2 * b1) / det, (a1 * d2 - a2 * d1) / det)


def outline(edges, keys, half, unit, inset=0.0, seg_deg=3.0, r_min=0.0):
    """CCW closed polyline [(x, y)] mm with filleted vertices. `inset` pulls every edge in
    (convex radii shrink by inset, concave grow, so the inset curve stays parallel)."""
    L = lines(edges, keys, half, unit, inset)
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


def opening(design, keys, half, px=0.05):
    """Top-frame opening that hugs the key stagger (Duo-style), as CCW polyline mm.
    Recipe (SolidWorks: same steps on sketch regions): union of key pitch boxes grown by
    opening_clearance; morphological closing with opening_close_r (fills inter-block wedges
    and gaps < 2r); convex corners rounded to opening_r_min. Raster at `px` mm, then
    simplified to opening_tol. Needs numpy/scipy/cv2 -> run in system Python, not Blender."""
    import numpy as np, cv2
    from scipy.ndimage import distance_transform_edt as edt
    c = design["case"]; unit = keys["unit_mm"]; cl = c["opening_clearance_mm"]
    ks = select(keys["keys"], half, "all")
    pts = [p for k in ks for p in key_rect(k, unit)]
    pad = c["opening_close_r_mm"] + 5
    x0, y0 = min(p[0] for p in pts) - pad, min(p[1] for p in pts) - pad
    W = int((max(p[0] for p in pts) + pad - x0) / px); H = int((max(p[1] for p in pts) + pad - y0) / px)
    m = np.zeros((H, W), np.uint8)
    for k in ks:
        g = dict(k, w_u=k["w_u"] + 2 * cl / unit)
        r = [((x - x0) / px, (y - y0) / px) for x, y in key_rect(g, unit, unit + 2 * cl)]
        cv2.fillPoly(m, [np.round(np.array(r) * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
    R = c["opening_close_r_mm"] / px; r1 = c["opening_r_min_mm"] / px
    m = edt(m == 0) <= R            # dilate
    m = edt(m) > R                  # erode -> closing
    m = edt(m) > r1                 # erode
    m = edt(m == 0) <= r1           # dilate -> convex corners >= r_min
    cs, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    assert len(cs) == 1, f"{half}: opening has {len(cs)} regions/holes, expected 1"
    cnt = cv2.approxPolyDP(cs[0], c["opening_tol_mm"] / px, True)[:, 0, :]
    poly = [(x0 + (u + 0.5) * px, y0 + (v + 0.5) * px) for u, v in cnt]
    a = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))
    return poly if a > 0 else poly[::-1]


def check(design, keys):
    """Every key pitch box inside its outline with >= bezel_min; no fillet overruns its edge."""
    unit = keys["unit_mm"]; report = {}
    for half in "LR":
        edges = design["case"]["outline"][half]
        poly, V, L = outline(edges, keys["keys"], half, unit)
        corners = [p for k in select(keys["keys"], half, "all") for p in key_rect(k, unit)]
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
    return report


if __name__ == "__main__":
    design, keys = load()
    rep = check(design, keys)
    print(json.dumps(rep, indent=1))
    from PIL import Image, ImageDraw
    S, W, H = 5, 230, 140
    img = Image.new("RGB", (2 * W * S, H * S), "white"); dr = ImageDraw.Draw(img)
    unit = keys["unit_mm"]; c = design["case"]
    for i, half in enumerate("LR"):
        T = lambda p, i=i: ((p[0] + W / 2 + i * W) * S, (H / 2 - p[1]) * S)
        for k in select(keys["keys"], half, "all"):
            dr.polygon([T(p) for p in key_rect(k, unit)], outline=(170, 170, 220))
        edges = c["outline"][half]
        for inset, col in ((0, "black"), (c["bezel_min_mm"] - c["opening_clearance_mm"], (200, 60, 60)), (c["wall_t_mm"], (60, 160, 60))):
            poly, _, _ = outline(edges, keys["keys"], half, unit, inset=inset, r_min=c["opening_r_min_mm"] if inset else 0)
            dr.line([T(p) for p in poly + poly[:1]], fill=col, width=2)

    ops = {}
    for half in "LR":
        op = opening(design, keys, half); ops[half] = [[round(x, 3), round(y, 3)] for x, y in op]
        poly, _, _ = outline(c["outline"][half], keys["keys"], half, unit)
        corners = [p for k in select(keys["keys"], half, "all") for p in key_rect(k, unit)]
        assert all(point_in(op, p) for p in corners), f"{half}: key outside opening"
        assert min(dist_to_poly(op, p) for p in corners) >= c["opening_clearance_mm"] - 0.1, f"{half}: opening clearance"
        frame = min(dist_to_poly(poly, p) for p in op)
        assert frame >= c["opening_frame_min_mm"], f"{half}: frame {frame:.2f} mm < opening_frame_min_mm"
        print(half, "opening pts", len(op), "min frame width", round(frame, 2))
        T = lambda p, i="LR".index(half): ((p[0] + W / 2 + i * W) * S, (H / 2 - p[1]) * S)
        dr.line([T(p) for p in op + op[:1]], fill=(40, 40, 230), width=2)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    src = json.dumps([design["case"], keys["keys"]], sort_keys=True)
    import hashlib
    json.dump({"_doc": "top-frame opening polylines, mm, half frame, CCW; generated by blender/outline.py (do not edit)",
               "source_sha1": hashlib.sha1(src.encode()).hexdigest(), "L": ops["L"], "R": ops["R"]},
              open(os.path.join(HERE, "out", "opening.json"), "w"), indent=0)
    os.makedirs(os.path.join(HERE, "tmp"), exist_ok=True)
    img.save(os.path.join(HERE, "tmp", "outline_check.png"))
