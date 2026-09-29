"""Cyrillic.

Capitals and lowercase come from the same drawings at two heights: in a
printed hand, most Cyrillic lowercase letters are small capitals (в г д ж к
л м н п т ...). Because letters are skeletons, a lowercase letter keeps the
full weight of the pen instead of being a shrunken capital.
"""

import numpy as np

from . import marks
from .metrics import AT, B, CT, DB, OS, XT
from .registry import REGISTRY, glyph
from .skel import L, Path, loop, moved, strokes

UC = dict(t=CT, lc=False)
LC = dict(t=XT, lc=True)


def _y(t, f):
    return B + f * (t - B)


# -- parametric drawings: (top skeleton line, width) -> strokes ----------------


def be(t, w):
    m = _y(t, 0.55)
    return strokes(
        Path(w * 0.92, t + 6).l((0, t)).l((0, B)),
        Path(0, m).l((w * 0.45, m)).c((w * 0.82, m), (w, m - (m - B) * 0.2), (w, (m + B) / 2))
        .c((w, B + (m - B) * 0.2), (w * 0.82, B), (w * 0.45, B)).l((0, B)),
    )


def ve(t, w):
    m = _y(t, 0.54)
    return strokes(
        L((0, t), (0, B)),
        Path(0, t).l((w * 0.45, t)).c((w * 0.76, t), (w * 0.9, t - (t - m) * 0.2), (w * 0.9, (t + m) / 2))
        .c((w * 0.9, m + (t - m) * 0.2), (w * 0.72, m), (w * 0.42, m)).l((0, m)),
        Path(0, m).l((w * 0.5, m)).c((w * 0.83, m), (w, m - (m - B) * 0.2), (w, (m + B) / 2))
        .c((w, B + (m - B) * 0.2), (w * 0.82, B), (w * 0.48, B)).l((0, B)),
    )


def ge(t, w):
    return strokes(Path(w, t + 6).l((0, t)).l((0, B)))


def ghe_up(t, w):
    return strokes(Path(w, t + (t - B) * 0.2).l((w, t)).l((0, t)).l((0, B)))


def de(t, w, feet):
    return strokes(
        Path(w * 0.1, B).c((w * 0.2, _y(t, 0.35)), (w * 0.25, _y(t, 0.75)), (w * 0.27, t)).l((w * 0.92, t)).l((w * 0.92, B)),
        L((-w * 0.06, feet), (-w * 0.06, B), (w * 1.06, B), (w * 1.06, feet)),
    )


def zhe(t, w):
    m = _y(t, 0.47)
    c = w / 2
    return strokes(
        L((c, t + 4), (c, B)),
        L((0, t), (c - 24, m), (-6, B)),
        L((w, t), (c + 24, m), (w + 6, B)),
    )


def ze(t, w):
    m = _y(t, 0.54)
    top, bot = t + OS, B - OS
    return strokes(
        Path(w * 0.04, t - (t - B) * 0.13).c((w * 0.16, top), (w * 0.34, top), (w * 0.5, top))
        .c((w * 0.8, top), (w * 0.94, t - (t - B) * 0.1), (w * 0.94, t - (t - B) * 0.24))
        .c((w * 0.94, m + (t - m) * 0.25), (w * 0.72, m), (w * 0.44, m)),
        Path(w * 0.44, m).c((w * 0.8, m), (w, m - (m - B) * 0.25), (w, (m + B) / 2))
        .c((w, B + (m - B) * 0.1), (w * 0.8, bot), (w * 0.5, bot))
        .c((w * 0.26, bot), (w * 0.08, B + (t - B) * 0.07), (0, B + (t - B) * 0.19)),
    )


def i_(t, w):
    return strokes(Path(0, t).l((0, B)).l((w, t)).l((w, B)))


def ka(t, w):
    m = _y(t, 0.47)
    return strokes(L((0, t), (0, B)), L((w * 0.92, t), (12, m - 20)), L((w * 0.3, m + 30), (w, B)))


def el(t, w):
    return strokes(Path(0, B).c((w * 0.18, _y(t, 0.25)), (w * 0.26, _y(t, 0.62)), (w * 0.28, t)).l((w, t)).l((w, B)))


def em(t, w):
    return strokes(L((0, B), (w * 0.03, t), (w * 0.5, _y(t, 0.33)), (w * 0.97, t), (w, B)))


def en(t, w):
    m = _y(t, 0.5)
    return strokes(L((0, t), (0, B)), L((w, t), (w, B)), L((0, m), (w, m + 6)))


def pe(t, w):
    return strokes(Path(0, B).l((0, t)).l((w, t + 4)).l((w, B)))


def te(t, w):
    return strokes(L((0, t), (w, t + 6)), L((w / 2, t), (w / 2, B)))


def u_cap(t, w):
    j = _y(t, 0.34)
    return strokes(
        L((0, t), (w * 0.5, j)),
        Path(w, t).l((w * 0.3, B + 30)).c((w * 0.25, B), (w * 0.18, B - OS), (w * 0.08, B - OS))
        .c((0, B - OS), (-w * 0.05, B + 10), (-w * 0.08, B + 30)),
    )


