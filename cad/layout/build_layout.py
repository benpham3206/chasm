"""Chasm layout generator: Duo-style split Alice, 68 keys (second B on the right, no left Fn).

    python cad/layout/build_layout.py --angle 8      # Duo-like (measured ~8 deg from QK plate photo)
    python cad/layout/build_layout.py --angle 12     # classic TGR Alice

Outputs in cad/layout/out/:
    keys_<a>.json        source of truth for CAD: per key centre (mm), rotation, size, half
    kle_<a>.json         raw KLE (paste into keyboard-layout-editor.com / ai03 plate gen / kbplacer)
    preview_<a>.png      both halves, labelled
    print_<a>_<half>.svg 1:1 printable (print at 100 %, check the 50 mm scale bar)

Geometry: classic Alice row staggers and block placement recovered from the TeaQueen
KiCad PCB (MIT, github.com/gregandcin/teaqueen); the inner (alpha) block of each half is
re-rotated about the corner where it meets the outer block, so any angle keeps the
blocks attached. Key set follows the QK Alice Duo plate (macro column, arrows right).
"""
import argparse
import json
import math
import os

U = 19.05  # mm per key unit
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# Positions are in key units, screen convention (x right, y down), in each half's own frame.
# Outer block: unrotated. (x of left edge, y of top edge, width, label)
LEFT_OUTER = [
    # 2026-10-04: macro column moved down one row; the freed top-left slot holds the knob
    (-1.25, 1.1, 1, "M1"), (-1.25, 2.1, 1, "M2"), (-1.25, 3.1, 1, "M3"), (-1.25, 4.1, 1, "M4"),
    (0.6, 0.1, 1, "`"), (1.6, 0.1, 1, "1"), (2.6, 0.0, 1, "2"),
    (0.35, 1.1, 1.5, "Tab"), (1.85, 1.1, 1, "Q"),
    (0.2, 2.1, 1.75, "Caps"), (1.95, 2.1, 1, "A"),
    (0.0, 3.1, 2.25, "Shift"), (2.25, 3.1, 1, "Z"),
    (0.2, 4.1, 1.5, "Ctrl"), (1.7, 4.1, 1, "Win"),
]
# Inner block, local frame (x left edge, row index, width, label)
LEFT_INNER = [
    (0.5, 0, 1, "3"), (1.5, 0, 1, "4"), (2.5, 0, 1, "5"), (3.5, 0, 1, "6"),
    (0.0, 1, 1, "W"), (1.0, 1, 1, "E"), (2.0, 1, 1, "R"), (3.0, 1, 1, "T"),
    (0.25, 2, 1, "S"), (1.25, 2, 1, "D"), (2.25, 2, 1, "F"), (3.25, 2, 1, "G"),
    (0.75, 3, 1, "X"), (1.75, 3, 1, "C"), (2.75, 3, 1, "V"), (3.75, 3, 1, "B"),
    (0.6648, 4.062, 1.5, "Alt"), (2.25, 4, 2.0, "Space"),
]
RIGHT_INNER = [
    (0.75, 0, 1, "7"), (1.75, 0, 1, "8"), (2.75, 0, 1, "9"), (3.75, 0, 1, "0"),
    (0.25, 1, 1, "Y"), (1.25, 1, 1, "U"), (2.25, 1, 1, "I"), (3.25, 1, 1, "O"),
    (0.5, 2, 1, "H"), (1.5, 2, 1, "J"), (2.5, 2, 1, "K"), (3.5, 2, 1, "L"),
    (0.0, 3, 1, "B"), (1.0, 3, 1, "N"), (2.0, 3, 1, "M"), (3.0, 3, 1, ","),
    (0.0, 4, 2.75, "Space"), (2.85, 4.05, 1.5, "Fn"),
]
RIGHT_OUTER = [
    (0.27, 0.0, 1, "-"), (1.27, 0.1, 1, "="), (2.27, 0.1, 2, "Bksp"),
    (0.0, 1.05, 1, "P"), (1.02, 1.1, 1, "["), (2.02, 1.1, 1, "]"), (3.02, 1.1, 1.5, "\\"),
    (0.47, 2.1, 1, ";"), (1.47, 2.1, 1, "'"), (2.47, 2.1, 2.25, "Enter"),
    # classic Alice right row (second B): ". /" join the outer block, so Shift + arrows sit 1u further right
    (0.17, 3.1, 1, "."), (1.17, 3.1, 1, "/"), (2.17, 3.1, 1.75, "Shift"), (3.92, 3.1, 1, "Up"),
    (2.92, 4.1, 1, "Left"), (3.92, 4.1, 1, "Down"), (4.92, 4.1, 1, "Right"),
]
# Block placement from TeaQueen at 12 deg (screen rotation, + = clockwise on screen):
# inner local origin relative to outer origin, and the pivot (local) used for re-rotation.
PLACE = {
    "L": {"origin": (3.319, 0.0164), "ref_rot": 12.0, "sign": +1, "pivot": (0.5, 0.0)},
    "R": {"origin": (-4.5687, 1.026), "ref_rot": -12.0, "sign": -1, "pivot": (4.75, 0.0)},
}
ENCODER = {"L": (-1.25 + 0.5, 0.1 + 0.5)}  # knob centre: top-left slot of the left half (2026-10-04), units


