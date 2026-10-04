"""Compose Figure 1 steps 4-6 (1400 x 900) from regions of the full-page screenshot taken by capture.mjs.

  python docs/screenshots/compose.py docs/screenshots
Each composite stacks two regions of the same page state (labelled A and B) on a white 1400 x 900 canvas,
scaled down only if needed to fit.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

D = Path(sys.argv[1])
log = json.loads((D / "shots_log.json").read_text(encoding="utf-8"))
B = log["boxes"]
full = Image.open(D / "_full_spline3.png").convert("RGB")
W, H, PAD = 1400, 900, 14
try:
    FONT = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
except OSError:
    try:
        FONT = ImageFont.truetype("arialbd.ttf", 22)
    except OSError:
        FONT = ImageFont.load_default()


def region(x0, y0, x1, y1):
    return full.crop((int(x0), int(y0), int(x1), int(y1)))


def panel_x():
    p = B["panel"]; return p["x"] + 4, p["x"] + p["w"] - 4


def compose(name, parts):
    canvas = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(canvas)
    avail = H - PAD * (len(parts) + 1)
    total = sum(im.height for _, im in parts); maxw = max(im.width for _, im in parts)
    s = min(1.0, avail / total, (W - 2 * PAD - 40) / maxw)
    y = max(PAD, (H - sum(round(im.height * s) for _, im in parts) - PAD * (len(parts) - 1)) // 2)
    for lab, im in parts:
        im2 = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) if s < 1 else im
        x = (W - im2.width) // 2
        canvas.paste(im2, (x, y)); d.rectangle((x - 1, y - 1, x + im2.width, y + im2.height), outline="#bbbbbb")
        d.text((x - 32, y + 2), lab, fill="#b23a48", font=FONT)
        y += im2.height + PAD
    canvas.save(D / f"{name}.png")
    print(name, "scale", round(s, 3))


x0, x1 = panel_x()
# 4: headline with the non-linearity test + coefficient table (A); pooled curve with 95% band (B)
hd, cf = B["headline"], B["coefTable"]
cv = B["curve"]
compose("step4", [("A", region(x0, hd["y"] - 6, x1, cf["y"] + cf["h"] + 6)),
                  ("B", region(cv["x"] - 6, cv["y"] - 6, cv["x"] + cv["w"] + 6, cv["y"] + cv["h"] + 6))])
# 5: heterogeneity and tests table (A); decorrelated residual plot (B)
tt, rs = B["testsTable"], B["resid"]
compose("step5", [("A", region(x0, tt["y"] - 34, x1, tt["y"] + tt["h"] + 6)),
                  ("B", region(rs["x"] - 6, rs["y"] - 6, rs["x"] + rs["w"] + 6, rs["y"] + rs["h"] + 6))])
# 6: predictions at chosen doses (A); export buttons (B)
pt, ex = B["predTable"], B["export"]
pi = B["predInputs"]
compose("step6", [("A", region(pi["x"] - 8, pi["y"] - 44, pi["x"] + pi["w"] + 8, pi["y"] + pi["h"] + 8)),
                  ("B", region(x0, pt["y"] - 34, x1, pt["y"] + pt["h"] + 6)),
                  ("C", region(x0, ex["y"] - 8, x1, ex["y"] + ex["h"] + 8))])