def ef(t, w, up, down):
    return strokes(L((w / 2, up), (w / 2, down)), loop(0, _y(t, 0.16) if t > XT else B - OS, w,
                                                        _y(t, 0.86) if t > XT else t + OS, k=0.6, overlap=0.2))


def tse(t, w, tail):
    return strokes(Path(0, t).l((0, B)).l((w * 1.12, B)).l((w * 1.12, tail)), L((w, t), (w, B)))


def che(t, w):
    j = _y(t, 0.38)
    return strokes(
        Path(0, t).l((0, _y(t, 0.64))).c((0, _y(t, 0.45)), (w * 0.2, j), (w * 0.45, j))
        .c((w * 0.66, j), (w * 0.86, _y(t, 0.42)), (w, _y(t, 0.47))),
        L((w, t), (w, B)),
    )


def sha(t, w):
    return strokes(Path(0, t).l((0, B)).l((w, B)).l((w, t)), L((w / 2, t), (w / 2, B)))


def shcha(t, w, tail):
    return strokes(Path(0, t).l((0, B)).l((w * 1.1, B)).l((w * 1.1, tail)), L((w / 2, t), (w / 2, B)), L((w, t), (w, B)))


def _soft_bowl(t, w, x0=0.0):
    m = _y(t, 0.55)
    return (
        Path(x0, m).l((x0 + w * 0.45, m)).c((x0 + w * 0.82, m), (x0 + w, m - (m - B) * 0.2), (x0 + w, (m + B) / 2))
        .c((x0 + w, B + (m - B) * 0.2), (x0 + w * 0.82, B), (x0 + w * 0.45, B)).l((x0, B))
    )


def soft(t, w):
    return strokes(L((0, t), (0, B)), _soft_bowl(t, w))


def hard(t, w):
    return strokes(Path(-w * 0.34, t - 4).l((0, t)).l((0, B)), _soft_bowl(t, w))


def yeru(t, w):
    return strokes(L((0, t), (0, B)), _soft_bowl(t, w * 0.8), L((w * 1.18, t), (w * 1.18, B)))


def e_rev(t, w):
    top, bot = t + OS, B - OS
    mid = (t + B) / 2
    h = t - B
    return strokes(
        Path(w * 0.02, t - h * 0.13).c((w * 0.14, top), (w * 0.32, top), (w * 0.48, top))
        .c((w * 0.84, top), (w, t - h * 0.27), (w, mid)).c((w, B + h * 0.27), (w * 0.84, bot), (w * 0.48, bot))
        .c((w * 0.3, bot), (w * 0.12, B + h * 0.06), (0, B + h * 0.16)),
        L((w * 0.3, mid), (w * 0.97, mid + 5)),
    )


def yu(t, w):
    mid = (t + B) / 2
    return strokes(L((0, t), (0, B)), L((0, mid), (w * 0.3, mid + 4)), loop(w * 0.27, B - OS, w, t + OS, k=0.6, overlap=0.2))


def ya(t, w):
    m = _y(t, 0.47)
    h = t - B
    return strokes(
        L((w, t), (w, B)),
        Path(w, t).l((w * 0.52, t)).c((w * 0.16, t), (w * 0.02, t - h * 0.14), (w * 0.02, t - h * 0.27))
        .c((w * 0.02, m + h * 0.12), (w * 0.16, m), (w * 0.52, m)).l((w, m)),
        L((w * 0.56, m), (0, B)),
    )


def e_ukr(t, w):
    top, bot = t + OS, B - OS
    mid = (t + B) / 2
    h = t - B
    return strokes(
        Path(w * 0.98, t - h * 0.13).c((w * 0.86, top), (w * 0.68, top), (w * 0.52, top))
        .c((w * 0.16, top), (0, t - h * 0.27), (0, mid)).c((0, B + h * 0.27), (w * 0.16, bot), (w * 0.52, bot))
        .c((w * 0.7, bot), (w * 0.88, B + h * 0.06), (w, B + h * 0.16)),
        L((w * 0.03, mid), (w * 0.7, mid + 5)),
    )


def be_lc(t, w):
    return strokes(
        Path(290, AT - 6).c((170, AT - 60), (30, 600), (12, 380)).c((0, 250), (20, B - OS), (152, B - OS))
        .c((262, B - OS), (306, 100), (306, 240)).c((306, 382), (240, 432), (160, 432))
        .c((92, 432), (42, 392), (16, 330))
    )


# -- the alphabet ---------------------------------------------------------------

