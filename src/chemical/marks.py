"""Accents, and letters built from a base plus accents.

Accented letters are drawn, not assembled from components: the base skeleton
and the accent skeleton are inked together by the same hand, so the accent
leans and bounces with its letter.
"""

import unicodedata

import numpy as np
from fontTools import agl

from .metrics import AT, B, CAP, CT, OS, XH, XT
from .registry import REGISTRY, glyph
from .skel import L, Path, S, dot, light, loop, moved, strokes


def gname(cp):
    name = agl.UV2AGL.get(cp)
    return name if name else f"uni{cp:04X}"


# accents drawn around (0, 0): the bottom centre of the accent


def acute():
    return strokes(L((-24, 0), (36, 96)))


def grave():
    return strokes(L((-36, 96), (24, 0)))


def circumflex():
    return strokes(L((-70, 0), (0, 80), (70, 0)))


def caron():
    return strokes(L((-70, 80), (0, 0), (70, 80)))


def dieresis():
    return strokes(dot(-62, 34, 6), dot(62, 34, 6))


def tilde():
    return strokes(S((-86, 14), (-44, 66), (28, 24), (86, 74)))


def macron():
    return strokes(L((-86, 34), (86, 40)))


def breve():
    return strokes(Path(-76, 86).c((-62, 6), (62, 6), (76, 86)))


def ring():
    return light(loop(-60, -6, 60, 112, overlap=0.25), 0.7)


def dotaccent():
    return strokes(dot(0, 36, 7))


def hungarumlaut():
    return strokes(L((-70, 0), (-22, 96)), L((30, 0), (78, 96)))


# accents that hang below the baseline, drawn from (0, 0) = baseline centre


def cedilla():
    return strokes(Path(4, 20).l((-4, -40)).c((40, -44), (58, -70), (48, -100)).c((36, -130), (-10, -136), (-48, -120)))


def ogonek():
    return strokes(Path(0, 20).c((-46, -30), (-56, -90), (-24, -122)).c((-4, -138), (28, -134), (52, -118)))


def commabelow():
    return strokes(Path(8, -40).c((16, -70), (8, -120), (-24, -168)))


ABOVE = {
    0x0300: grave, 0x0301: acute, 0x0302: circumflex, 0x0303: tilde, 0x0304: macron,
    0x0306: breve, 0x0307: dotaccent, 0x0308: dieresis, 0x030A: ring, 0x030B: hungarumlaut,
    0x030C: caron,
}
BELOW = {0x0326: commabelow, 0x0327: cedilla, 0x0328: ogonek}

# where accents sit: (x anchor from skeleton bounds, lift)
GAP_LC = 70  # between x-height ink and accent ink
GAP_UC = 58


def _bounds(items):
    pts = np.vstack([s.pts for s in items])
    return pts.min(axis=0), pts.max(axis=0)


def _anchor_x(base_name, lo, hi):
    special = {"a": 150, "d": 150, "g": 150, "q": 150, "b": 160, "p": 160, "h": 150,
               "t": 110, "l": 0, "dotlessi": 0, "dotlessj": 0, "r": 100, "G": 205, "J": 290,
               "L": 40}
    if base_name in special:
        return special[base_name]
    return (lo[0] + hi[0]) / 2.0


def _is_cap(base_name):
    return any(chr(u).isupper() for u in REGISTRY[base_name].unicodes)


def compose(base_name, marks_above=(), marks_below=(), cap=None):
    base = strokes(REGISTRY[base_name].draw())
    lo, hi = _bounds(base)
    ax = _anchor_x(base_name, lo, hi)
    if cap is None:
        cap = _is_cap(base_name)
    y = (CAP + GAP_UC if cap else XH + GAP_LC) + 34
    if not cap and hi[1] > XT + 60:  # ascender: the accent goes above it
        y = hi[1] + 34 + GAP_LC
    out = list(base)
    for fn in marks_above:
        mk = fn()
        out += moved(mk, lambda p, ax=ax, y=y: p + [ax, y])
        mlo, mhi = _bounds(mk)
        y += (mhi[1] - mlo[1]) + 70
    for fn in marks_below:
        bx = hi[0] - 34 if fn is ogonek else (lo[0] + hi[0]) / 2.0
        out += moved(fn(), lambda p, bx=bx: p + [bx, 0.0])
    return out


def _side(base_name):
    gd = REGISTRY[base_name]
    return gd.left, gd.right


def register_composed(cp, base_name, above, below):
    name = gname(cp)
    left, right = _side(base_name)
    glyph(name, cp, left, right)(lambda: compose(base_name, above, below))


def _base_for(ch, above):
    if above and ch == "i":
        return "dotlessi"
    if above and ch == "j":
        return "dotlessj"
    return gname(ord(ch))


# dotless i and j carry accents


