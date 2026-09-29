"""The pen: turns skeleton strokes into ink.

A felt-tip nib is modelled as a slightly oval shape held at a fixed angle, so
strokes swell and thin a little with direction, the way a worn marker does.
Every stroke is outlined on its own (with round ends), then all strokes of a
glyph are merged into clean, non-overlapping contours.
"""

from dataclasses import dataclass

import numpy as np
import pathops
from fontTools.pens.recordingPen import RecordingPen

from .noise import Warp, Wobble, rng


class Nib:
    """A felt tip: a superellipse (2 = oval, higher = blunter), held at an angle."""

    def __init__(self, width, ratio=0.86, angle=32.0, squareness=2.0, samples=128):
        a, b = width / 2.0, width / 2.0 * ratio
        t = np.linspace(0.0, 2 * np.pi, samples, endpoint=False)
        e = 2.0 / squareness
        x = a * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** e
        y = b * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** e
        th = np.radians(angle)
        rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        self.edge = np.stack([x, y], axis=1) @ rot.T
        self.width = width

    def support(self, dirs):
        """Points on the nib's edge whose outward normals are `dirs`."""
        return self.edge[np.argmax(dirs @ self.edge.T, axis=1)]


@dataclass(frozen=True)
class Hand:
    """How unsteady the hand is. All distances in font units."""

    warp: float = 10.0  # the whole letter bends a little
    warp_len: float = 520.0
    wobble: float = 2.6  # lines are never quite straight
    pressure: float = 0.13  # the nib swells and thins along a stroke
    stroke_var: float = 0.11  # every stroke is pressed a little differently
    pool: float = 0.10  # ink pools where the hand slows down, in tight turns
    blob: float = 0.09  # and where the pen lands (more on some strokes)
    taper: float = 0.14  # and runs thin where it lifts
    overshoot: float = 20.0  # corners are drawn past the turn
    through: float = 0.55  # chance that a stroke ending on another runs through it
    through_len: tuple = (16.0, 34.0)
    rough: float = 2.2  # ragged edge where ink bleeds into paper
    rough_fine: float = 0.55  # share of the finest ripple in that edge
    rise: float = 0.03  # horizontals climb to the right, as in handwriting
    bow: float = 6.0  # long straight strokes bow a little
    flick: float = 0.0  # chance of an exit flick on the last down-stroke
    flick_dir: float = 1.0  # +1 flicks right (Latin, Cyrillic), -1 left (Hangul)
    entry: float = 0.0  # chance of a small lead-in on the first down-stroke
    rotate: float = 0.9  # degrees of tilt per glyph
    shift: float = 6.0  # baseline bounce
    scale: float = 0.012  # size drift


def _tangents(pts):
    d = np.gradient(pts, axis=0)
    return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)


def _arclength(pts):
    return np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]


def _slowness(pts, s, radius=70.0, window=40.0):
    """0..1 along a stroke: 1 where it turns tighter than `radius`."""
    t = _tangents(pts)
    ang = np.unwrap(np.arctan2(t[:, 1], t[:, 0]))
    ds = np.maximum(np.gradient(s), 1e-6)
    curv = np.abs(np.gradient(ang) / ds)
    slow = np.clip(curv * radius, 0.0, 1.0)
    k = max(1, int(window / max(np.median(ds), 1e-3)))
    kernel = np.ones(2 * k + 1) / (2 * k + 1)
    return np.convolve(np.pad(slow, k, mode="edge"), kernel, mode="valid")


def _tucks(placed, width):
    """Which stroke ends land inside the body of another stroke (T-joins).

    There the pen eases off, so the end tucks into the other stroke instead
    of bulging out of its side. Ends that meet other ends (corners) are left
    alone.
    """
    out = []
    reach = 0.55 * width
    for i, a in enumerate(placed):
        flags = []
        for end in (a[0], a[-1]):
            hit = None
            for j, b in enumerate(placed):
                if i == j or len(b) < 2:
                    continue
                d = np.linalg.norm(b - end, axis=1)
                k = int(np.argmin(d))
                if d[k] > reach:
                    continue
                s = _arclength(b)
                if min(s[k], s[-1] - s[k]) > 0.6 * width:
                    other = b[min(k + 2, len(b) - 1)] - b[max(k - 2, 0)]
                    mine = a[min(3, len(a) - 1)] - a[0] if end is a[0] else a[-1] - a[max(len(a) - 4, 0)]
                    cos = abs(np.dot(other, mine)) / max(np.linalg.norm(other) * np.linalg.norm(mine), 1e-9)
                    hit = "steep" if cos < 0.57 else "shallow"
                    break
            flags.append(hit)
        out.append(tuple(flags))
    return out


