"""From inked polygons to clean Bézier outlines.

Corners (where strokes cross) stay sharp; everything else is fitted with as
few cubic curves as the tolerance allows (Schneider's algorithm), then split
at horizontal and vertical extremes like a hand-built outline would be.
"""

import numpy as np


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def _bez(c, u):
    u = np.asarray(u)[:, None]
    m = 1 - u
    return m**3 * c[0] + 3 * m**2 * u * c[1] + 3 * m * u**2 * c[2] + u**3 * c[3]


def _bez1(c, u):
    u = np.asarray(u)[:, None]
    m = 1 - u
    return 3 * (m**2 * (c[1] - c[0]) + 2 * m * u * (c[2] - c[1]) + u**2 * (c[3] - c[2]))


def _bez2(c, u):
    u = np.asarray(u)[:, None]
    return 6 * ((1 - u) * (c[2] - 2 * c[1] + c[0]) + u * (c[3] - 2 * c[2] + c[1]))


def _chord(pts):
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    return d / d[-1] if d[-1] > 0 else np.linspace(0, 1, len(pts))


def _generate(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    m = 1 - u
    b0, b1, b2, b3 = m**3, 3 * m**2 * u, 3 * m * u**2, u**3
    a1 = t1[None, :] * b1[:, None]
    a2 = t2[None, :] * b2[:, None]
    c00, c01, c11 = np.sum(a1 * a1), np.sum(a1 * a2), np.sum(a2 * a2)
    tmp = pts - (p0[None, :] * (b0 + b1)[:, None] + p3[None, :] * (b2 + b3)[:, None])
    x0, x1 = np.sum(a1 * tmp), np.sum(a2 * tmp)
    det = c00 * c11 - c01 * c01
    seg = np.linalg.norm(p3 - p0)
    al = ar = seg / 3.0
    if abs(det) > 1e-12:
        al = (x0 * c11 - x1 * c01) / det
        ar = (c00 * x1 - c01 * x0) / det
    if not (1e-6 * seg < al < 2.5 * seg and 1e-6 * seg < ar < 2.5 * seg):
        al = ar = seg / 3.0
    return np.array([p0, p0 + t1 * al, p3 + t2 * ar, p3])


def _reparam(c, pts, u):
    d = _bez(c, u) - pts
    d1, d2 = _bez1(c, u), _bez2(c, u)
    num = np.sum(d * d1, axis=1)
    den = np.sum(d1 * d1, axis=1) + np.sum(d * d2, axis=1)
    step = np.divide(num, den, out=np.zeros_like(num), where=np.abs(den) > 1e-12)
    return np.clip(u - step, 0.0, 1.0)


def _err(c, pts, u):
    d = np.sum((_bez(c, u) - pts) ** 2, axis=1)
    i = int(np.argmax(d))
    return d[i], i


def fit_run(pts, t1, t2, tol, depth=0):
    """Fit cubic(s) to an open run of points with fixed end tangents.

    t1 points forward from the first point, t2 points backward from the last.
    """
    n = len(pts)
    if n == 2 or depth > 24:
        dist = np.linalg.norm(pts[-1] - pts[0]) / 3.0
        return [np.array([pts[0], pts[0] + t1 * dist, pts[-1] + t2 * dist, pts[-1]])]
    u = _chord(pts)
    c = _generate(pts, u, t1, t2)
    e2, split = _err(c, pts, u)
    if e2 < tol * tol:
        return [c]
    if e2 < (5 * tol) ** 2:
        for _ in range(10):
            u = _reparam(c, pts, u)
            c = _generate(pts, u, t1, t2)
            e2, split = _err(c, pts, u)
            if e2 < tol * tol:
                return [c]
    split = min(max(split, 1), n - 2)
    lo = max(split - 2, 0)
    hi = min(split + 2, n - 1)
    tc = _unit(pts[lo] - pts[hi])
    return fit_run(pts[: split + 1], t1, tc, tol, depth + 1) + fit_run(
        pts[split:], -tc, t2, tol, depth + 1
    )


def _resample_run(pts, step):
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    total = d[-1]
    if total <= 0:
        return pts[[0, -1]]
    n = max(2, int(np.ceil(total / step)) + 1)
    s = np.linspace(0.0, total, n)
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], axis=1)


def _tangent_out(run, reach=7.0):
    """Direction leaving the first point of a run, measured over `reach` units."""
    d = np.cumsum(np.linalg.norm(np.diff(run, axis=0), axis=1))
    k = int(np.searchsorted(d, reach)) + 1
    k = min(max(k, 1), len(run) - 1)
    return _unit(run[k] - run[0])


