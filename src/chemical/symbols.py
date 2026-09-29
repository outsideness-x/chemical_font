"""Spaces, punctuation and symbols."""

from .metrics import B, CT, XT
from .registry import glyph
from .skel import L, Path, dot, strokes


@glyph("space", 0x20, variants=1, advance=250)
def space():
    return []


@glyph("period", 0x2E, "punct", "punct", variants=1)
def period():
    return strokes(dot(0, B + 6, 6))


@glyph("comma", 0x2C, "punct", "punct", variants=1)
def comma():
    return strokes(Path(14, B + 20).c((20, 0), (8, -60), (-22, -110)))


@glyph("exclam", 0x21, "punct", "punct", variants=1)
def exclam():
    return strokes(L((0, CT), (6, 200)), dot(4, B + 6, 6))


@glyph("question", 0x3F, "punct", "punct", variants=1)
def question():
    return strokes(
        Path(0, 560).c((10, 640), (70, CT + 10), (150, CT + 10)).c((240, CT + 10), (290, 610), (290, 540))
        .c((290, 450), (220, 410), (170, 380)).c((140, 360), (135, 320), (138, 220)),
        dot(138, B + 6, 6),
    )


@glyph("hyphen", 0x2D, "punct", "punct", variants=1)
def hyphen():
    return strokes(L((0, 300), (200, 312)))


@glyph("colon", 0x3A, "punct", "punct", variants=1)
def colon():
    return strokes(dot(0, XT - 20, 6), dot(0, B + 6, 6))
