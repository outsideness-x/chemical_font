"""Hangul: 11,172 syllables composed from hand-drawn jamo.

A syllable is laid out in one of six classic schemes: the vowel stands to the
right (가), lies below (고) or wraps around (과) the initial consonant, with
or without a final consonant (각 곡 곽). Each consonant is drawn for its
position — ㄱ before ㅏ sweeps down to the left, before ㅗ it drops straight —
and every stroke is inked by the same pen as the Latin and Cyrillic, a touch
lighter in crowded syllables so they never clog.
"""

import numpy as np

from .registry import glyph
from .skel import L, Path, Stroke, loop, strokes

ADVANCE = 900
FT, FB = 700, 12  # skeleton top and bottom of the syllable frame
FL, FR = 92, 808  # skeleton left and right


def F(u, v):
    """Normalised frame coordinates -> font units."""
    return (FL + u * (FR - FL), FB + v * (FT - FB))


def FB_(u0, v0, u1, v1):
    return Box(*F(u0, v0), *F(u1, v1))


CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"

DOUBLE = {"ㄲ": "ㄱㄱ", "ㄸ": "ㄷㄷ", "ㅃ": "ㅂㅂ", "ㅆ": "ㅅㅅ", "ㅉ": "ㅈㅈ",
          "ㄳ": "ㄱㅅ", "ㄵ": "ㄴㅈ", "ㄶ": "ㄴㅎ", "ㄺ": "ㄹㄱ", "ㄻ": "ㄹㅁ", "ㄼ": "ㄹㅂ",
          "ㄽ": "ㄹㅅ", "ㄾ": "ㄹㅌ", "ㄿ": "ㄹㅍ", "ㅀ": "ㄹㅎ", "ㅄ": "ㅂㅅ"}

VERT = "ㅏㅐㅑㅒㅓㅔㅕㅖㅣ"
HORIZ = "ㅗㅛㅜㅠㅡ"
COMPOUND = {"ㅘ": ("ㅗ", "ㅏ"), "ㅙ": ("ㅗ", "ㅐ"), "ㅚ": ("ㅗ", "ㅣ"), "ㅝ": ("ㅜ", "ㅓ"),
            "ㅞ": ("ㅜ", "ㅔ"), "ㅟ": ("ㅜ", "ㅣ"), "ㅢ": ("ㅡ", "ㅣ")}


# -- consonants: drawn into a box, shaped by where they stand -------------------


class Box:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    @property
    def w(self):
        return self.x1 - self.x0

    @property
    def h(self):
        return self.y1 - self.y0

    def __call__(self, u, v):
        return (self.x0 + u * self.w, self.y0 + v * self.h)

    def split(self, gap=0.08, left_share=0.5):
        mid = self.x0 + self.w * left_share
        g = self.w * gap / 2
        return Box(self.x0, self.y0, mid - g, self.y1), Box(mid + g, self.y0, self.x1, self.y1)

    def fit(self, max_ratio=1.25, min_ratio=0.0, anchor=(0.5, 0.5)):
        """Shrink to keep width/height within [min_ratio, max_ratio]."""
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        w, h = self.w, self.h
        if w > h * max_ratio:
            nw = h * max_ratio
            x0 += (w - nw) * anchor[0]
            x1 = x0 + nw
        elif min_ratio and w < h * min_ratio:
            nh = w / min_ratio
            y0 += (h - nh) * anchor[1]
            y1 = y0 + nh
        return Box(x0, y0, x1, y1)


def c_giyeok(b, ctx):
    if ctx in ("v", "c"):
        return [Path(*b(0.03, 1)).l(b(0.84, 1)).c(b(0.9, 0.62), b(0.78, 0.26), b(0.24, 0.0))]
    return [Path(*b(0.02, 1)).l(b(0.93, 1)).c(b(0.94, 0.6), b(0.93, 0.3), b(0.9, 0.0))]


def c_nieun(b, ctx):
    rise = 0.1 if ctx in ("v", "c") else 0.04
    return [Path(*b(0.05, 1)).l(b(0.05, 0.02)).l(b(0.98, rise))]


def c_digeut(b, ctx):
    return [L(b(0.05, 1), b(0.9, 1)), Path(*b(0.06, 1)).l(b(0.06, 0.02)).l(b(0.98, 0.04))]


def c_rieul(b, ctx):
    return [Path(*b(0.05, 1)).l(b(0.88, 1)).l(b(0.88, 0.52)).l(b(0.1, 0.5)).l(b(0.1, 0.02)).l(b(0.98, 0.04))]


