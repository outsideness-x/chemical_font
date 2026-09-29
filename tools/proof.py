#!/usr/bin/env python3
"""Render proof sheets from the built font with HarfBuzz shaping + FreeType.

    .venv/bin/python tools/proof.py out.png "line one" "line two" --size 96
"""

import argparse
import os

import freetype
import numpy as np
import uharfbuzz as hb
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FONT = os.path.join(ROOT, "build", "chemical-Regular.ttf")


def shape(font_path, text, features=None):
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    upem = face.upem
    font.scale = (upem, upem)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return buf.glyph_infos, buf.glyph_positions, upem


def render_lines(lines, size=96, font_path=DEFAULT_FONT, features=None, fg=(20, 20, 20),
                 bg=(250, 247, 240), margin=None, line_height=1.25, width=None, guides=False):
    face = freetype.Face(font_path)
    face.set_char_size(int(size * 64))
    margin = int(size * 0.4) if margin is None else margin
    shaped = [shape(font_path, t, features) for t in lines]
    scale = size / shaped[0][2] if shaped else 1
    widths = [sum(p.x_advance for p in pos) * scale for _, pos, _ in shaped]
    W = width or int(max(widths + [10]) + 2 * margin)
    lh = int(size * line_height)
    H = int(lh * len(lines) + 2 * margin)
    ink = np.zeros((H, W), np.float32)
    guide_rows = []
    for li, (infos, pos, upem) in enumerate(shaped):
        baseline = margin + int(size * 0.95) + li * lh
        if guides:
            for yv in (0, 550, 700):
                guide_rows.append(baseline - int(yv * scale))
        x = margin
        for info, p in zip(infos, pos):
            face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            g = face.glyph
            bm = g.bitmap
            if bm.width and bm.rows:
                arr = np.array(bm.buffer, np.float32).reshape(bm.rows, bm.pitch)[:, : bm.width] / 255.0
                gx = int(round(x + p.x_offset * scale)) + g.bitmap_left
                gy = baseline - int(round(p.y_offset * scale)) - g.bitmap_top
                x0, y0 = max(gx, 0), max(gy, 0)
                x1, y1 = min(gx + bm.width, W), min(gy + bm.rows, H)
                if x1 > x0 and y1 > y0:
                    sub = arr[y0 - gy : y1 - gy, x0 - gx : x1 - gx]
                    ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], sub)
            x += p.x_advance * scale
    fgc = np.array(fg, np.float32)
    bgc = np.array(bg, np.float32)
    img = bgc[None, None, :] * (1 - ink[..., None]) + fgc[None, None, :] * ink[..., None]
    for gy in guide_rows:
        if 0 <= gy < H:
            img[gy, :, :] = img[gy, :, :] * 0.6 + np.array([120, 170, 230]) * 0.4
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("lines", nargs="+")
    ap.add_argument("--size", type=float, default=96)
    ap.add_argument("--font", default=DEFAULT_FONT)
    ap.add_argument("--features", default="")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--guides", action="store_true")
    args = ap.parse_args()
    feats = {}
    for f in filter(None, args.features.split(",")):
        on = not f.startswith("-")
        feats[f.lstrip("-+")] = on
    kw = dict(fg=(232, 64, 44), bg=(12, 12, 12)) if args.dark else {}
    img = render_lines(args.lines, args.size, args.font, feats, guides=args.guides, **kw)
    img.save(args.out)
    print(args.out, img.size)


if __name__ == "__main__":
    main()
