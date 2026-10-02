"""Sanity checks for build_layout outputs: keycap overlaps, KLE round-trip, optional reference."""
import json, math, sys, re, os
U = 19.05
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

def poly(k, shrink=0.0):
    w, h = k["w_u"] * U - 1.05 - shrink, 18.0 - shrink
    a = math.radians(k["rot_deg"]); c, s = math.cos(a), math.sin(a)
    return [(k["x_mm"] + dx * c - dy * s, k["y_mm"] + dx * s + dy * c)
            for dx, dy in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2))]

def overlap(p, q):  # separating axis theorem for convex polygons
    for poly_ in (p, q):
        for i in range(4):
            x1, y1 = poly_[i]; x2, y2 = poly_[(i + 1) % 4]
            nx, ny = y2 - y1, x1 - x2
            a = [nx * x + ny * y for x, y in p]; b = [nx * x + ny * y for x, y in q]
            if max(a) <= min(b) or max(b) <= min(a):
                return False
    return True

def min_gap(p, q, steps=40):
    # sampled edge distance (mm) between two keycap outlines
    def pts(P):
        for i in range(4):
            (x1, y1), (x2, y2) = P[i], P[(i + 1) % 4]
            for t in range(steps):
                yield x1 + (x2 - x1) * t / steps, y1 + (y2 - y1) * t / steps
    A = list(pts(p)); B = list(pts(q))
    return min(math.dist(a, b) for a in A for b in B)

def kle_parse(text):
    """Minimal kle-serial: returns key centres (screen units) with rotation."""
    rows = json.loads("[" + re.sub(r"([{,])\s*([a-z]+)\s*:", r'\1"\2":', text) + "]")
    keys = []; cur = dict(x=0, y=0, r=0, rx=0, ry=0)
    for row in rows:
        w = 1
        for item in row:
            if isinstance(item, dict):
                if "r" in item: cur["r"] = item["r"]
                if "rx" in item: cur["rx"] = item["rx"]; cur["x"] = cur["rx"]; cur["y"] = cur["ry"]
                if "ry" in item: cur["ry"] = item["ry"]; cur["x"] = cur["rx"]; cur["y"] = cur["ry"]
                cur["x"] += item.get("x", 0); cur["y"] += item.get("y", 0); w = item.get("w", 1)
            else:
                cx, cy = cur["x"] + w / 2, cur["y"] + 0.5
                a = math.radians(cur["r"]); dx, dy = cx - cur["rx"], cy - cur["ry"]
                keys.append((cur["rx"] + dx * math.cos(a) - dy * math.sin(a),
                             cur["ry"] + dx * math.sin(a) + dy * math.cos(a), cur["r"], w, item))
                cur["x"] += w; w = 1
        cur["y"] += 1; cur["x"] = cur["rx"]
    return keys

for tag in sys.argv[1:] or ["8", "12"]:
    data = json.load(open(os.path.join(OUT, f"keys_{tag}.json")))
    ks = data["keys"]
    bad, tight = [], []
    for half in ("L", "R"):
        hk = [k for k in ks if k["half"] == half]
        for i in range(len(hk)):
            for j in range(i + 1, len(hk)):
                p, q = poly(hk[i]), poly(hk[j])
                if math.dist((hk[i]["x_mm"], hk[i]["y_mm"]), (hk[j]["x_mm"], hk[j]["y_mm"])) > 60:
                    continue
                if overlap(p, q):
                    bad.append((hk[i]["label"], hk[j]["label"]))
                else:
                    g = min_gap(p, q)
                    if g < 0.6:
                        tight.append((hk[i]["label"], hk[j]["label"], round(g, 2)))
    kle = kle_parse(open(os.path.join(OUT, f"kle_{tag}.json")).read())
    print(f"[{tag} deg] keys {len(ks)} | keycap overlaps: {bad or 'none'} | gaps < 0.6 mm: {tight or 'none'} | KLE parsed {len(kle)} keys")
