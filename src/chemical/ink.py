"""Inking: skeleton -> pen -> fitted outline, with a content-addressed cache."""

import hashlib
import os
import pickle
from dataclasses import replace

import numpy as np

from . import metrics
from .fit import fit_contour
from .noise import rng
from .pen import Hand, Nib, ink
from .registry import REGISTRY

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "ink")
ENGINE_VERSION = "9"  # bump to invalidate every cached outline

NIBS = {
    "marker": dict(width=metrics.PEN, ratio=0.72, angle=32.0, squareness=2.5),
    "thin": dict(width=metrics.THIN, ratio=0.94, angle=32.0, squareness=2.0),
}

HAND = Hand()

# How a letter sits on the line. Each letter gets one of four tilts, lifts and
# sizes per variant, dealt from a shuffled deck, so the variants of a letter
# are guaranteed to differ and neighbours (which cycle through variants) never
# stand the same way.
TILTS = (-0.4, -0.8, -1.2, -1.6)  # degrees: all lean the same way, forward
LIFTS = (-24.0, -8.0, 8.0, 24.0)  # font units
SIZES = (0.95, 0.983, 1.017, 1.05)


def pose_for(name, variant, calm=1.0):
    deck = rng("pose", name)
    tilt_i, lift_i, size_i = (deck.permutation(4) for _ in range(3))
    v = variant % 4
    j = rng("pose", name, variant)
    return (
        calm * (TILTS[tilt_i[v]] + j.uniform(-0.15, 0.15)),
        calm * (LIFTS[lift_i[v]] + j.uniform(-2.5, 2.5)),
        1.0 + calm * (SIZES[size_i[v]] - 1.0 + j.uniform(-0.004, 0.004)),
    )


def variant_name(name, variant):
    return name if variant == 0 else f"{name}.alt{variant}"


def _sample(seg):
    if seg[0] == "line":
        return np.vstack(seg[1:])
    p0, p1, p2, p3 = seg[1:]
    t = np.linspace(0.0, 1.0, 9)[:, None]
    m = 1 - t
    return m**3 * p0 + 3 * m**2 * t * p1 + 3 * m * t**2 * p2 + t**3 * p3


def _key(strokes, nib, hand, seed, tol):
    h = hashlib.blake2b(digest_size=16)
    h.update(ENGINE_VERSION.encode())
    h.update(repr((sorted(nib.items()), hand, seed, tol)).encode())
    for s in strokes:
        h.update(np.round(s.pts, 3).tobytes())
        h.update(repr((s.weight, s.hand)).encode())
    return h.hexdigest()


def draw_glyph(name, variant=0, strokes=None, nib_name=None, seed_name=None, tol=1.25):
    """Return (contours, (xmin, ymin, xmax, ymax)) for one glyph variant.

    Contours are lists of segments: ('line', p0, p1) or ('curve', p0, c1, c2, p3).
    """
    gd = REGISTRY.get(name)
    if strokes is None:
        strokes = gd.draw()
    if not strokes:
        return [], (0.0, 0.0, 0.0, 0.0)
    nib_name = nib_name or (gd.nib if gd else "marker")
    nib_spec = NIBS[nib_name]
    hand = HAND
    calm = 1.0
    if gd and gd.hand:
        extra = dict(gd.hand)
        calm = extra.pop("calm", 1.0)
        hand = replace(hand, **extra)
    seed = (seed_name or name, variant)
    pose = pose_for(name, variant, calm)
    key = _key(strokes, nib_spec, (hand, pose), seed, tol)
    path = os.path.join(CACHE_DIR, key[:2], key + ".pkl")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return pickle.load(fh)
    polys = ink(strokes, Nib(**nib_spec), hand, seed, pose)
    contours = [c for c in (fit_contour(p, tol=tol) for p in polys) if c]
    if contours:
        pts = np.vstack([_sample(seg) for c in contours for seg in c])
        bounds = (*pts.min(axis=0), *pts.max(axis=0))
    else:
        bounds = (0.0, 0.0, 0.0, 0.0)
    result = (contours, tuple(float(b) for b in bounds))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + f".{os.getpid()}.tmp"
    with open(tmp, "wb") as fh:
        pickle.dump(result, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, path)
    return result
