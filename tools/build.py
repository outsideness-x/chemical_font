#!/usr/bin/env python3
"""Build chemical: ink every glyph, then write .otf, .ttf and .woff2.

    .venv/bin/python tools/build.py            # everything
    .venv/bin/python tools/build.py --no-hangul  # fast loop for Latin/Cyrillic work
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from chemical import builder, features  # noqa: E402
from chemical.registry import REGISTRY  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-hangul", action="store_true", help="skip Hangul syllables")
    ap.add_argument("--hangul-sample", default=None, help="only the syllables in this text")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"))
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--formats", default="ttf,otf,woff2")
    args = ap.parse_args()

    t0 = time.time()

    sample = set(ord(c) for c in args.hangul_sample) if args.hangul_sample else None

    def keep(gd):
        syllables = [u for u in gd.unicodes if 0xAC00 <= u <= 0xD7A3]
        if not syllables:
            return True
        if args.no_hangul:
            return False
        return sample is None or syllables[0] in sample

    jobs = builder.plan(keep)
    results = builder.render(jobs, args.jobs)
    placed = builder.layout(results)
    order = [j.out for j in jobs]
    cmap = {}
    for j in jobs:
        if j.variant == 0 and j.out == j.src:
            for u in REGISTRY[j.src].unicodes:
                cmap[u] = j.out
    fea = features.feature_code(set(order))
    formats = args.formats.split(",")
    base = os.path.join(args.out, "chemical-Regular")
    if "ttf" in formats or "woff2" in formats:
        builder.assemble(placed, order, cmap, fea, base + ".ttf", "ttf")
        print("  wrote", base + ".ttf", f"{os.path.getsize(base + '.ttf') / 1024:.0f} KB")
    if "otf" in formats:
        builder.assemble(placed, order, cmap, fea, base + ".otf", "otf")
        print("  wrote", base + ".otf", f"{os.path.getsize(base + '.otf') / 1024:.0f} KB")
    if "woff2" in formats:
        builder.woff2(base + ".ttf", base + ".woff2")
        print("  wrote", base + ".woff2", f"{os.path.getsize(base + '.woff2') / 1024:.0f} KB")
    print(f"done in {time.time() - t0:.1f}s, {len(order) + 1} glyphs")


if __name__ == "__main__":
    main()
