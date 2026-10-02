"""SSD1306-style 128x64 1-bit status screen for the hub OLED -> blender/tex/oled_status.png.

    python blender/make_oled.py
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 8

img = Image.new("1", (128, 64), 0)
d = ImageDraw.Draw(img)
f = ImageFont = None
try:
    from PIL import ImageFont as _IF
    f = _IF.load_default()
except Exception:
    pass


def text(x, y, s):
    d.text((x, y), s, font=f, fill=1)


def batt(x, y, w, h, pct):
    d.rectangle([x, y, x + w, y + h], outline=1)          # body
    d.rectangle([x + w + 1, y + h // 3, x + w + 2, y + 2 * h // 3], fill=1)  # nub
    iw = int((w - 3) * pct / 100)
    if iw > 0:
        d.rectangle([x + 2, y + 2, x + 1 + iw, y + h - 2], fill=1)


# row 1: left battery
text(3, 4, "L"); batt(14, 3, 30, 9, 82); text(50, 4, "82%")
# BLE + link glyph top right
text(86, 4, "BLE")
d.arc([116, 2, 126, 12], start=200, end=340, fill=1)
d.arc([119, 5, 123, 9], start=200, end=340, fill=1)
d.point([(121, 10)], fill=1); d.point([(121, 11)], fill=1)
# row 2: right battery
text(3, 17, "R"); batt(14, 16, 30, 9, 96); text(50, 17, "96%")
text(86, 17, "2.4G")
# divider
d.line([0, 30, 127, 30], fill=1)
# layer
text(3, 38, "LAYER")
text(36, 36, "BASE")
# frame the layer name
d.rectangle([32, 35, 66, 46], outline=1)
# bottom status line
text(3, 52, "chasm hub v1")
text(100, 52, "OK")

img = img.resize((128 * SCALE, 64 * SCALE), Image.NEAREST)
# pad with black so the image covers the whole window face: the active area
# is a centred rect of window_mm (the emissive face maps uv 0..1 = window)
import json
D = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
o = D["hub"]["oled"]
fx = o["active_mm"][0] / o["window_mm"][0]
fy = o["active_mm"][1] / o["window_mm"][1]
cw, ch = round(img.width / fx), round(img.height / fy)
pad = Image.new("1", (cw, ch), 0)
pad.paste(img, ((cw - img.width) // 2, (ch - img.height) // 2))
os.makedirs(os.path.join(HERE, "tex"), exist_ok=True)
pad.save(os.path.join(HERE, "tex", "oled_status.png"))
print("wrote", os.path.join(HERE, "tex", "oled_status.png"), pad.size)