def _cubic(p0, p1, p2, p3, n=12):
    t = np.linspace(0.0, 1.0, n)[:, None]
    m = 1 - t
    return m**3 * p0 + 3 * m**2 * t * p1 + 3 * m * t**2 * p2 + t**3 * p3


def _downward(d, lean=0.6):
    return d[1] < 0 and abs(d[0]) < lean * abs(d[1])


def _with_flick(pts, side, size):
    """End a down-stroke the way a writing hand does: with a small flick."""
    end = pts[-1]
    keep = pts[pts[:, 1] > end[1] + 0.75 * size]
    if len(keep) < 2:
        return pts
    p0 = keep[-1]
    x = p0[0]
    curve = _cubic(p0, p0 + [0.0, -0.5 * size], np.array([x + side * 0.2 * size, end[1] - 0.12 * size]),
                   np.array([x + side * 1.05 * size, end[1] + 0.3 * size]), 14)
    return np.vstack([keep, curve[1:]])


def _with_lead_in(pts, size):
    """Start a down-stroke with a small hook from the left."""
    p0 = pts[0]
    hook = _cubic(p0 + [-size, -0.2 * size], p0 + [-0.75 * size, 0.3 * size], p0 + [-0.05 * size, 0.35 * size], p0, 12)
    return np.vstack([hook[:-1], pts])


def _bowed(pts, r, amount):
    """Long straight strokes are never ruler-straight: bow them a little."""
    s = _arclength(pts)
    total = s[-1]
    if total < 140 or np.linalg.norm(pts[-1] - pts[0]) < 0.985 * total:
        return pts
    d = (pts[-1] - pts[0]) / np.linalg.norm(pts[-1] - pts[0])
    n = np.array([-d[1], d[0]])
    bend = r.uniform(-1.0, 1.0) * amount * min(1.0, total / 450.0)
    return pts + n * (bend * np.sin(np.pi * s / total))[:, None]


def _extend(pts, at_start, length, step=4.0):
    """Carry a stroke on past its end, straight along its last direction."""
    if length <= 0 or len(pts) < 2:
        return pts
    if at_start:
        d = pts[0] - pts[min(3, len(pts) - 1)]
    else:
        d = pts[-1] - pts[max(len(pts) - 4, 0)]
    n = np.linalg.norm(d)
    if n < 1e-9:
        return pts
    d /= n
    t = np.arange(step, length + 1e-6, step)
    if len(t) == 0 or t[-1] < length:
        t = np.r_[t, length]
    if at_start:
        return np.vstack([pts[0] + d * t[::-1, None], pts])
    return np.vstack([pts, pts[-1] + d * t[:, None]])


def roughen(contours, r, amp, fine=0.55):
    """Ragged ink edge: each outline pushed in and out along its normal."""
    if not amp:
        return contours
    out = []
    for c in contours:
        c = np.vstack([c, c[:1]])
        seg = np.linalg.norm(np.diff(c, axis=0), axis=1)
        s = np.r_[0.0, np.cumsum(seg)]
        per = s[-1]
        if per < 60:
            out.append(c[:-1])
            continue
        n = max(12, int(per / 3.5))
        u = np.linspace(0.0, per, n, endpoint=False)
        pts = np.stack([np.interp(u, s, c[:, 0]), np.interp(u, s, c[:, 1])], axis=1)
        t = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        nrm = np.stack([t[:, 1], -t[:, 0]], axis=1)
        d = np.zeros(n)
        for wl, wt in ((58.0, fine), (120.0, 0.8), (260.0, 0.6)):
            k = max(1, int(round(per / wl)))
            d += wt * np.sin(2 * np.pi * k * u / per + r.uniform(0, 2 * np.pi))
        out.append(pts + nrm * (amp * d / 1.2)[:, None])
    return out


def _dedupe(pts, eps=0.5):
    keep = np.r_[True, np.linalg.norm(np.diff(pts, axis=0), axis=1) > eps]
    return pts[keep]


def split_corners(pts, widths, max_turn=50.0):
    """Split a stroke where it turns sharply, so each corner gets a round end."""
    if len(pts) < 3:
        return [(pts, widths)]
    d = np.diff(pts, axis=0)
    ang = np.arctan2(d[:, 1], d[:, 0])
    turn = np.abs((np.diff(ang) + np.pi) % (2 * np.pi) - np.pi)
    cuts = list(np.where(turn > np.radians(max_turn))[0] + 1)
    pieces, start = [], 0
    for c in cuts + [len(pts) - 1]:
        if c - start >= 1:
            pieces.append((pts[start : c + 1], widths[start : c + 1]))
        start = c
    return pieces