@glyph("dotlessi", 0x131, "stem", "stem")
def dotlessi():
    return strokes(L((0, XT), (0, B)))


@glyph("dotlessj", 0x237, "arm", "stem")
def dotlessj():
    return strokes(Path(0, XT).l((0, -70)).c((0, -150), (-45, -183), (-110, -183)).c((-140, -183), (-160, -174), (-175, -160)))


def build_accented(ranges):
    """Register every precomposed letter in `ranges` whose parts we can draw."""
    for cp in ranges:
        ch = chr(cp)
        name = gname(cp)
        if name in REGISTRY:
            continue
        decomp = unicodedata.normalize("NFD", ch)
        if len(decomp) < 2:
            continue
        above, below = [], []
        ok = True
        for m in decomp[1:]:
            mc = ord(m)
            if mc in ABOVE:
                above.append(ABOVE[mc])
            elif mc in BELOW:
                below.append(BELOW[mc])
            else:
                ok = False
        base = _base_for(decomp[0], bool(above))
        if ok and base in REGISTRY:
            register_composed(cp, base, above, below)


# caron on tall letters is written as an apostrophe beside the stem


def _apostrophe(x, y):
    return Path(x + 6, y + 90).c((x + 22, y + 70), (x + 20, y + 30), (x - 8, y - 16))


@glyph("dcaron", 0x10F, "round", 40)
def dcaron():
    return strokes(REGISTRY["d"].draw(), _apostrophe(390, AT - 110))


@glyph("lcaron", 0x13E, "stem", 20)
def lcaron():
    return strokes(REGISTRY["l"].draw(), _apostrophe(100, AT - 110))


@glyph("tcaron", 0x165, "arm", 20)
def tcaron():
    return strokes(REGISTRY["t"].draw(), _apostrophe(200, AT - 150))


@glyph("Lcaron", 0x13D, "Stem", "Open")
def Lcaron():
    return strokes(REGISTRY["L"].draw(), _apostrophe(120, CT - 110))


@glyph("Dcroat", 0x110, "Stem", "Round")
def Dcroat():
    return strokes(REGISTRY["D"].draw(), L((-70, 350), (130, 356)))


@glyph("Eth", 0xD0, "Stem", "Round")
def Eth():
    return strokes(REGISTRY["D"].draw(), L((-70, 350), (130, 356)))


@glyph("dcroat", 0x111, "round", "stem")
def dcroat():
    return strokes(REGISTRY["d"].draw(), L((210, AT - 90), (380, AT - 84)))


@glyph("eth", 0xF0, "round", "round")
def eth():
    return strokes(
        Path(90, AT - 20).c((200, 690), (310, 560), (310, 330)).c((310, 130), (250, 24), (155, 24))
        .c((60, 24), (0, 110), (0, 240)).c((0, 370), (70, 440), (155, 440)).c((230, 440), (290, 400), (310, 340)),
        L((80, 600), (260, 700)),
    )


@glyph("Hbar", 0x126, "Stem", "Stem")
def Hbar():
    return strokes(REGISTRY["H"].draw(), L((-50, 560), (400, 566)))


@glyph("hbar", 0x127, "stem", "stem")
def hbar():
    return strokes(REGISTRY["h"].draw(), L((-60, 640), (170, 646)))


@glyph("Lslash", 0x141, "Stem", "Open")
def Lslash():
    return strokes(REGISTRY["L"].draw(), L((-60, 290), (130, 420)))


@glyph("lslash", 0x142, "arm", "tail")
def lslash():
    return strokes(REGISTRY["l"].draw(), L((-80, 330), (90, 460)))


@glyph("Tbar", 0x166, "Open", "Open")
def Tbar():
    return strokes(REGISTRY["T"].draw(), L((80, 360), (300, 366)))


@glyph("tbar", 0x167, "arm", "open")
def tbar():
    return strokes(REGISTRY["t"].draw(), L((20, 330), (210, 336)))


@glyph("Oslash", 0xD8, "Round", "Round")
def Oslash():
    return strokes(REGISTRY["O"].draw(), L((-10, -30), (420, CT + 40)))


@glyph("oslash", 0xF8, "round", "round")
def oslash():
    return strokes(REGISTRY["o"].draw(), L((-10, -30), (330, XT + 40)))


@glyph("AE", 0xC6, "Diag", "Open")
def AE():
    return strokes(
        L((0, B), (260, CT)), L((260, CT), (560, CT + 4)), L((260, CT), (270, B), (570, B + 4)),
        L((280, 360), (520, 366)), L((110, 250), (270, 254)),
    )


@glyph("ae", 0xE6, "round", "open")
def ae():
    a_ = REGISTRY["a"].draw()
    e_ = moved(REGISTRY["e"].draw(), lambda p: p + [300, 0])
    return strokes(a_, e_)


