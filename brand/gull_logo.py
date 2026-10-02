"""Chasm gull mark drafts: two mirrored wings from one vertex (split: one wing per half).

    python brand/gull_logo.py   -> brand/gull_drafts.svg / .png

Each wing is one cubic Bezier from the vertex (0, 0) to the wing tip, y up.
Variants differ only in control points, so a chosen one feeds CAD/Blender as numbers.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# name: (c1, c2, tip) for the RIGHT wing; left wing = mirror in x
VARIANTS = {
    "A arch":  ((2, 9), (10, 12), (16, 5)),
    "B swept": ((3, 7), (12, 10), (20, 2)),
    "C gull":  ((1, 6), (8, 10), (12, 8)),  # chosen 2026-10-01
}


def wing_path(c1, c2, tip, sx):
    f = lambda p: f"{sx * p[0]:.2f},{-p[1]:.2f}"
    return f"M0,0 C{f(c1)} {f(c2)} {f(tip)}"


def svg(stroke=2.2, cell=60):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cell * len(VARIANTS)} 40" width="{cell * len(VARIANTS) * 4}" height="160">',
           '<rect width="100%" height="100%" fill="white"/>']
    for i, (name, (c1, c2, tip)) in enumerate(VARIANTS.items()):
        cx = cell * i + cell / 2
        out.append(f'<g transform="translate({cx},26)" fill="none" stroke="black" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">')
        out += [f'<path d="{wing_path(c1, c2, tip, s)}"/>' for s in (1, -1)]
        out.append("</g>")
        out.append(f'<text x="{cx}" y="37" font-size="3.2" text-anchor="middle" font-family="sans-serif">{name}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    p = os.path.join(HERE, "gull_drafts.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg())
    import fitz
    fitz.open(p).load_page(0).get_pixmap().save(os.path.join(HERE, "gull_drafts.png"))
    print(p)
