#!/usr/bin/env python3
"""Split the built font into unicode-range web subsets plus a stylesheet.

    .venv/bin/python tools/webfonts.py [build/chemical-Regular.ttf] [out_dir]

A page only downloads the slices whose characters it uses: Latin and
Cyrillic are small, common Hangul (the 2,350 syllables of KS X 1001) comes in
slices, and rare syllables in bigger slices that most pages never touch.
"""

import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "build", "chemical-Regular.ttf")
OUT = os.path.join(ROOT, "build", "web")

LATIN = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) + list(range(0x218, 0x21C))
    + [0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021, 0x2022,
       0x2026, 0x2030, 0x2039, 0x203A, 0x203B, 0x2044, 0x20AC, 0x20A9, 0x20BD, 0x2116, 0x2122,
       0x2190, 0x2191, 0x2192, 0x2193, 0x2212, 0x2605, 0x2606, 0x2661, 0x2665, 0x2713, 0x2717,
       0x2726, 0x2009, 0x237]
)
CYRILLIC = list(range(0x400, 0x530))
JAMO = list(range(0x3000, 0x3040)) + list(range(0x3131, 0x318F)) + list(range(0xFF01, 0xFF60)) + [0x30FB]


def is_common(cp):
    try:
        chr(cp).encode("euc_kr")
        return True
    except UnicodeEncodeError:
        return False


def ranges(cps):
    cps = sorted(set(cps))
    out, start, prev = [], None, None
    for c in cps:
        if start is None:
            start = prev = c
        elif c == prev + 1:
            prev = c
        else:
            out.append((start, prev))
            start = prev = c
    if start is not None:
        out.append((start, prev))
    return ", ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in out)


def slices():
    syll = range(0xAC00, 0xD7A4)
    common = [c for c in syll if is_common(c)]
    rare = [c for c in syll if not is_common(c)]
    out = [("latin", LATIN), ("cyrillic", CYRILLIC), ("hangul-jamo", JAMO)]
    for i in range(0, len(common), 240):
        out.append((f"hangul-{i // 240:02d}", common[i:i + 240]))
    for i in range(0, len(rare), 900):
        out.append((f"hangul-rare-{i // 900:02d}", rare[i:i + 900]))
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT
    os.makedirs(out_dir, exist_ok=True)
    cmap = TTFont(src).getBestCmap()
    css = []
    total = 0
    for name, cps in slices():
        cps = [c for c in cps if c in cmap]
        if not cps:
            continue
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = False
        opts.flavor = "woff2"
        font = TTFont(src)
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=cps)
        sub.subset(font)
        path = os.path.join(out_dir, f"chemical-{name}.woff2")
        subset.save_font(font, path, opts)
        size = os.path.getsize(path)
        total += size
        print(f"  {name:18s} {len(cps):5d} chars  {size / 1024:7.1f} KB")
        css.append(
            "@font-face {\n"
            '  font-family: "chemical";\n'
            f'  src: url("./chemical-{name}.woff2") format("woff2");\n'
            "  font-display: swap;\n"
            f"  unicode-range: {ranges(cps)};\n"
            "}\n"
        )
    with open(os.path.join(out_dir, "chemical.css"), "w") as fh:
        fh.write("/* chemical — unicode-range subsets; a page loads only the slices it uses */\n")
        fh.write("\n".join(css))
    print(f"  total {total / 1024 / 1024:.2f} MB in {len(css)} slices -> {out_dir}/chemical.css")


if __name__ == "__main__":
    main()
