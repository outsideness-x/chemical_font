"""Kerning measured from the ink.

For every pair the white between the two letters is measured band by band
(each side's depth capped, the way a reader's eye stops at deep counters)
and compared with the white between two straight stems. Pairs that open a
visible hole (AV, To, LT, "T.") are pulled together; pairs that would touch
are pushed apart. Kerning is class based: a letter's four variants and its
accented forms share its class.
"""

import unicodedata

import numpy as np

from .marks import gname
from .metrics import CAP, XH
from .registry import REGISTRY, side_value

STEP = 10.0
YS = np.arange(-260.0, 960.0, STEP)
DMAX = 120.0  # how deep the eye looks into an open side
WINDOW = 4  # rows either side (x STEP units) that count as "near"


def _flatten(contours, dx):
    polys = []
    for c in contours:
        pts = []
        for seg in c:
            if seg[0] == "line":
                pts += [seg[1], seg[2]]
            else:
                p0, p1, p2, p3 = (np.asarray(p) for p in seg[1:])
                t = np.linspace(0.0, 1.0, 9)[:, None]
                m = 1 - t
                pts += list(m**3 * p0 + 3 * m**2 * t * p1 + 3 * m * t**2 * p2 + t**3 * p3)
        polys.append(np.asarray(pts, float) + [dx, 0.0])
    return polys


def profile(contours, dx):
    """Leftmost and rightmost ink x at each YS row (nan where there is none)."""
    left = np.full(len(YS), np.nan)
    right = np.full(len(YS), np.nan)
    for poly in _flatten(contours, dx):
        a, b = poly, np.roll(poly, -1, axis=0)
        y0, y1 = np.minimum(a[:, 1], b[:, 1]), np.maximum(a[:, 1], b[:, 1])
        for i, y in enumerate(YS):
            m = (y0 <= y) & (y < y1)
            if not np.any(m):
                continue
            aa, bb = a[m], b[m]
            x = aa[:, 0] + (y - aa[:, 1]) * (bb[:, 0] - aa[:, 0]) / (bb[:, 1] - aa[:, 1])
            left[i] = np.nanmin([left[i], x.min()])
            right[i] = np.nanmax([right[i], x.max()])
    return left, right


def _near(arr, fn):
    out = np.full_like(arr, np.nan)
    for i in range(len(arr)):
        win = arr[max(0, i - WINDOW): i + WINDOW + 1]
        if np.any(~np.isnan(win)):
            out[i] = fn(win[~np.isnan(win)])
    return out


class Shape:
    def __init__(self, name, contours, dx, adv):
        self.name = name
        self.adv = adv
        self.left, self.right = profile(contours, dx)
        self.left_near = _near(self.left, np.min)
        self.right_near = _near(self.right, np.max)
        ink = ~np.isnan(self.left)
        self.ymin = YS[ink].min() if ink.any() else 0.0
        self.ymax = YS[ink].max() if ink.any() else 0.0
        gd = REGISTRY[name]
        self.lsb = side_value(gd.left)
        self.rsb = side_value(gd.right)


SOFT = 30.0  # soft-min temperature: how strongly the narrowest place dominates


def _gaps(a, b, zone):
    """Capped white between a (left) and b (right), row by row, over zone."""
    rows = (YS >= zone[0]) & (YS <= zone[1])
    da = a.adv - a.right_near[rows]
    db = b.left_near[rows]
    da = np.where(np.isnan(da), a.rsb + DMAX, np.minimum(da, a.rsb + DMAX))
    db = np.where(np.isnan(db), b.lsb + DMAX, np.minimum(db, b.lsb + DMAX))
    return da + db


def _perceived(g):
    """Soft minimum: the eye reads a gap mostly by its narrowest place."""
    if len(g) == 0:
        return np.inf
    m = g.min()
    return float(m - SOFT * np.log(np.mean(np.exp(-(g - m) / SOFT))))


def _closest(a, b):
    both = ~np.isnan(a.right_near) & ~np.isnan(b.left)
    if not both.any():
        return np.inf
    return float(np.min(a.adv - a.right_near[both] + b.left[both]))


