#!/usr/bin/env python3
"""Sanity checks for the built fonts.

    .venv/bin/python tools/check.py

Runs the OpenType Sanitizer (what Chrome and Firefox use to accept a web
font), checks coverage of Latin, Cyrillic and every Hangul syllable, and
looks for mapped characters that came out empty.
"""

import os
import sys

import ots
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")

REQUIRED = {
    "Basic Latin": [c for c in range(0x21, 0x7F)],
    "Russian": [c for c in range(0x410, 0x450)] + [0x401, 0x451],
    "Ukrainian/Belarusian": [0x404, 0x454, 0x406, 0x456, 0x407, 0x457, 0x490, 0x491, 0x40E, 0x45E],
    "Hangul syllables": list(range(0xAC00, 0xD7A4)),
    "Hangul compatibility jamo": list(range(0x3131, 0x3164)),
}
SPACES = {0x20, 0xA0, 0x2009, 0x3000}


def main():
    ok = True
    for fn in ("chemical-Regular.otf", "chemical-Regular.ttf", "chemical-Regular.woff2"):
        path = os.path.join(BUILD, fn)
        if not os.path.exists(path):
            print(f"missing {fn}")
            ok = False
            continue
        res = ots.sanitize(path, os.devnull, capture_output=True)
        status = "ok" if res.returncode == 0 else "FAILED"
        print(f"ots {fn}: {status}")
        if res.returncode:
            ok = False
            print(res.stderr.decode()[:2000])

    font = TTFont(os.path.join(BUILD, "chemical-Regular.ttf"))
    cmap = font.getBestCmap()
    glyf = font["glyf"]
    for label, cps in REQUIRED.items():
        missing = [c for c in cps if c not in cmap]
        print(f"{label}: {len(cps) - len(missing)}/{len(cps)}")
        if missing:
            ok = False
            print("  missing:", " ".join(chr(c) for c in missing[:40]))
    empty = [c for c, g in cmap.items() if c not in SPACES and glyf[g].numberOfContours == 0]
    if empty:
        ok = False
        print("empty glyphs:", " ".join(f"U+{c:04X}" for c in empty[:40]))
    feats = sorted({fr.FeatureTag for fr in font["GSUB"].table.FeatureList.FeatureRecord})
    print("GSUB features:", " ".join(feats))
    if "GPOS" in font:
        print("GPOS features:", " ".join(sorted({fr.FeatureTag for fr in font["GPOS"].table.FeatureList.FeatureRecord})))
    print("glyphs:", len(font.getGlyphOrder()))
    print("all good" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
