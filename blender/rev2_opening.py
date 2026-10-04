"""Numpy-only replacement for outline.opening, usable in Blender's Python.

The returned polygon is a CCW polyline in millimetres in the selected half frame.
Raster coordinates are cell centres; the boundary is traced on cell edges.
"""
import math


def _edt_1d(values):
    """Exact squared Euclidean distance transform of a 1D cost array."""
    import numpy as np

    n = len(values)
    finite = np.flatnonzero(values < 1.0e19)
    if not len(finite):
        return np.full(n, 1.0e20, dtype=np.float64)
    v = np.empty(len(finite), dtype=np.int32)
    z = np.empty(len(finite) + 1, dtype=np.float64)
    k = 0
    v[0] = finite[0]
    z[0], z[1] = -1.0e30, 1.0e30
    for q0 in finite[1:]:
        q = int(q0)
        while True:
            p = int(v[k])
            s = ((values[q] + q * q) - (values[p] + p * p)) / (2.0 * (q - p))
            if s > z[k] or k == 0:
                break
            k -= 1
        if s <= z[k] and k == 0:
            # First site dominates all earlier sites.
            v[0] = q
            z[1] = 1.0e30
        else:
            k += 1
            v[k] = q
            z[k] = s
            z[k + 1] = 1.0e30
    k = 0
    out = np.empty(n, dtype=np.float64)
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        p = int(v[k])
        out[q] = (q - p) * (q - p) + values[p]
    return out


def _edt(features):
    """Squared distance to True cells, with a padded exterior handled by caller."""
    import numpy as np

    h, w = features.shape
    inf = 1.0e20
    f = np.where(features, 0.0, inf).astype(np.float64)
    tmp = np.empty_like(f)
    for y in range(h):
        tmp[y, :] = _edt_1d(f[y, :])
    out = np.empty_like(f)
    for x in range(w):
        out[:, x] = _edt_1d(tmp[:, x])
    return out


def _rdp(points, epsilon):
    """Ramer-Douglas-Peucker for an open point chain."""
    if len(points) <= 2:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    best_i, best_d = 0, -1.0
    for i in range(1, len(points) - 1):
        x, y = points[i]
        if den:
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / den))
            d = (x - (ax + t * dx)) ** 2 + (y - (ay + t * dy)) ** 2
        else:
            d = (x - ax) ** 2 + (y - ay) ** 2
        if d > best_d:
            best_i, best_d = i, d
    if best_d <= epsilon * epsilon:
        return [points[0], points[-1]]
    return _rdp(points[:best_i + 1], epsilon)[:-1] + _rdp(points[best_i:], epsilon)


def _contour(mask, x0, y0, px):
    """Trace directed cell-boundary edges, producing a CCW outer boundary."""
    import numpy as np

    h, w = mask.shape
    edges = []
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if y == 0 or not mask[y - 1, x]:
            edges.append(((x, y), (x + 1, y)))
        if x == w - 1 or not mask[y, x + 1]:
            edges.append(((x + 1, y), (x + 1, y + 1)))
        if y == h - 1 or not mask[y + 1, x]:
            edges.append(((x + 1, y + 1), (x, y + 1)))
        if x == 0 or not mask[y, x - 1]:
            edges.append(((x, y + 1), (x, y)))
    outgoing = {}
    for a, b in edges:
        outgoing.setdefault(a, []).append(b)
    loops = []
    unused = set(edges)
    while unused:
        first = next(iter(unused))
        start, cur = first
        chain = [start]
        prev = start
        unused.remove(first)
        guard = len(edges) + 1
        while cur != start and guard:
            chain.append(cur)
            candidates = [q for q in outgoing.get(cur, ()) if (cur, q) in unused]
            if not candidates:
                break
            # At a diagonal-touch vertex, favor a left turn to stay around the
            # same occupied cell with its interior on the left.
            incoming = (cur[0] - prev[0], cur[1] - prev[1])
            def rank(q):
                d = (q[0] - cur[0], q[1] - cur[1])
                cross = incoming[0] * d[1] - incoming[1] * d[0]
                dot = incoming[0] * d[0] + incoming[1] * d[1]
                return (0 if cross > 0 else 1 if dot > 0 else 2,)
            nxt = min(candidates, key=rank)
            unused.remove((cur, nxt))
            prev, cur = cur, nxt
            guard -= 1
        if cur == start and len(chain) >= 4:
            loops.append(chain)
    if len(loops) != 1:
        loop_areas = [sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(q, q[1:] + q[:1])) / 2 for q in loops]
        loop_boxes = [(min(x for x, _ in q), max(x for x, _ in q), min(y for _, y in q), max(y for _, y in q)) for q in loops]
        raise AssertionError("opening must be one region without holes; contours=%d areas=%r boxes=%r" % (len(loops), loop_areas, loop_boxes))
    loop = loops[0]
    # Convert raster-edge vertices to world mm.
    poly = [(x0 + x * px, y0 + y * px) for x, y in loop]
    # Split closed chain at a farthest vertex pair, simplify each open arc,
    # then restore the closed CCW polygon.
    i0 = 0
    i1 = max(range(1, len(poly)), key=lambda i: (poly[i][0] - poly[i0][0]) ** 2 + (poly[i][1] - poly[i0][1]) ** 2)
    chain_a = poly[i0:i1 + 1]
    chain_b = poly[i1:] + poly[:i0 + 1]
    simplified = _rdp(chain_a, px * 0.45)[:-1] + _rdp(chain_b, px * 0.45)[:-1]
    if len(simplified) < 3:
        raise AssertionError("opening contour collapsed during simplification")
    area2 = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(simplified, simplified[1:] + simplified[:1]))
    if area2 < 0:
        simplified.reverse()
    return simplified


