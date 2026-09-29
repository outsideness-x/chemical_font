"""Skeletons: the centre lines a pen follows.

A glyph is drawn as a list of strokes. Each stroke is a dense polyline in font
units (y up). The helpers below build those polylines from lines, cubic
curves, smooth splines through points and elliptical arcs.
"""

import numpy as np

STEP = 4.0  # sampling step along a skeleton, font units


def _as(p):
    return np.asarray(p, float)


def resample(pts, step=STEP):
    """Densify a polyline so consecutive points are at most `step` apart."""
    pts = _as(pts)
    out = [pts[:1]]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        t = np.linspace(0.0, 1.0, n + 1)[1:, None]
        out.append(a + (b - a) * t)
    return np.vstack(out)


def cubic(p0, p1, p2, p3):
    p0, p1, p2, p3 = map(_as, (p0, p1, p2, p3))
    approx = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2)
    n = max(2, int(np.ceil(approx / STEP * 1.25)))
    t = np.linspace(0.0, 1.0, n + 1)[:, None]
    mt = 1 - t
    return mt**3 * p0 + 3 * mt**2 * t * p1 + 3 * mt * t**2 * p2 + t**3 * p3


def spline(points, closed=False, alpha=0.5):
    """Centripetal Catmull-Rom spline through `points` (no cusps, no loops)."""
    P = _as(points)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-6) ** alpha
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-6) ** alpha
        t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-6) ** alpha
        n = max(2, int(np.ceil(np.linalg.norm(p2 - p1) / STEP * 1.25)))
        t = np.linspace(t1, t2, n + 1)[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        c = (t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2
        out.append(c if not out else c[1:])
    return np.vstack(out)


def arc(cx, cy, rx, ry, a0, a1, rot=0.0):
    """Elliptical arc from angle a0 to a1 (degrees, counter-clockwise positive)."""
    span = abs(a1 - a0) / 360.0 * 2 * np.pi * max(rx, ry)
    n = max(3, int(np.ceil(span / STEP * 1.25)))
    a = np.radians(np.linspace(a0, a1, n + 1))
    x, y = rx * np.cos(a), ry * np.sin(a)
    r = np.radians(rot)
    c, s = np.cos(r), np.sin(r)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], axis=1)


class Path:
    """Chainable skeleton builder: Path(x, y).l(p).c(c1, c2, p).s(p, q)..."""

    def __init__(self, x, y):
        self.parts = [_as([[x, y]])]

    @property
    def cur(self):
        return self.parts[-1][-1]

    def _add(self, seg):
        self.parts.append(seg[1:])
        return self

    def l(self, *pts):
        for p in pts:
            self._add(resample([self.cur, _as(p)]))
        return self

    def c(self, c1, c2, p):
        return self._add(cubic(self.cur, c1, c2, p))

    def q(self, c, p):
        p0, c, p = self.cur, _as(c), _as(p)
        return self._add(cubic(p0, p0 + 2 / 3 * (c - p0), p + 2 / 3 * (c - p), p))

    def s(self, *pts):
        return self._add(spline([self.cur, *pts]))

    def arc(self, cx, cy, rx, ry, a0, a1, rot=0.0):
        seg = arc(cx, cy, rx, ry, a0, a1, rot)
        return self._add(np.vstack([self.cur, seg]))

    @property
    def pts(self):
        return np.vstack(self.parts)


class Stroke:
    """One pen movement: a dense centre line plus how hard the pen presses."""

    __slots__ = ("pts", "weight", "hand")

    def __init__(self, pts, weight=1.0, hand=1.0):
        self.pts = _as(pts)
        self.weight = weight  # width multiplier
        self.hand = hand  # multiplier for this stroke's wobble

    def transformed(self, fn):
        return Stroke(fn(self.pts), self.weight, self.hand)


def strokes(*items):
    """Normalise a mix of Path / arrays / Stroke / nested lists to [Stroke]."""
    out = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, Stroke):
            out.append(it)
        elif isinstance(it, Path):
            out.append(Stroke(it.pts))
        elif isinstance(it, (list, tuple)):
            out.extend(strokes(*it))
        else:
            out.append(Stroke(it))
    return out


# -- small vocabulary ---------------------------------------------------------


def L(*pts):
    """A straight stroke through the given points (corners stay sharp)."""
    return Path(*pts[0]).l(*pts[1:])


def S(*pts, closed=False):
    """A smooth stroke through the given points."""
    return spline(pts, closed=closed)


def C(p0, c1, c2, p3):
    return cubic(p0, c1, c2, p3)


def O(cx, cy, rx, ry, start=90.0, sweep=360.0, rot=0.0):
    """An oval drawn from `start`, counter-clockwise by `sweep` degrees.

    A sweep a little over 360 closes the loop the way a hand does: with a
    small overlap instead of a perfect join.
    """
    return arc(cx, cy, rx, ry, start, start + sweep, rot)


def dot(x, y, r=7.0):
    """A marker dot: a tiny loop the nib fills into a round blob."""
    return arc(x, y, r, r * 0.9, 200.0, 200.0 + 380.0)


def translate(dx, dy):
    return lambda p: p + np.array([dx, dy])


def scale_about(sx, sy, ox=0.0, oy=0.0):
    return lambda p: (p - [ox, oy]) * [sx, sy] + [ox, oy]


def loop(x0, y0, x1, y1, k=0.6, start=0, overlap=0.14, tilt=0.0):
    """A closed bowl drawn the way a hand draws an 'o'.

    Four quarter curves (top -> left -> bottom -> right -> top); `k` is the
    handle length (0.552 = ellipse, higher = squarer). The stroke starts at
    quarter `start` and runs past its beginning by `overlap` of a quarter.
    """
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    top, left, bot, right = (cx, y1), (x0, cy), (cx, y0), (x1, cy)
    quarters = [
        (top, (cx - k * rx, y1), (x0, cy + k * ry), left),
        (left, (x0, cy - k * ry), (cx - k * rx, y0), bot),
        (bot, (cx + k * rx, y0), (x1, cy - k * ry), right),
        (right, (x1, cy + k * ry), (cx + k * rx, y1), top),
    ]
    quarters = quarters[start:] + quarters[:start]
    parts = [cubic(*q) for q in quarters]
    if overlap > 0:
        q = cubic(*quarters[0])
        parts.append(q[: max(2, int(len(q) * overlap))])
    pts = np.vstack([parts[0]] + [p[1:] for p in parts[1:]])
    if tilt:
        r = np.radians(tilt)
        c, s = np.cos(r), np.sin(r)
        pts = (pts - [cx, cy]) @ np.array([[c, s], [-s, c]]) + [cx, cy]
    return pts