@glyph("OE", 0x152, "Round", "Open")
def OE():
    return strokes(
        Path(330, CT).l((200, CT)).c((80, CT), (0, 540), (0, 350)).c((0, 150), (80, B), (200, B)).l((330, B)),
        L((330, CT + 6), (330, B)), L((330, CT + 4), (590, CT + 8)), L((330, 360), (550, 366)), L((330, B), (600, B + 4)),
    )


@glyph("oe", 0x153, "round", "open")
def oe():
    o_ = REGISTRY["o"].draw()
    e_ = moved(REGISTRY["e"].draw(), lambda p: p + [290, 0])
    return strokes(o_, e_)


@glyph("germandbls", 0xDF, "stem", "open")
def germandbls():
    return strokes(
        Path(0, B).l((0, 540)).c((0, 680), (70, AT + 10), (160, AT + 10)).c((250, AT + 10), (300, 680), (300, 610))
        .c((300, 530), (230, 480), (160, 470)).c((260, 460), (330, 390), (330, 270))
        .c((330, 120), (250, 24), (160, 24)).c((120, 24), (90, 34), (70, 50))
    )


@glyph("Thorn", 0xDE, "Stem", "Round")
def Thorn():
    return strokes(
        L((0, CT), (0, B)),
        Path(0, 540).l((150, 540)).c((255, 540), (310, 480), (310, 390)).c((310, 300), (250, 230), (150, 230)).l((0, 230)),
    )


@glyph("thorn", 0xFE, "stem", "round")
def thorn():
    return strokes(L((0, AT), (0, -183)), REGISTRY["b"].draw()[1:])


@glyph("kgreenlandic", 0x138, "stem", "diag")
def kgreenlandic():
    return strokes(L((0, XT), (0, B)), L((270, XT), (18, 250)), L((100, 310), (290, B)))


@glyph("Eng", 0x14A, "Stem", "Stem")
def Eng():
    return strokes(
        L((0, B), (0, CT)),
        Path(0, 480).c((40, 620), (130, CT + 10), (200, CT + 10)).c((300, CT + 10), (350, 600), (350, 480))
        .l((350, 20)).c((350, -100), (290, -160), (210, -160)).c((170, -160), (140, -150), (120, -130)),
    )


@glyph("eng", 0x14B, "stem", "stem")
def eng():
    return strokes(
        L((0, XT + 4), (0, B)),
        Path(8, 350).c((29, 460), (98, XT + 2), (176, XT + 2)).c((272, XT + 2), (300, 460), (300, 360))
        .l((300, -60)).c((300, -140), (250, -183), (190, -183)).c((150, -183), (120, -170), (100, -150)),
    )


@glyph("longs", 0x17F, "stem", "arm")
def longs():
    return strokes(Path(40, B).l((40, 560)).c((40, 680), (90, AT), (160, AT)).c((200, AT), (225, 726), (240, 708)))


@glyph("napostrophe", 0x149, 20, "stem")
def napostrophe():
    return strokes(_apostrophe(0, CT - 110), moved(REGISTRY["n"].draw(), lambda p: p + [90, 0]))


@glyph("IJ", 0x132, "Stem", "Stem")
def IJ():
    return strokes(REGISTRY["I"].draw(), moved(REGISTRY["J"].draw(), lambda p: p + [110, 0]))


@glyph("ij", 0x133, "stem", "stem")
def ij():
    return strokes(REGISTRY["i"].draw(), moved(REGISTRY["j"].draw(), lambda p: p + [150, 0]))


@glyph("Ldot", 0x13F, "Stem", "Open")
def Ldot():
    return strokes(REGISTRY["L"].draw(), dot(200, 380, 7))


@glyph("ldot", 0x140, "stem", "open")
def ldot():
    return strokes(REGISTRY["l"].draw(), dot(160, 380, 7))


LATIN_ACCENTED = list(range(0xC0, 0x100)) + list(range(0x100, 0x180)) + list(range(0x218, 0x21C))


# accents on their own (spacing marks), standing where they would over an x-height letter


def _spacing(fn, below=False):
    def draw():
        y = 0.0 if below else XH + GAP_LC + 34
        return moved(fn(), lambda p: p + [0.0, y])

    return draw


SPACING = [
    (0x60, "grave", grave), (0xA8, "dieresis", dieresis), (0xAF, "macron", macron),
    (0xB4, "acute", acute), (0xB8, "cedilla", cedilla, True), (0x2C6, "circumflex", circumflex),
    (0x2C7, "caron", caron), (0x2D8, "breve", breve), (0x2D9, "dotaccent", dotaccent),
    (0x2DA, "ring", ring), (0x2DB, "ogonek", ogonek, True), (0x2DC, "tilde", tilde),
    (0x2DD, "hungarumlaut", hungarumlaut),
]

for _cp, _name, _fn, *_below in SPACING:
    glyph(_name, _cp, 40, 40, variants=1)(_spacing(_fn, bool(_below)))
