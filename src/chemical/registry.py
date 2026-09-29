"""Glyph registry: every drawable glyph declares itself here."""

from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

# sidebearings (ink edge to advance edge), by the shape of the letter's side
SIDES = {
    # lowercase
    "stem": 34,  # n l h m u (straight vertical sides)
    "round": 25,  # o c e d b p q (bowls)
    "open": 16,  # right side of c e r t f (open, light)
    "arm": 8,  # right side of r, left of j: overhang
    "diag": 6,  # v w x y (diagonal sides)
    "tail": 22,
    # capitals
    "Stem": 42,
    "Round": 30,
    "Open": 20,
    "Diag": 8,
    # figures & marks
    "fig": 30,
    "punct": 32,
    "tight": 14,
    "wide": 60,
    "zero": 0,
}


@dataclass
class GlyphDef:
    name: str
    unicodes: Tuple[int, ...]
    draw: Callable
    left: object = "stem"
    right: object = "stem"
    variants: int = 4
    advance: Optional[float] = None  # fixed advance (tabular / Hangul)
    nib: str = "marker"
    hand: dict = field(default_factory=dict)  # Hand overrides
    center: bool = False  # centre ink in a fixed advance


REGISTRY = {}


def glyph(name, uni=None, left="stem", right="stem", variants=4, advance=None,
          nib="marker", hand=None, center=False):
    if uni is None:
        unis = ()
    elif isinstance(uni, (tuple, list)):
        unis = tuple(uni)
    else:
        unis = (uni,)

    def deco(fn):
        REGISTRY[name] = GlyphDef(name, unis, fn, left, right, variants, advance, nib,
                                  dict(hand or {}), center)
        return fn

    return deco


def side_value(v):
    return SIDES[v] if isinstance(v, str) else float(v)