def opening(design, keys, half, px=None):
    """Return one CCW key opening polyline for ``half`` in local mm coordinates.

    Expands each rotated pitch box by the configured clearance, performs a
    Euclidean binary closing, rounds small corners, and traces the union. The
    optional ``px`` is the raster pitch in mm; default is case.opening_px_mm or
    0.20 mm. This implementation uses only Blender's bundled numpy and stdlib.
    """
    import numpy as np

    c = design["case"]
    unit = float(keys["unit_mm"])
    px = float(px if px is not None else c.get("opening_px_mm", 0.20))
    if px <= 0:
        raise ValueError("opening raster pitch must be positive")
    clearance = float(c["opening_clearance_mm"]) + float(c.get("opening_sampling_guard_mm", 0.0))
    close_r = float(c["opening_close_r_mm"])
    round_r = float(c["opening_r_min_mm"])
    ks = [k for k in keys["keys"] if k["half"] == half and not k.get("solid_top")]
    if not ks:
        raise ValueError("no opening keys for half " + half)
    rects = []
    for k in ks:
        w = float(k["w_u"]) * unit + 2.0 * clearance
        h = unit + 2.0 * clearance
        a = math.radians(float(k["rot_deg"]))
        co, si = math.cos(a), math.sin(a)
        rect = [(k["x_mm"] + co * x - si * y, k["y_mm"] + si * x + co * y)
                for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        rects.append((k, rect))
    pad = close_r + round_r + 2.0 + 3.0 * px
    x0 = min(p[0] for _, r in rects for p in r) - pad
    y0 = min(p[1] for _, r in rects for p in r) - pad
    x1 = max(p[0] for _, r in rects for p in r) + pad
    y1 = max(p[1] for _, r in rects for p in r) + pad
    wpx = int(math.ceil((x1 - x0) / px))
    hpx = int(math.ceil((y1 - y0) / px))
    # Add padding so erosion distances see a background border on every side.
    border = int(math.ceil((close_r + round_r + 2 * px) / px)) + 2
    x0 -= border * px
    y0 -= border * px
    mask = np.zeros((hpx + 2 * border, wpx + 2 * border), dtype=np.bool_)
    yy, xx = np.ogrid[:mask.shape[0], :mask.shape[1]]
    gx = x0 + (xx + 0.5) * px
    gy = y0 + (yy + 0.5) * px
    for k, _ in rects:
        a = math.radians(float(k["rot_deg"]))
        co, si = math.cos(a), math.sin(a)
        dx, dy = gx - float(k["x_mm"]), gy - float(k["y_mm"])
        lx, ly = co * dx + si * dy, -si * dx + co * dy
        mask |= (np.abs(lx) <= float(k["w_u"]) * unit / 2.0 + clearance) & (np.abs(ly) <= unit / 2.0 + clearance)

    r2 = (close_r / px) ** 2
    # Close the key union: dilate then erode with the same Euclidean disk.
    dilated = _edt(mask) <= r2
    closed = _edt(~dilated) > r2
    if round_r > 0:
        r12 = (round_r / px) ** 2
        eroded = _edt(~closed) > r12
        mask = _edt(eroded) <= r12
    else:
        mask = closed
    poly = _contour(mask, x0, y0, px)
    if len(poly) < 3:
        raise AssertionError("opening contour must have at least three vertices")
    return poly


def area(poly):
    """Signed area in square millimetres; useful for caller-side assertions."""
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