def rot(px, py, deg):
    a = math.radians(deg)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


def build(angle):
    keys = []
    for half, outer, inner in (("L", LEFT_OUTER, LEFT_INNER), ("R", RIGHT_OUTER, RIGHT_INNER)):
        p = PLACE[half]
        for x, y, w, lab in outer:
            keys.append({"half": half, "label": lab, "w": w, "cx": x + w / 2, "cy": y + 0.5, "rot": 0.0})
        # pivot in screen units at the reference rotation, then re-rotate the block about it
        qx, qy = p["pivot"]
        ox, oy = p["origin"]
        rx, ry = rot(qx, qy, p["ref_rot"])
        pivot = (ox + rx, oy + ry)
        new_rot = p["sign"] * angle
        for x, y, w, lab in inner:
            lx, ly = x + w / 2 - qx, y + 0.5 - qy
            dx, dy = rot(lx, ly, new_rot)
            keys.append({"half": half, "label": lab, "w": w, "cx": pivot[0] + dx, "cy": pivot[1] + dy,
                         "rot": new_rot, "pivot": pivot, "unrot": (pivot[0] + lx, pivot[1] + ly)})
    return keys


CENTRES = {}


def to_mm(keys):
    """Per-half world frame for CAD: mm, y UP, origin at the half's key-area bbox centre,
    rotation CCW positive."""
    out = []
    for half in ("L", "R"):
        hk = [k for k in keys if k["half"] == half]
        corners = []
        for k in hk:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    dx, dy = rot(sx * k["w"] / 2, sy * 0.5, k["rot"])
                    corners.append((k["cx"] + dx, k["cy"] + dy))
        cx = (min(c[0] for c in corners) + max(c[0] for c in corners)) / 2
        cy = (min(c[1] for c in corners) + max(c[1] for c in corners)) / 2
        span = (max(c[0] for c in corners) - min(c[0] for c in corners),
                max(c[1] for c in corners) - min(c[1] for c in corners))
        CENTRES[half] = (cx, cy)
        for i, k in enumerate(hk):
            out.append({"id": f"{half}{i:02d}", "half": half, "label": k["label"], "w_u": k["w"],
                        "x_mm": round((k["cx"] - cx) * U, 3), "y_mm": round(-(k["cy"] - cy) * U, 3),
                        "rot_deg": -k["rot"], "stab": k["w"] >= 2})
        print(f"{half}: {len(hk)} keys, key area {span[0] * U:.1f} x {span[1] * U:.1f} mm")
    return out


