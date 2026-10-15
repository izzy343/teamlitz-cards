"""Split a tall card into parts GroupMe will accept (tall cards get dropped).
Cuts only on blank background rows, keeping every part at most MAX_H px tall.
Usage: python3 split_card.py in.png out_prefix   -> prints one output path per line
A card already short enough is copied to <out_prefix>.png unchanged."""
import sys, shutil
from PIL import Image

MAX_H = 1100

src, prefix = sys.argv[1], sys.argv[2]
im = Image.open(src)
rgb = im.convert("RGB")
w, h = rgb.size
if h <= MAX_H:
    out = prefix + ".png"
    shutil.copyfile(src, out)
    print(out)
    sys.exit(0)

bg = rgb.getpixel((2, 2))
px = rgb.load()
blank = [all(px[x, y] == bg for x in range(0, w, 2)) for y in range(h)]

cuts, top = [], 0
while h - top > MAX_H:
    # cut in the middle of the tallest blank band (a section break) within the limit
    lo, hi = top + 300, min(top + MAX_H, h - 1)
    best, best_len, y = None, 0, lo
    while y <= hi:
        if blank[y]:
            s = y
            while y <= hi and blank[y]:
                y += 1
            # prefer later bands when nearly as tall, so parts stay balanced
            if y - s >= best_len - 4:
                best, best_len = (s + y) // 2, max(best_len, y - s)
        y += 1
    y = best if best is not None else top + MAX_H  # no gap found: hard cut
    cuts.append(y)
    top = y

edges = [0] + cuts + [h]
for i in range(len(edges) - 1):
    out = f"{prefix}_p{i + 1}.png"
    part = rgb.crop((0, edges[i], w, edges[i + 1]))
    part.quantize(colors=64, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out)