def _zone(a, b):
    return max(a.ymin, b.ymin, 0.0), min(a.ymax, b.ymax, CAP)


def natural_zone(shape):
    gd = REGISTRY[shape.name]
    ch = chr(gd.unicodes[0]) if gd.unicodes else ""
    if ch.isalpha() and ch.islower():
        return 0.0, float(XH)
    if ch.isalpha() or ch.isdigit():
        return 0.0, float(CAP)
    return max(shape.ymin, 0.0), min(shape.ymax, CAP)


class Wall:
    """A flat vertical side: what a letter's own spacing was judged against."""

    def __init__(self, side):
        self.adv = side
        self.rsb = self.lsb = side
        self.right_near = np.full(len(YS), 0.0)
        self.left_near = np.full(len(YS), side)


def side_whites(shape):
    zone = natural_zone(shape)
    wall = Wall(0.0)
    right = _perceived(_gaps(shape, wall, zone))
    left = _perceived(_gaps(wall, shape, zone))
    return right, left


def kern_value(a, b, sides):
    zone = _zone(a, b)
    if zone[1] - zone[0] < 50:
        return 0
    natural = sides[a.name][0] + sides[b.name][1]
    k = (natural - _perceived(_gaps(a, b, zone))) * 0.7
    k = max(k, 30 - _closest(a, b))  # never let ink come closer than this
    k = int(round(max(-150.0, min(50.0, k)) / 5.0) * 5)
    return k if abs(k) >= 15 else 0


KERN_PUNCT = ["period", "comma", "colon", "semicolon", "exclam", "question", "quotesingle", "quotedbl",
              "quoteleft", "quoteright", "quotedblleft", "quotedblright", "quotesinglbase", "quotedblbase",
              "guillemetleft", "guillemetright", "guilsinglleft", "guilsinglright", "parenleft", "parenright",
              "bracketleft", "bracketright", "braceleft", "braceright", "hyphen", "endash", "emdash", "slash",
              "ellipsis", "asterisk"]


def kerning_set():
    names = []
    for c in list(range(0x41, 0x5B)) + list(range(0x61, 0x7B)) + list(range(0x0410, 0x0450)) + [
            0x0404, 0x0454, 0x0490, 0x0491, 0x0406, 0x0456]:
        n = gname(c)
        if n in REGISTRY:
            names.append(n)
    names += ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    names += [p for p in KERN_PUNCT if p in REGISTRY]
    return names


def members(present):
    """Kerning class members for each base: variants plus accented forms."""
    out = {}
    base_set = set(kerning_set())
    for n in base_set:
        out[n] = [g for g in [n] + [f"{n}.alt{v}" for v in (1, 2, 3)] if g in present]
    for name, gd in REGISTRY.items():
        if name in base_set or not gd.unicodes:
            continue
        ch = chr(gd.unicodes[0])
        d = unicodedata.normalize("NFD", ch)
        if len(d) > 1 and unicodedata.category(d[0]).startswith("L"):
            bn = gname(ord(d[0]))
            if bn in out:
                out[bn] += [g for g in [name] + [f"{name}.alt{v}" for v in (1, 2, 3)] if g in present]
    return out


def compute(placed, present):
    shapes = {}
    for n in kerning_set():
        if n in placed and placed[n][0]:
            contours, dx, adv = placed[n]
            shapes[n] = Shape(n, contours, dx, adv)
    sides = {n: side_whites(sh) for n, sh in shapes.items()}
    pairs = {}
    for a in shapes.values():
        for b in shapes.values():
            k = kern_value(a, b, sides)
            if k:
                pairs[(a.name, b.name)] = k
    return pairs


def fea(pairs, present):
    if not pairs:
        return ""
    mem = members(present)
    used = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    lines = []
    cname = {}
    for n in used:
        cname[n] = "@k_" + n.replace(".", "_")
        lines.append(f"{cname[n]} = [{' '.join(mem.get(n, [n]))}];")
    lines.append("feature kern {")
    for (a, b), k in sorted(pairs.items()):
        lines.append(f"    pos {cname[a]} {cname[b]} {k};")
    lines.append("} kern;")
    return "\n".join(lines)