# (codepoint of capital, drawing, capital width, lowercase width, sides uc, sides lc)
TABLE = [
    (0x0411, be, 300, 280, ("Stem", "Round"), ("stem", "round")),
    (0x0412, ve, 300, 275, ("Stem", "Round"), ("stem", "round")),
    (0x0413, ge, 280, 240, ("Stem", "Open"), ("stem", "open")),
    (0x0416, zhe, 520, 470, ("Diag", "Diag"), ("diag", "diag")),
    (0x0417, ze, 320, 290, ("Open", "Round"), ("open", "round")),
    (0x0418, i_, 350, 300, ("Stem", "Stem"), ("stem", "stem")),
    (0x041A, ka, 350, 300, ("Stem", "Diag"), ("stem", "diag")),
    (0x041B, el, 350, 310, ("Diag", "Stem"), ("diag", "stem")),
    (0x041C, em, 440, 400, ("Stem", "Stem"), ("stem", "stem")),
    (0x041D, en, 350, 300, ("Stem", "Stem"), ("stem", "stem")),
    (0x041F, pe, 340, 300, ("Stem", "Stem"), ("stem", "stem")),
    (0x0422, te, 380, 330, ("Open", "Open"), ("open", "open")),
    (0x0427, che, 330, 290, ("Stem", "Stem"), ("stem", "stem")),
    (0x0428, sha, 490, 440, ("Stem", "Stem"), ("stem", "stem")),
    (0x042A, hard, 300, 280, ("Open", "Round"), ("open", "round")),
    (0x042B, yeru, 300, 270, ("Stem", "Stem"), ("stem", "stem")),
    (0x042C, soft, 300, 280, ("Stem", "Round"), ("stem", "round")),
    (0x042D, e_rev, 400, 320, ("Open", "Round"), ("open", "round")),
    (0x042E, yu, 520, 460, ("Stem", "Round"), ("stem", "round")),
    (0x042F, ya, 330, 290, ("Diag", "Stem"), ("diag", "stem")),
    (0x0404, e_ukr, 400, 320, ("Round", "Open"), ("round", "open")),
    (0x0490, ghe_up, 290, 250, ("Stem", "Open"), ("stem", "open")),
]

# letters that share their shape with Latin: (cyrillic codepoint, latin glyph)
TWINS = {
    0x0410: "A", 0x0415: "E", 0x041E: "O", 0x0420: "P", 0x0421: "C", 0x0425: "X", 0x0406: "I",
    0x0408: "J", 0x0405: "S",
    0x0430: "a", 0x0435: "e", 0x043E: "o", 0x0440: "p", 0x0441: "c", 0x0443: "y", 0x0445: "x",
    0x0456: "i", 0x0458: "j", 0x0455: "s",
}
# capital twins whose Cyrillic lowercase is a small capital
LATIN_SMALLCAP = {0x0412: "B", 0x041A: "K", 0x041C: "M", 0x041D: "H", 0x0422: "T"}


def _reg(cp, fn, left, right):
    glyph(marks.gname(cp), cp, left, right)(fn)


def register():
    for cp, draw, wu, wl, su, sl in TABLE:
        _reg(cp, (lambda d=draw, w=wu: d(CT, w)), *su)
        _reg(cp + (0x20 if cp < 0x0430 else 1) if cp >= 0x0410 else cp + 0x50, (lambda d=draw, w=wl: d(XT, w)), *sl)
    for cp, src in TWINS.items():
        gd = REGISTRY[src]
        _reg(cp, (lambda s=src: REGISTRY[s].draw()), gd.left, gd.right)

    # letters that need their own proportions or extra parts
    _reg(0x0414, lambda: de(CT, 330, -110), "Diag", "Diag")  # Д
    _reg(0x0434, lambda: de(XT, 300, -100), "diag", "diag")  # д
    _reg(0x0426, lambda: tse(CT, 330, -110), "Stem", "Stem")  # Ц
    _reg(0x0446, lambda: tse(XT, 290, -100), "stem", "stem")  # ц
    _reg(0x0429, lambda: shcha(CT, 480, -110), "Stem", "Stem")  # Щ
    _reg(0x0449, lambda: shcha(XT, 430, -100), "stem", "stem")  # щ
    _reg(0x0423, lambda: u_cap(CT, 370), "Diag", "Diag")  # У
    _reg(0x0424, lambda: ef(CT, 440, CT + 40, B - 40), "Round", "Round")  # Ф
    _reg(0x0444, lambda: ef(XT, 400, AT, DB), "round", "round")  # ф
    _reg(0x0431, lambda: be_lc(XT, 300), "round", "round")  # б
    _reg(0x0491, lambda: ghe_up(XT, 250), "stem", "open")  # ґ

    # accented Cyrillic
    def comp(cp, base_cp, above):
        base = marks.gname(base_cp)
        gd = REGISTRY[base]
        glyph(marks.gname(cp), cp, gd.left, gd.right)(lambda b=base, a=above: marks.compose(b, a))

    comp(0x0401, 0x0415, [marks.dieresis])  # Ё
    comp(0x0451, 0x0435, [marks.dieresis])  # ё
    comp(0x0419, 0x0418, [marks.breve])  # Й
    comp(0x0439, 0x0438, [marks.breve])  # й
    comp(0x040E, 0x0423, [marks.breve])  # Ў
    comp(0x045E, 0x0443, [marks.breve])  # ў
    comp(0x0407, 0x0406, [marks.dieresis])  # Ї
    glyph(marks.gname(0x0457), 0x0457, "stem", "stem")(lambda: marks.compose("dotlessi", [marks.dieresis]))  # ї