_HULL_DIRS = 56


def _hull_dirs():
    a = np.linspace(0.0, 2 * np.pi, _HULL_DIRS, endpoint=False)
    return np.stack([np.cos(a), np.sin(a)], axis=1)


def stamps(pts, widths, nib, every=2):
    """Exact ink of a stroke: the convex hull of each pair of nib stamps.

    Used where a stroke turns tighter than the nib is wide; there an offset
    outline would fold over itself.
    """
    idx = np.r_[np.arange(0, len(pts) - 1, every), len(pts) - 1]
    P, Wd = pts[idx], widths[idx]
    if len(P) == 1:
        P, Wd = np.vstack([P, P + [0.5, 0.0]]), np.r_[Wd, Wd]
    U = _hull_dirs()
    E = nib.support(U)
    h = np.sum(E * U, axis=1)
    reach = P @ U.T + Wd[:, None] * h[None, :]
    pick_b = reach[1:] > reach[:-1]
    a = P[:-1, None, :] + Wd[:-1, None, None] * E[None, :, :]
    b = P[1:, None, :] + Wd[1:, None, None] * E[None, :, :]
    return list(np.where(pick_b[..., None], b, a))


def _foldless(pts, widths, nib, margin=1.7):
    """True when no part of the stroke turns tighter than the nib's reach."""
    if len(pts) < 4:
        return False
    t = _tangents(pts)
    ang = np.unwrap(np.arctan2(t[:, 1], t[:, 0]))
    ds = np.maximum(np.linalg.norm(np.gradient(pts, axis=0), axis=1), 1e-6)
    curv = np.abs(np.gradient(ang)) / ds
    reach = widths * nib.width / 2.0 * margin
    return bool(np.all(curv * reach < 1.0))


def outline(pts, widths, nib, cap_steps=22):
    """Closed counter-clockwise polygon around one stroke piece."""
    if len(pts) == 1:
        pts = np.vstack([pts, pts + [0.5, 0.0]])
        widths = np.r_[widths, widths]
    t = _tangents(pts)
    n = np.stack([-t[:, 1], t[:, 0]], axis=1)
    right = pts + widths[:, None] * nib.support(-n)
    left = pts + widths[:, None] * nib.support(n)
    phi = np.linspace(0.0, np.pi, cap_steps)[1:-1, None]
    end = pts[-1] + widths[-1] * nib.support(-n[-1] * np.cos(phi) + t[-1] * np.sin(phi))
    start = pts[0] + widths[0] * nib.support(n[0] * np.cos(phi) - t[0] * np.sin(phi))
    return np.vstack([right, end, left[::-1], start])


def _poly_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def union(polys, min_island=90.0, min_hole=420.0):
    """Merge overlapping polygons; drop specks and ink-filled pinholes."""
    path = pathops.Path()
    for poly in polys:
        path.moveTo(*poly[0])
        for p in poly[1:]:
            path.lineTo(*p)
        path.close()
    path.fillType = pathops.FillType.WINDING
    merged = pathops.simplify(path, clockwise=False)
    rec = RecordingPen()
    merged.draw(rec)
    contours, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op in ("closePath", "endPath"):
            if len(cur) >= 3:
                contours.append(np.asarray(cur, float))
            cur = []
        else:  # simplify of polygons only yields lines
            cur.extend(args)
    out = []
    for c in contours:
        a = _poly_area(c)
        if (a > 0 and a < min_island) or (a < 0 and -a < min_hole):
            continue
        out.append(c)
    return out


