"""3x2 contact sheet of the v1 drafts -> renders/review/v1_contact.jpg

    python blender/contact_sheet.py
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "renders", "stills", "v1", "draft")
OUT = os.path.join(ROOT, "renders", "review", "v1_contact.jpg")

NAMES = ["01_hero", "02_top", "03_plinth", "04_gull", "05_underside", "06_hub"]
CELL_W, CELL_H = 480, 600
PAD, LABEL_H = 12, 28

img = Image.new("RGB", (3 * CELL_W + 4 * PAD, 2 * (CELL_H + LABEL_H) + 3 * PAD),
                (24, 24, 26))
d = ImageDraw.Draw(img)
for i, name in enumerate(NAMES):
    cx, cy = PAD + (i % 3) * (CELL_W + PAD), PAD + (i // 3) * (CELL_H + LABEL_H + PAD)
    p = os.path.join(SRC, name + ".png")
    if os.path.exists(p):
        img.paste(Image.open(p).resize((CELL_W, CELL_H)), (cx, cy))
    else:
        d.rectangle([cx, cy, cx + CELL_W, cy + CELL_H], fill=(60, 40, 40))
    d.text((cx + 4, cy + CELL_H + 6), f"{i+1}  {name[3:]}", fill=(200, 200, 200))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, quality=90)
print("wrote", OUT)
