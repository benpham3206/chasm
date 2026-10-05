"""Runtime derivation of the Rev3 rounded-rectangle half-case plans."""
import hashlib
import json
import math


def _corners(k, unit_mm):
    width = k["w_u"] * unit_mm
    a = math.radians(k.get("rot_deg", 0.0))
    c, s = math.cos(a), math.sin(a)
    return [(k["x_mm"] + c * x - s * y, k["y_mm"] + s * x + c * y)
            for x, y in ((-width / 2, -unit_mm / 2),
                         (width / 2, -unit_mm / 2),
                         (width / 2, unit_mm / 2),
                         (-width / 2, unit_mm / 2))]


def _keepouts(D, keys):
    """Return real layout items plus the encoder and full-gull keepouts once."""
    result = [k for k in keys["keys"] if not k.get("virtual")]
    unit = keys["unit_mm"]
    kb = D.get("knob_kb")
    if kb:
        enc = next(e for e in keys.get("encoders", []) if e["half"] == kb["half"])
        result.append({"id": "LKNOB" if enc["half"] == "L" else "RKNOB",
                       "half": enc["half"], "w_u": kb["box_mm"] / unit,
                       "x_mm": enc["x_mm"], "y_mm": enc["y_mm"], "rot_deg": 0.0})
    logo = D.get("logo", {})
    if logo.get("full_right"):
        right = next(k for k in result if k["id"] == logo["right_key"])
        up = next(k for k in result if k["id"] == logo["up_key"])
        result.append({"id": "RLOGO", "half": "R",
                       "w_u": logo["keepout_mm"] / unit,
                       "x_mm": right["x_mm"] + logo["vertex_x_offset_mm"],
                       "y_mm": up["y_mm"] + logo["vertex_y_offset_mm"] + logo["keepout_y_offset_mm"],
                       "rot_deg": 0.0})
    return result


def synchronize_plan(D, keys):
    """Recompute plan records from design parameters and the current layout.

    ``case.plan`` owns the bezel, hub-radius scale and arc sampling. Stored W/D,
    center and radius are outputs only, so stale generated values cannot control
    geometry. The returned SHA-1 lets the opening generator and scene builder
    prove that they derived the same plan.
    """
    cfg = D["case"]["plan"]
    bezel = float(cfg["bezel_mm"])
    radius = float(D["hub"]["r_plan_mm"]) * float(cfg["hub_radius_scale"])
    arc_segments = int(cfg["arc_segments"])
    if bezel <= 0 or radius <= 0 or arc_segments < 2:
        raise ValueError("case.plan bezel/radius scale/arc segments must be positive")
    keepouts = _keepouts(D, keys)
    derived = {}
    for half in "LR":
        pts = [p for k in keepouts if k["half"] == half
               for p in _corners(k, keys["unit_mm"])]
        xmin, xmax = min(p[0] for p in pts), max(p[0] for p in pts)
        ymin, ymax = min(p[1] for p in pts), max(p[1] for p in pts)
        rec = {
            "center_mm": [(xmin + xmax) / 2.0, (ymin + ymax) / 2.0],
            "width_mm": xmax - xmin + 2.0 * bezel,
            "depth_mm": ymax - ymin + 2.0 * bezel,
            "corner_radius_mm": radius,
            "arc_segments": arc_segments,
            "semantic_edge_count": len(D["case"]["outline"][half]),
            "source_bounds_mm": [xmin, xmax, ymin, ymax],
            "source": "keys_8 pitch boxes plus encoder/logo virtual keepouts"
        }
        if rec["width_mm"] <= 2 * radius or rec["depth_mm"] <= 2 * radius:
            raise ValueError(f"{half} case.plan radius collapses its straight runs")
        derived[half] = rec
        edges = D["case"]["outline"][half]
        edges[0]["rounded_rectangle"] = rec
        inner = next(e for e in edges if e["name"] == "inner")
        if half == "L":
            inner.update(n_deg=0.0, d=rec["center_mm"][0] + rec["width_mm"] / 2.0)
        else:
            inner.update(n_deg=180.0, d=-(rec["center_mm"][0] - rec["width_mm"] / 2.0))
        for edge in edges:
            edge["r"] = radius
    cfg["derived"] = derived
    payload = json.dumps(derived, sort_keys=True, separators=(",", ":"))
    cfg["derived_sha1"] = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    D["case"]["bezel_min_mm"] = bezel - radius * (1.0 - 1.0 / math.sqrt(2.0))
    return cfg["derived_sha1"]