def c_mieum(b, ctx):
    b = b.fit(1.7)
    return [L(b(0.05, 1), b(0.05, 0.02)), Path(*b(0.05, 1)).l(b(0.95, 1)).l(b(0.95, 0.02)),
            L(b(0.05, 0.02), b(0.95, 0.02))]


def c_bieup(b, ctx):
    b = b.fit(1.7)
    return [L(b(0.07, 1), b(0.07, 0.02)), L(b(0.93, 1), b(0.93, 0.02)), L(b(0.07, 0.5), b(0.93, 0.5)),
            L(b(0.07, 0.02), b(0.93, 0.02))]


def _siot(b, ctx, top=1.0):
    if ctx in ("v", "c"):
        return [Path(*b(0.52, top)).c(b(0.5, top * 0.62), b(0.32, top * 0.24), b(0.0, 0.0)),
                L(b(0.44, top * 0.5), b(1.0, 0.02))]
    return [Path(*b(0.5, top)).c(b(0.46, top * 0.62), b(0.3, top * 0.24), b(0.02, 0.0)),
            L(b(0.47, top * 0.58), b(0.98, 0.02))]


def c_siot(b, ctx):
    return _siot(b, ctx)


def c_ieung(b, ctx):
    b = b.fit(1.3, 0.85)
    return [loop(b.x0, b.y0, b.x1, b.y1, k=0.58, start=0, overlap=0.18)]


def _jieut(b, ctx, top=1.0):
    bar = L(b(0.05, top), b(0.9, top))
    if ctx in ("v", "c"):
        return [bar, Path(*b(0.56, top)).c(b(0.52, top * 0.6), b(0.32, top * 0.22), b(0.0, 0.0)),
                L(b(0.46, top * 0.46), b(1.0, 0.02))]
    return [bar, Path(*b(0.52, top)).c(b(0.48, top * 0.6), b(0.3, top * 0.22), b(0.02, 0.0)),
            L(b(0.49, top * 0.52), b(0.98, 0.02))]


def c_jieut(b, ctx):
    return _jieut(b, ctx)


def c_chieut(b, ctx):
    return [L(b(0.44, 1.0), b(0.56, 0.86))] + _jieut(b, ctx, top=0.74)


def c_kieuk(b, ctx):
    if ctx in ("v", "c"):
        return c_giyeok(b, ctx) + [L(b(0.04, 0.52), b(0.78, 0.54))]
    return c_giyeok(b, ctx) + [L(b(0.04, 0.5), b(0.9, 0.52))]


def c_tieut(b, ctx):
    return [L(b(0.06, 1), b(0.92, 1)), L(b(0.06, 0.51), b(0.86, 0.52)),
            Path(*b(0.06, 1)).l(b(0.06, 0.02)).l(b(0.98, 0.04))]


def c_pieup(b, ctx):
    b = b.fit(1.9)
    return [L(b(0.02, 1), b(0.98, 1)), L(b(0.3, 1), b(0.34, 0.02)), L(b(0.7, 1), b(0.66, 0.02)),
            L(b(0.0, 0.02), b(1.0, 0.02))]


def c_hieut(b, ctx):
    ring = Box(*b(0.16, 0.0), *b(0.84, 0.6)).fit(1.35, 0.8, anchor=(0.5, 1.0))
    return [L(b(0.48, 1.0), b(0.52, 0.86)), L(b(0.08, 0.77), b(0.92, 0.78)),
            loop(ring.x0, ring.y0, ring.x1, ring.y1, k=0.58, overlap=0.18)]


CONSONANTS = {"ㄱ": c_giyeok, "ㄴ": c_nieun, "ㄷ": c_digeut, "ㄹ": c_rieul, "ㅁ": c_mieum, "ㅂ": c_bieup,
              "ㅅ": c_siot, "ㅇ": c_ieung, "ㅈ": c_jieut, "ㅊ": c_chieut, "ㅋ": c_kieuk, "ㅌ": c_tieut,
              "ㅍ": c_pieup, "ㅎ": c_hieut}


def consonant(ch, box, ctx):
    if ch in DOUBLE:
        a, b = DOUBLE[ch]
        share = 0.5
        if ch in ("ㄳ", "ㄵ", "ㄶ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅄ"):
            share = 0.48
        left, right = box.split(0.1, share)
        inner = "h" if ctx == "f" else ctx
        return CONSONANTS[a](left, inner) + CONSONANTS[b](right, inner)
    return CONSONANTS[ch](box, ctx)


# -- vowels and layouts ---------------------------------------------------------


