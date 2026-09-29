"""Deterministic, smooth randomness: the hand that holds the pen.

Every random decision is seeded from the glyph name and variant, so a build
is reproducible and a glyph only changes when its own drawing changes.
"""

import hashlib

import numpy as np


def seed_of(*parts) -> int:
    key = "|".join(str(p) for p in parts).encode()
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "little")


def rng(*parts) -> np.random.Generator:
    return np.random.default_rng(seed_of(*parts))


class Wobble:
    """Smooth 1-D noise in [-1, 1]: a few detuned sines with random phases."""

    def __init__(self, r, wavelengths=(420.0, 190.0, 90.0), weights=(1.0, 0.45, 0.2)):
        self.k = np.array([2 * np.pi / (w * r.uniform(0.8, 1.25)) for w in wavelengths])
        self.phase = r.uniform(0, 2 * np.pi, len(wavelengths))
        self.weight = np.asarray(weights, float) / float(np.sum(weights))

    def __call__(self, s):
        s = np.asarray(s, float)
        return np.sum(
            self.weight[:, None] * np.sin(self.k[:, None] * s[None, :] + self.phase[:, None]),
            axis=0,
        )


class Warp:
    """A smooth displacement field over the whole glyph.

    Because it is continuous, strokes that meet keep meeting: the hand bends
    the letter, it does not tear it apart.
    """

    def __init__(self, r, amplitude, wavelength=520.0, terms=3):
        self.terms = []
        for _ in range(terms):
            angle = r.uniform(0, 2 * np.pi)
            k = 2 * np.pi / (wavelength * r.uniform(0.75, 1.3))
            direction = r.normal(size=2)
            direction /= np.linalg.norm(direction)
            self.terms.append(
                (np.array([np.cos(angle), np.sin(angle)]) * k, r.uniform(0, 2 * np.pi), direction)
            )
        self.amplitude = amplitude / np.sqrt(terms)

    def __call__(self, pts):
        pts = np.asarray(pts, float)
        d = np.zeros_like(pts)
        for kv, phase, direction in self.terms:
            d += np.sin(pts @ kv + phase)[:, None] * direction[None, :]
        return pts + self.amplitude * d