def ink(strokes, nib, hand, seed, pose=None):
    """Draw strokes with a hand and a nib; return merged contour polygons.

    `pose` = (tilt in degrees, lift in units, size factor) places the whole
    letter: letters written by hand never sit exactly on the line.
    """
    r = rng(seed)
    allpts = np.vstack([s.pts for s in strokes])
    lo, hi = allpts.min(axis=0), allpts.max(axis=0)
    center = (lo + hi) / 2.0
    if pose is None:
        pose = (
            float(np.clip(r.normal(0.0, hand.rotate * 0.6), -hand.rotate, hand.rotate)),
            float(r.uniform(-hand.shift, hand.shift)),
            1.0 + float(r.uniform(-hand.scale, hand.scale)),
        )
    tilt, lift, size = pose[:3]
    wide = pose[3] if len(pose) > 3 else 1.0
    ang = np.radians(tilt)
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    foot = np.array([center[0], 0.0])  # letters grow up from the baseline
    warp = Warp(r, hand.warp, hand.warp_len) if hand.warp else None

    placed = []
    for st in strokes:
        pts = (st.pts - foot) * [size * wide, size] + foot
        pts = pts + np.stack([np.zeros(len(pts)), hand.rise * (pts[:, 0] - center[0])], axis=1)
        pts = (pts - center) @ rot.T + center + [0.0, lift]
        if warp is not None:
            pts = warp(pts)
        pts = _dedupe(pts)
        if hand.bow and not st.fill:
            pts = _bowed(pts, r, hand.bow)
        placed.append(pts)

    # the writing hand: a lead-in on the first down-stroke, a flick on the last
    if hand.entry or hand.flick:
        xs = np.vstack(placed)[:, 0]
        xmin, xmax = xs.min(), xs.max()
        ys = np.vstack(placed)[:, 1]
        if hand.entry and r.random() < hand.entry:
            for i, pts in enumerate(placed):
                if len(pts) > 4 and _downward(pts[4] - pts[0], 0.8) and pts[0][0] < xmin + 45 \
                        and pts[0][1] > ys.max() - 60:
                    placed[i] = _with_lead_in(pts, 34.0)
                    break
        if hand.flick and r.random() < hand.flick:
            best = None
            for i, pts in enumerate(placed):
                if len(pts) > 4 and _downward(pts[-1] - pts[-5]) and pts[-1][0] > xmax - 45:
                    if hand.flick_dir > 0 and pts[-1][1] > ys.min() + 40:
                        continue  # Latin flicks only on the baseline
                    if best is None or pts[-1][0] > placed[best][-1][0]:
                        best = i
            if best is not None:
                placed[best] = _with_flick(placed[best], hand.flick_dir, 44.0 if hand.flick_dir > 0 else 36.0)
    joins = _tucks(placed, nib.width)

    polys = []
    for st, pts, (join0, join1) in zip(strokes, placed, joins):
        # a stroke that meets another square-on sometimes runs straight through it
        tuck0, tuck1 = join0 is not None, join1 is not None
        if join0 == "steep" and r.random() < hand.through:
            pts, tuck0 = _extend(pts, True, r.uniform(*hand.through_len)), False
        if join1 == "steep" and r.random() < hand.through:
            pts, tuck1 = _extend(pts, False, r.uniform(*hand.through_len)), False
        s = _arclength(pts)
        total = s[-1] if len(s) else 0.0
        if hand.wobble and st.hand and len(pts) > 2:
            t = _tangents(pts)
            n = np.stack([-t[:, 1], t[:, 0]], axis=1)
            fade = np.minimum(1.0, np.minimum(s, total - s) / 25.0 + 0.35)
            pts = pts + n * (Wobble(r, (420.0, 210.0), (1.0, 0.35))(s) * hand.wobble * st.hand * fade)[:, None]
        # pressure: one or two slow swells along the stroke, never lumps
        w = 1.0 + hand.pressure * Wobble(r, (900.0, 430.0), (1.0, 0.3))(s)
        w *= 1.0 + hand.stroke_var * r.uniform(-1.0, 1.0)
        if hand.pool and len(pts) > 6:
            w *= 1.0 + hand.pool * _slowness(pts, s)
        w *= 1.0 + hand.blob * r.uniform(0.3, 1.6) * (not tuck0) * np.exp(-s / 30.0)
        w *= 1.0 - hand.taper * np.clip(1.0 - (total - s) / 60.0, 0.0, 1.0) ** 1.6
        if tuck0:
            w *= 1.0 - 0.3 * np.exp(-s / 20.0)
        if tuck1:
            w *= 1.0 - 0.3 * np.exp(-(total - s) / 20.0)
        w *= st.weight
        if getattr(st, "fill", False) and len(pts) > 2:
            area = _poly_area(pts)
            polys.append(pts if area > 0 else pts[::-1])
        pieces = split_corners(pts, w)
        for i, (piece, pw) in enumerate(pieces):
            # a quick hand overshoots its corners
            if hand.overshoot and len(pieces) > 1:
                if i > 0 and r.random() < 0.8:
                    n0 = len(piece)
                    piece = _extend(piece, True, r.uniform(0.3, 1.0) * hand.overshoot)
                    pw = np.r_[np.full(len(piece) - n0, pw[0]), pw]
                if i < len(pieces) - 1 and r.random() < 0.8:
                    n0 = len(piece)
                    piece = _extend(piece, False, r.uniform(0.3, 1.0) * hand.overshoot)
                    pw = np.r_[pw, np.full(len(piece) - n0, pw[-1])]
            if _foldless(piece, pw, nib):
                polys.append(outline(piece, pw, nib))
            else:
                polys.extend(stamps(piece, pw, nib))
    return roughen(union(polys), r, hand.rough * nib.width / 84.0, hand.rough_fine)