def _stem(u, top, bot):
    return L(F(u, top), F(u, bot))


def _bar(u0, u1, v):
    a, b = F(u0, v), F(u1, v)
    return L(a, (b[0], b[1] + 5))


def vertical_vowel(v, top, bot, final, shift=0.0):
    """Strokes of a right-standing vowel, and where the consonant's room ends."""
    mid = bot + (top - bot) * (0.56 if final else 0.52)
    d = 0.085 if final else 0.11
    s = shift
    if v == "ㅏ":
        x = 0.80 + s
        return [_stem(x, top, bot), _bar(x, x + 0.17, mid)], 0.67 + s
    if v == "ㅑ":
        x = 0.80 + s
        return [_stem(x, top, bot), _bar(x, x + 0.165, mid + d), _bar(x, x + 0.165, mid - d)], 0.66 + s
    if v == "ㅓ":
        x = 0.935 + s
        return [_bar(x - 0.185, x, mid), _stem(x, top, bot)], 0.63 + s
    if v == "ㅕ":
        x = 0.935 + s
        return [_bar(x - 0.18, x, mid + d), _bar(x - 0.18, x, mid - d), _stem(x, top, bot)], 0.63 + s
    if v == "ㅣ":
        x = 0.86 + s
        return [_stem(x, top, bot)], 0.72 + s
    if v == "ㅐ":
        a, b = 0.70 + s, 0.95 + s
        return [_stem(a, top, bot), _bar(a, b, mid), _stem(b, top, bot)], 0.58 + s
    if v == "ㅒ":
        a, b = 0.70 + s, 0.95 + s
        return [_stem(a, top, bot), _bar(a, b, mid + d), _bar(a, b, mid - d), _stem(b, top, bot)], 0.58 + s
    if v == "ㅔ":
        a, b = 0.79 + s, 0.96 + s
        return [_bar(a - 0.17, a, mid), _stem(a, top, bot), _stem(b, top, bot)], 0.56 + s
    if v == "ㅖ":
        a, b = 0.79 + s, 0.96 + s
        return [_bar(a - 0.165, a, mid + d), _bar(a - 0.165, a, mid - d), _stem(a, top, bot),
                _stem(b, top, bot)], 0.55 + s
    raise KeyError(v)


def horizontal_vowel(v, y, u0, u1, reach, cu=None):
    """Strokes of a lying vowel with its bar at y; `reach` = tick/leg length."""
    cu = (u0 + u1) / 2 if cu is None else cu
    bar = _bar(u0, u1, y)
    if v == "ㅗ":
        return [L(F(cu, y + reach), F(cu, y)), bar]
    if v == "ㅛ":
        g = (u1 - u0) * 0.17
        return [L(F(cu - g, y + reach), F(cu - g, y)), L(F(cu + g, y + reach), F(cu + g, y)), bar]
    if v == "ㅜ":
        c = cu + (u1 - u0) * 0.05
        return [bar, L(F(c, y), F(c, y - reach))]
    if v == "ㅠ":
        g = (u1 - u0) * 0.17
        return [bar, L(F(cu - g, y), F(cu - g, y - reach)), L(F(cu + g, y), F(cu + g, y - reach))]
    if v == "ㅡ":
        return [bar]
    raise KeyError(v)


# horizontal vowels: bar height, tick/leg reach, bottom of the consonant's room
H_OPEN = {"ㅗ": (0.12, 0.18, 0.40), "ㅛ": (0.12, 0.18, 0.40), "ㅜ": (0.48, 0.46, 0.60),
          "ㅠ": (0.48, 0.44, 0.60), "ㅡ": (0.30, 0.0, 0.45)}
# ... with a final: bar, reach, consonant bottom, final top
H_CLOSED = {"ㅗ": (0.53, 0.11, 0.73, 0.40), "ㅛ": (0.53, 0.11, 0.73, 0.40),
            "ㅜ": (0.63, 0.18, 0.77, 0.37), "ㅠ": (0.63, 0.17, 0.77, 0.37),
            "ㅡ": (0.58, 0.0, 0.72, 0.42)}