def corners_of(poly, max_turn=32.0):
    """Indices of sharp vertices in a closed polygon."""
    prev = poly - np.roll(poly, 1, axis=0)
    nxt = np.roll(poly, -1, axis=0) - poly
    a = np.arctan2(prev[:, 1], prev[:, 0])
    b = np.arctan2(nxt[:, 1], nxt[:, 0])
    turn = np.abs((b - a + np.pi) % (2 * np.pi) - np.pi)
    return list(np.where(turn > np.radians(max_turn))[0])


def _split_extrema(c, min_dev=1.5):
    """Split a cubic at its interior horizontal/vertical extremes."""
    d0, d1, d2 = c[1] - c[0], c[2] - c[1], c[3] - c[2]
    A, B, Cc = d0 - 2 * d1 + d2, 2 * (d1 - d0), d0
    ts = []
    for k in (0, 1):
        a, b, cc = A[k], B[k], Cc[k]
        if abs(a) < 1e-9:
            if abs(b) > 1e-9:
                ts.append(-cc / b)
            continue
        disc = b * b - 4 * a * cc
        if disc < 0:
            continue
        r = np.sqrt(disc)
        ts += [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    good = []
    for t in sorted(t for t in ts if 0.04 < t < 0.96):
        p = _bez(c, [t])[0]
        if np.all(np.abs(p - c[0]) > min_dev) or np.all(np.abs(p - c[3]) > min_dev):
            if not good or t - good[-1] > 0.04:
                good.append(t)
    if not good:
        return [c]
    out, rest, t0 = [], c, 0.0
    for t in good:
        tt = (t - t0) / (1 - t0)
        p01 = rest[0] + (rest[1] - rest[0]) * tt
        p12 = rest[1] + (rest[2] - rest[1]) * tt
        p23 = rest[2] + (rest[3] - rest[2]) * tt
        p012 = p01 + (p12 - p01) * tt
        p123 = p12 + (p23 - p12) * tt
        mid = p012 + (p123 - p012) * tt
        out.append(np.array([rest[0], p01, p012, mid]))
        rest = np.array([mid, p123, p23, rest[3]])
        t0 = t
    out.append(rest)
    return out


def _is_line(c, tol=0.6):
    chord = c[3] - c[0]
    L = np.linalg.norm(chord)
    if L < 1e-6:
        return True
    n = np.array([-chord[1], chord[0]]) / L
    for p in (c[1], c[2]):
        if abs(np.dot(p - c[0], n)) > tol:
            return False
        s = np.dot(p - c[0], chord) / (L * L)
        if s < -0.05 or s > 1.05:
            return False
    return True


def fit_contour(poly, tol=1.0, step=3.0):
    """Closed polygon -> list of segments (('line', p0, p1) | ('curve', p0..p3))."""
    poly = np.asarray(poly, float)
    keep = np.r_[True, np.linalg.norm(np.diff(poly, axis=0), axis=1) > 0.4]
    poly = poly[keep]
    if np.linalg.norm(poly[0] - poly[-1]) < 0.4:
        poly = poly[:-1]
    if len(poly) < 3:
        return []
    corners = corners_of(poly)
    if not corners:
        # smooth loop: open it at its lowest and highest points
        lo, hi = int(np.argmin(poly[:, 1])), int(np.argmax(poly[:, 1]))
        cuts, smooth = sorted({lo, hi}), True
    else:
        cuts, smooth = corners, False
    n = len(poly)
    cubics = []
    for i, a in enumerate(cuts):
        b = cuts[(i + 1) % len(cuts)]
        idx = np.arange(a, b + 1) if b > a else np.r_[np.arange(a, n), np.arange(0, b + 1)]
        run = _resample_run(poly[idx], step)
        if len(run) < 2:
            continue
        if smooth:
            t1 = _unit(poly[(a + 2) % n] - poly[(a - 2) % n])
            t2 = -_unit(poly[(b + 2) % n] - poly[(b - 2) % n])
        else:
            t1 = _tangent_out(run)
            t2 = _tangent_out(run[::-1])
        cubics += fit_run(run, t1, t2, tol)
    segs = []
    for c in cubics:
        for part in _split_extrema(c):
            if _is_line(part):
                segs.append(("line", part[0], part[3]))
            else:
                segs.append(("curve", part[0], part[1], part[2], part[3]))
    return segs
