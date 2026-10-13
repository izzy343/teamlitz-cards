"""Shrink a rendered card for posting: 780px wide, 64-color PNG. Usage: python3 compress.py in.png out.png"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
w, h = im.size
im = im.resize((780, round(h * 780 / w)), Image.LANCZOS)
im.quantize(colors=64, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(sys.argv[2], optimize=True)
print("wrote", sys.argv[2])