def kle(keys, angle):
    """Raw KLE: one key per row so every key resets its own rotation origin."""
    rows = []
    for half, x_off in (("L", 0.0), ("R", 14.0)):
        for k in [k for k in keys if k["half"] == half]:
            props = {"r": k["rot"], "rx": 0, "ry": 0}
            if k["rot"]:
                px, py = k["pivot"]
                ux, uy = k["unrot"]
                props.update(rx=round(px + x_off, 4), ry=round(py, 4))
                props.update(x=round(ux - k["w"] / 2 - px, 4), y=round(uy - 0.5 - py, 4))
            else:
                props.update(x=round(k["cx"] - k["w"] / 2 + x_off, 4), y=round(k["cy"] - 0.5, 4))
            if k["w"] != 1:
                props["w"] = k["w"]
            rows.append([props, k["label"]])
    return rows


def kle_text(rows):
    def fmt(v):
        return json.dumps(v)
    lines = []
    for props, label in rows:
        body = ",".join(f"{k}:{fmt(v)}" for k, v in props.items())
        lines.append(f"[{{{body}}},{json.dumps(label)}]")
    return ",\n".join(lines)


def svg_half(keys_mm, half, angle, path):
    hk = [k for k in keys_mm if k["half"] == half]
    pad = 10
    xs, ys = [], []  # true keycap corners, so wide halves still fit a Letter page
    for k in hk:
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            dx, dy = rot(sx * k["w_u"] * U / 2, sy * U / 2, k["rot_deg"])
            xs.append(k["x_mm"] + dx); ys.append(k["y_mm"] + dy)
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    W, H = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad + 20
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}mm" height="{H:.1f}mm" viewBox="0 0 {W:.1f} {H:.1f}">',
          f'<text x="{pad}" y="8" font-size="4" font-family="sans-serif">chasm {half} half, {angle} deg, 1:1. Outer: keycap 18 mm; inner dashed: 14 mm switch hole</text>']
    for k in hk:
        cx, cy = k["x_mm"] - x0 + pad, -(k["y_mm"]) - (-y1) + pad + 10
        w = k["w_u"] * U - 1.05
        tf = f'rotate({-k["rot_deg"]:.3f} {cx:.3f} {cy:.3f})'
        el.append(f'<rect x="{cx - w / 2:.3f}" y="{cy - 9:.3f}" width="{w:.3f}" height="18" rx="1.5" '
                  f'fill="none" stroke="black" stroke-width="0.3" transform="{tf}"/>')
        el.append(f'<rect x="{cx - 7:.3f}" y="{cy - 7:.3f}" width="14" height="14" fill="none" stroke="#888" '
                  f'stroke-width="0.2" stroke-dasharray="1,1" transform="{tf}"/>')
        el.append(f'<text x="{cx:.3f}" y="{cy + 1.5:.3f}" font-size="3.5" text-anchor="middle" '
                  f'font-family="sans-serif" transform="{tf}">{k["label"].replace("&", "&amp;").replace("<", "&lt;")}</text>')
    el.append(f'<line x1="{pad}" y1="{H - 6}" x2="{pad + 50}" y2="{H - 6}" stroke="black" stroke-width="0.5"/>'
              f'<text x="{pad + 52}" y="{H - 5}" font-size="3.5" font-family="sans-serif">50 mm: measure to check print scale</text>')
    el.append("</svg>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(el))


def pdf_pages(svgs, path):
    """SVGs -> one PDF, each centred 1:1 on a US Letter landscape page (also prints on A4 at 'Actual size')."""
    import fitz
    out = fitz.open()
    for svg in svgs:
        src = fitz.open("pdf", fitz.open(svg).convert_to_pdf())
        r = src[0].rect
        page = out.new_page(width=792, height=612)
        assert r.width <= 792 and r.height <= 612, f"{svg} larger than page"
        x, y = (792 - r.width) / 2, (612 - r.height) / 2
        page.show_pdf_page(fitz.Rect(x, y, x + r.width, y + r.height), src, 0)
        page.insert_text((x + 42, 612 - 14), "Print at 'Actual size' / 100 % (not 'Fit'). Check the 50 mm bar.", fontsize=8)
    out.save(path)


def preview(keys, angle, path):
    from PIL import Image, ImageDraw, ImageFont
    s = 60  # px per unit
    allx = [k["cx"] + (16 if k["half"] == "R" else 0) for k in keys]
    x0 = min(allx) - 2; y0 = min(k["cy"] for k in keys) - 1.5
    W = int((max(allx) - x0 + 2) * s); H = int((max(k["cy"] for k in keys) - y0 + 1.5) * s)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    f = ImageFont.load_default(size=16)
    for k in keys:
        off = 16 if k["half"] == "R" else 0
        pts = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            dx, dy = rot(sx * (k["w"] / 2 - 0.03), sy * 0.47, k["rot"])
            pts.append(((k["cx"] + off + dx - x0) * s, (k["cy"] + dy - y0) * s))
        fill = "#f3ead8" if k["rot"] else ("#e6e6ef" if not k["label"].startswith("M") else "#dfe8df")
        if k["w"] >= 2:
            fill = "#f2d7d7"
        d.polygon(pts, fill=fill, outline="black", width=2)
        d.text(((k["cx"] + off - x0) * s, (k["cy"] - y0) * s), k["label"], fill="black", font=f, anchor="mm")
    ex, ey = ENCODER["L"]
    d.ellipse(((ex - x0 - 0.35) * s, (ey - y0 - 0.35) * s, (ex - x0 + 0.35) * s, (ey - y0 + 0.35) * s), outline="#555", width=3)
    d.text((10, 8), f"chasm draft layout, inner blocks at +/-{angle} deg. Red = stabilised (>=2u). Circle = knob candidate.",
           fill="black", font=ImageFont.load_default(size=20))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--angle", type=float, default=8.0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    tag = f"{a.angle:g}"
    keys = build(a.angle)
    mm = to_mm(keys)
    encs = []
    for half, (ex, ey) in ENCODER.items():
        cx, cy = CENTRES[half]
        encs.append({"half": half, "x_mm": round((ex - cx) * U, 3), "y_mm": round(-(ey - cy) * U, 3),
                     "slot_u": 1.0, "note": "EC11 knob in a 1u slot (top-left of the left half)"})
    with open(os.path.join(OUT, f"keys_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump({"angle_deg": a.angle, "unit_mm": U, "frame": "per half, mm, y up, origin = key-area bbox centre",
                   "keys": mm, "encoders": encs}, fh, indent=1)
    # KLE / ai03: the knob slot is shown as a 1u key labelled Knob (plate gen cuts a 14 mm hole = EC11 clearance)
    kle_keys = keys + [{"half": h, "label": "Knob", "w": 1.0, "cx": ex, "cy": ey, "rot": 0.0}
                       for h, (ex, ey) in ENCODER.items()]
    with open(os.path.join(OUT, f"kle_{tag}.json"), "w", encoding="utf-8") as fh:
        fh.write(kle_text(kle(kle_keys, a.angle)))
    preview(keys, a.angle, os.path.join(OUT, f"preview_{tag}.png"))
    svgs = [os.path.join(OUT, f"print_{tag}_{half}.svg") for half in ("L", "R")]
    for half, svg in zip(("L", "R"), svgs):
        svg_half(mm, half, a.angle, svg)
    pdf_pages(svgs, os.path.join(OUT, f"print_{tag}.pdf"))
    sizes = {}
    for k in mm:
        sizes[k["w_u"]] = sizes.get(k["w_u"], 0) + 1
    print("total", len(mm), "keys; sizes:", dict(sorted(sizes.items())))


if __name__ == "__main__":
    main()