def layout(v, has_final):
    """-> (vowel strokes, initial box, context, final box or None)"""
    if v in VERT:
        top, bot = 1.0, (0.45 if has_final else 0.0)
        vs, right = vertical_vowel(v, top, bot, has_final)
        if has_final:
            return vs, FB_(0.02, 0.57, right, 0.98), "v", FB_(0.08, 0.0, 0.93, 0.37)
        return vs, FB_(0.02, 0.17, right, 0.95), "v", None

    if v in HORIZ:
        if not has_final:
            y, reach, cb = H_OPEN[v]
            vs = horizontal_vowel(v, y, 0.04, 0.96, reach)
            return vs, FB_(0.15, cb, 0.85, 1.0), "h", None
        y, reach, cb, ft = H_CLOSED[v]
        vs = horizontal_vowel(v, y, 0.06, 0.94, reach)
        return vs, FB_(0.19, cb, 0.81, 1.0), "h", FB_(0.12, 0.0, 0.88, ft)

    h, vv = COMPOUND[v]
    top, bot = 1.0, (0.45 if has_final else 0.0)
    vert, right = vertical_vowel(vv, top, bot, has_final, shift=0.03 if vv in "ㅏㅣ" else 0.01)
    if h == "ㅗ":
        y, reach = (0.60, 0.1) if has_final else (0.22, 0.16)
        hs = horizontal_vowel(h, y, 0.0, right + 0.03, reach, cu=right / 2)
        cb = y + reach + 0.07
    elif h == "ㅜ":
        y, reach = (0.66, 0.16) if has_final else (0.56, 0.5)
        hs = horizontal_vowel(h, y, 0.0, right + (0.02 if vv == "ㅣ" else -0.03), reach, cu=right / 2 - 0.04)
        cb = y + 0.12
    else:
        y = 0.62 if has_final else 0.36
        hs = horizontal_vowel(h, y, 0.0, right + 0.03, 0)
        cb = y + 0.13
    init = FB_(0.03, cb, right - 0.04, 0.98)
    fin = FB_(0.08, 0.0, 0.92, 0.36) if has_final else None
    return hs + vert, init, "c", fin


def _weight(cho, v, jong):
    w = 0.95
    if jong:
        w *= 0.93
    if jong in DOUBLE:
        w *= 0.95
    if cho in DOUBLE:
        w *= 0.96
    if v in COMPOUND:
        w *= 0.96
    if v in "ㅒㅖㅙㅞ":
        w *= 0.97
    return w


def syllable(cp):
    i = cp - 0xAC00
    cho, jung, jong = CHO[i // 588], JUNG[(i % 588) // 28], JONG[i % 28].strip()
    vs, init, ctx, fin = layout(jung, bool(jong))
    parts = consonant(cho, init, ctx) + vs
    if jong:
        parts += consonant(jong, fin, "f")
    w = _weight(cho, jung, jong)
    return [Stroke(s.pts, weight=w) for s in strokes(parts)]


# -- standalone jamo (Hangul Compatibility Jamo, U+3131-U+318E) ---------------

COMPAT_CONSONANTS = "ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅃㅄㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
COMPAT_VOWELS = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"


def compat(ch):
    if ch in COMPAT_CONSONANTS:
        wide = ch in DOUBLE
        box = FB_(0.1 if not wide else 0.04, 0.12, 0.9 if not wide else 0.96, 0.86)
        return [Stroke(s.pts, weight=0.95) for s in strokes(consonant(ch, box, "h"))]
    if ch in VERT:
        vs, _ = vertical_vowel(ch, 0.96, 0.04, False, shift=-0.36)
        return [Stroke(s.pts, weight=0.95) for s in strokes(vs)]
    if ch in HORIZ:
        reach = 0.0 if ch == "ㅡ" else 0.27
        y = 0.32 if ch in "ㅗㅛ" else (0.62 if ch in "ㅜㅠ" else 0.48)
        return [Stroke(s.pts, weight=0.95) for s in strokes(horizontal_vowel(ch, y, 0.1, 0.9, reach))]
    vs, _, _, _ = layout(ch, False)
    return [Stroke(s.pts, weight=0.95) for s in strokes(vs)]


# Hangul sits a little calmer on the line, with a softer ragged edge
HANGUL_HAND = {"calm": 0.6, "rough": 1.7, "rough_fine": 0.2}


def register(limit=None):
    for ch in COMPAT_CONSONANTS + COMPAT_VOWELS:
        cp = ord(ch)
        glyph(f"uni{cp:04X}", cp, variants=1, advance=ADVANCE, hand=HANGUL_HAND)(lambda c=ch: compat(c))
    last = 0xD7A3 if limit is None else min(0xD7A3, 0xAC00 + limit - 1)
    for cp in range(0xAC00, last + 1):
        glyph(f"uni{cp:04X}", cp, variants=1, advance=ADVANCE, hand=HANGUL_HAND)(lambda c=cp: syllable(c))
