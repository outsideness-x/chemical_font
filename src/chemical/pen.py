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
    def __init__(self, width, ratio=0.86, angle=32.0):
        a = width / 2.0
        th = np.radians(angle)
        rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        self.M = rot @ np.diag([a, a * ratio])
        self.width = width

    def support(self, dirs):
        """Points on the nib's edge whose outward normals are `dirs`."""
        mt = dirs @ self.M
        return (mt @ self.M.T) / np.linalg.norm(mt, axis=1, keepdims=True)


@dataclass(frozen=True)
class Hand:
    """How unsteady the hand is. All distances in font units."""

    warp: float = 7.0  # the whole letter bends a little
    warp_len: float = 560.0
    wobble: float = 1.6  # lines are never quite straight
    pressure: float = 0.045  # the nib presses unevenly
    blob: float = 0.07  # ink pools where the pen lands
    taper: float = 0.05  # and thins where it lifts
    rotate: float = 0.9  # degrees of tilt per glyph
    shift: float = 6.0  # baseline bounce
    scale: float = 0.012  # size drift


def _tangents(pts):
    d = np.gradient(pts, axis=0)
    return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)


def _arclength(pts):
    return np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]


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
    tilt, lift, size = pose
    ang = np.radians(tilt)
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    foot = np.array([center[0], 0.0])  # letters grow up from the baseline
    warp = Warp(r, hand.warp, hand.warp_len) if hand.warp else None

    polys = []
    for st in strokes:
        pts = (st.pts - foot) * size + foot
        pts = (pts - center) @ rot.T + center + [0.0, lift]
        if warp is not None:
            pts = warp(pts)
        pts = _dedupe(pts)
        s = _arclength(pts)
        total = s[-1] if len(s) else 0.0
        if hand.wobble and st.hand and len(pts) > 2:
            t = _tangents(pts)
            n = np.stack([-t[:, 1], t[:, 0]], axis=1)
            fade = np.minimum(1.0, np.minimum(s, total - s) / 25.0 + 0.35)
            pts = pts + n * (Wobble(r, (300.0, 130.0), (1.0, 0.4))(s) * hand.wobble * st.hand * fade)[:, None]
        w = 1.0 + hand.pressure * Wobble(r, (340.0, 150.0), (1.0, 0.5))(s)
        w *= 1.0 + hand.blob * np.exp(-s / 16.0)
        w *= 1.0 - hand.taper * np.exp(-(total - s) / 28.0)
        w *= st.weight
        for piece, pw in split_corners(pts, w):
            polys.append(outline(piece, pw, nib))
    return union(polys)
