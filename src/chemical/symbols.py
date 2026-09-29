"""Figures, punctuation and symbols."""

import numpy as np

from .metrics import AT, B, CT, DB, OS, XT
from .registry import glyph
from .skel import L, Path, S, dot, filled, light, loop, moved, scale_about, strokes, translate

TOP = XT + OS
BOT = B - OS
CTOP = CT + OS
MATH = 318  # centre line of operators and dashes


def _g(name, uni, left="punct", right="punct", variants=1, **kw):
    return glyph(name, uni, left, right, variants=variants, **kw)


# -- spaces -------------------------------------------------------------------


@glyph("space", 0x20, variants=1, advance=250)
def space():
    return []


@glyph("nbspace", 0xA0, variants=1, advance=250)
def nbspace():
    return []


@glyph("thinspace", 0x2009, variants=1, advance=130)
def thinspace():
    return []


@glyph("ideographicspace", 0x3000, variants=1, advance=900)
def ideographicspace():
    return []


# -- figures (lining, proportional) --------------------------------------------


def _fig(name, uni):
    return glyph(name, uni, "fig", "fig", variants=4)


@_fig("zero", 0x30)
def zero():
    return strokes(loop(0, BOT, 300, CTOP, k=0.6, start=0, overlap=0.22))


@_fig("one", 0x31)
def one():
    return strokes(Path(10, 530).l((140, CT + 6)).l((140, B)))


@_fig("two", 0x32)
def two():
    return strokes(
        Path(18, 540)
        .c((35, 625), (100, CTOP), (172, CTOP))
        .c((262, CTOP), (318, 612), (318, 528))
        .c((318, 430), (236, 330), (10, B + 4))
        .l((334, B))
    )


@_fig("three", 0x33)
def three():
    return strokes(
        Path(22, 585).c((50, 640), (110, CTOP), (172, CTOP)).c((255, CTOP), (305, 622), (305, 548))
        .c((305, 460), (238, 398), (140, 392)),
        Path(140, 392).c((262, 392), (328, 322), (328, 212)).c((328, 90), (248, BOT), (165, BOT))
        .c((88, BOT), (30, 52), (6, 112)),
    )


@_fig("four", 0x34)
def four():
    return strokes(L((196, CT + 6), (0, 248), (344, 248)), L((262, 492), (262, B)))


@_fig("five", 0x35)
def five():
    return strokes(
        L((302, CT + 2), (54, CT - 6), (36, 392)),
        Path(36, 392).c((90, 436), (140, 450), (182, 450)).c((274, 450), (330, 380), (330, 250))
        .c((330, 108), (250, BOT), (160, BOT)).c((90, BOT), (35, 50), (8, 110)),
    )


@_fig("six", 0x36)
def six():
    return strokes(
        Path(284, CT + 6).c((150, 580), (14, 420), (14, 235)).c((14, 90), (84, BOT), (172, BOT))
        .c((262, BOT), (330, 88), (330, 210)).c((330, 336), (258, 412), (172, 412))
        .c((100, 412), (44, 372), (18, 300))
    )


@_fig("seven", 0x37)
def seven():
    return strokes(L((0, CT - 4), (324, CT + 6), (112, B)))


@_fig("eight", 0x38)
def eight():
    return strokes(
        S((262, 606), (168, CTOP), (58, 608), (72, 470), (176, 398), (306, 300), (316, 128),
          (172, BOT), (26, 128), (46, 300), (176, 398), (276, 474), (290, 600), (240, CTOP - 20))
    )


@_fig("nine", 0x39)
def nine():
    return strokes(
        Path(316, 480).c((296, 392), (232, 348), (164, 348)).c((74, 348), (12, 420), (12, 516))
        .c((12, 610), (78, CTOP), (164, CTOP)).c((258, CTOP), (318, 600), (318, 480)).l((292, B))
    )


# -- punctuation ----------------------------------------------------------------


@_g("period", 0x2E)
def period():
    return strokes(dot(0, B + 8, 7))


@_g("comma", 0x2C)
def comma():
    return strokes(Path(12, B + 30).c((22, 8), (12, -58), (-24, -112)))


@_g("colon", 0x3A)
def colon():
    return strokes(dot(0, XT - 30, 7), dot(0, B + 8, 7))


@_g("semicolon", 0x3B)
def semicolon():
    return strokes(dot(10, XT - 30, 7), Path(12, B + 30).c((22, 8), (12, -58), (-24, -112)))


@_g("exclam", 0x21)
def exclam():
    return strokes(L((0, CT + 4), (8, 205)), dot(6, B + 8, 7))


@_g("exclamdown", 0xA1)
def exclamdown():
    return strokes(dot(6, XT - 10, 7), L((8, 370), (0, DB + 20)))


@_g("question", 0x3F)
def question():
    return strokes(
        Path(0, 560).c((10, 640), (70, CTOP), (150, CTOP)).c((240, CTOP), (290, 612), (290, 540))
        .c((290, 452), (222, 410), (172, 380)).c((140, 360), (135, 320), (138, 215)),
        dot(138, B + 8, 7),
    )


@_g("questiondown", 0xBF)
def questiondown():
    return moved(question(), lambda p: np.array([290, CT + B]) - p)


@_g("ellipsis", 0x2026, left=40, right=40)
def ellipsis():
    return strokes(dot(0, B + 8, 7), dot(150, B + 8, 7), dot(300, B + 8, 7))


@_g("periodcentered", 0xB7)
def periodcentered():
    return strokes(dot(0, MATH, 7))


@_g("bullet", 0x2022)
def bullet():
    return strokes(filled(loop(0, MATH - 70, 140, MATH + 70, overlap=0.0)))


# quotes: a marker quote is a short, slightly curved flick


def _flick(x, y, up=True):
    if up:  # opening quote: fat end at the bottom
        return Path(x + 30, y + 110).c((0 + x, y + 80), (x - 8, y + 40), (x + 6, y))
    return Path(x, y + 110).c((x + 22, y + 90), (x + 22, y + 40), (x - 10, y - 10))


@_g("quotesingle", 0x27)
def quotesingle():
    return strokes(L((0, CT + 10), (6, CT - 150)))


@_g("quotedbl", 0x22)
def quotedbl():
    return strokes(L((0, CT + 10), (6, CT - 150)), L((110, CT + 10), (116, CT - 150)))


@_g("quoteleft", 0x2018)
def quoteleft():
    return strokes(_flick(0, CT - 120, True))


@_g("quoteright", 0x2019)
def quoteright():
    return strokes(_flick(0, CT - 110, False))


@_g("quotedblleft", 0x201C)
def quotedblleft():
    return strokes(_flick(0, CT - 120, True), _flick(105, CT - 120, True))


@_g("quotedblright", 0x201D)
def quotedblright():
    return strokes(_flick(0, CT - 110, False), _flick(105, CT - 110, False))


@_g("quotesinglbase", 0x201A)
def quotesinglbase():
    return strokes(_flick(0, -60, False))


@_g("quotedblbase", 0x201E)
def quotedblbase():
    return strokes(_flick(0, -60, False), _flick(105, -60, False))


def _chevron(x, left=True, w=110, h=140, y=MATH):
    if left:
        return L((x + w, y + h), (x, y), (x + w, y - h))
    return L((x, y + h), (x + w, y), (x, y - h))


@_g("guillemetleft", 0xAB, left=26, right=30)
def guillemetleft():
    return strokes(_chevron(0, True), _chevron(120, True))


@_g("guillemetright", 0xBB, left=30, right=26)
def guillemetright():
    return strokes(_chevron(0, False), _chevron(120, False))


@_g("guilsinglleft", 0x2039, left=26, right=30)
def guilsinglleft():
    return strokes(_chevron(0, True))


@_g("guilsinglright", 0x203A, left=30, right=26)
def guilsinglright():
    return strokes(_chevron(0, False))


# dashes


@_g("hyphen", 0x2D, left=30, right=30)
def hyphen():
    return strokes(L((0, MATH - 6), (190, MATH + 6)))


@_g("endash", 0x2013, left=20, right=20)
def endash():
    return strokes(L((0, MATH - 6), (380, MATH + 6)))


@_g("emdash", 0x2014, left=20, right=20)
def emdash():
    return strokes(L((0, MATH - 8), (780, MATH + 6)))


@_g("underscore", 0x5F, left=10, right=10)
def underscore():
    return strokes(L((0, -110), (420, -104)))


# brackets


@_g("parenleft", 0x28, left=44, right=14)
def parenleft():
    return strokes(Path(150, AT + 10).c((40, 620), (0, 420), (0, 280)).c((0, 120), (40, -40), (150, DB + 20)))


@_g("parenright", 0x29, left=14, right=44)
def parenright():
    return strokes(Path(0, AT + 10).c((110, 620), (150, 420), (150, 280)).c((150, 120), (110, -40), (0, DB + 20)))


@_g("bracketleft", 0x5B, left=50, right=14)
def bracketleft():
    return strokes(L((140, AT + 10), (0, AT + 6), (4, DB + 20), (140, DB + 18)))


@_g("bracketright", 0x5D, left=14, right=50)
def bracketright():
    return strokes(L((0, AT + 6), (140, AT + 10), (136, DB + 18), (0, DB + 20)))


@_g("braceleft", 0x7B, left=40, right=14)
def braceleft():
    return strokes(
        Path(170, AT + 10).c((80, AT), (70, 640), (70, 560)).c((70, 420), (60, 300), (0, 285)),
        Path(0, 285).c((60, 270), (70, 150), (70, 20)).c((70, -80), (80, DB + 30), (170, DB + 20)),
    )


@_g("braceright", 0x7D, left=14, right=40)
def braceright():
    return moved(braceleft(), lambda p: np.array([170, 0]) + p * [-1, 1])


@_g("slash", 0x2F, left=10, right=10)
def slash():
    return strokes(L((0, DB + 30), (300, AT)))


@_g("backslash", 0x5C, left=10, right=10)
def backslash():
    return strokes(L((0, AT), (300, DB + 30)))


@_g("bar", 0x7C, left=60, right=60)
def bar():
    return strokes(L((0, AT + 20), (4, DB)))


@_g("brokenbar", 0xA6, left=60, right=60)
def brokenbar():
    return strokes(L((0, AT + 20), (2, 360)), L((2, 200), (4, DB)))


# operators


@_g("plus", 0x2B, left=36, right=36)
def plus():
    return strokes(L((0, MATH), (400, MATH + 8)), L((198, MATH + 200), (202, MATH - 196)))


@_g("minus", 0x2212, left=36, right=36)
def minus():
    return strokes(L((0, MATH), (400, MATH + 8)))


@_g("equal", 0x3D, left=36, right=36)
def equal():
    return strokes(L((0, MATH + 92), (400, MATH + 100)), L((4, MATH - 96), (400, MATH - 88)))


@_g("multiply", 0xD7, left=40, right=40)
def multiply():
    return strokes(L((0, MATH + 170), (330, MATH - 160)), L((330, MATH + 170), (4, MATH - 164)))


@_g("divide", 0xF7, left=36, right=36)
def divide():
    return strokes(L((0, MATH), (400, MATH + 8)), dot(200, MATH + 180, 7), dot(200, MATH - 172, 7))


@_g("plusminus", 0xB1, left=36, right=36)
def plusminus():
    return strokes(L((0, MATH + 80), (400, MATH + 88)), L((198, MATH + 270), (202, MATH - 100)),
                   L((0, MATH - 200), (400, MATH - 192)))


@_g("less", 0x3C, left=36, right=36)
def less():
    return strokes(L((360, MATH + 210), (0, MATH), (360, MATH - 210)))


@_g("greater", 0x3E, left=36, right=36)
def greater():
    return strokes(L((0, MATH + 210), (360, MATH), (0, MATH - 210)))


@_g("asciicircum", 0x5E, left=30, right=30)
def asciicircum():
    return strokes(L((0, 440), (130, CT + 10), (260, 440)))


@_g("asciitilde", 0x7E, left=30, right=30)
def asciitilde():
    return strokes(S((0, MATH - 20), (70, MATH + 55), (160, MATH - 15), (250, MATH - 55), (320, MATH + 30)))


@_g("asterisk", 0x2A, left=30, right=30)
def asterisk():
    cx, cy, r = 130, CT - 140, 130
    lines = []
    for a in (90, 210, 330):
        t = np.radians(a)
        lines.append(L((cx, cy), (cx + r * np.cos(t), cy + r * np.sin(t))))
    for a in (30, 150, 270):
        t = np.radians(a)
        lines.append(L((cx, cy), (cx + r * 0.8 * np.cos(t), cy + r * 0.8 * np.sin(t))))
    return strokes(lines)


@_g("numbersign", 0x23, left=24, right=24)
def numbersign():
    return strokes(
        L((120, CT), (80, B)), L((280, CT), (240, B)),
        L((0, 460), (380, 470)), L((-10, 230), (360, 238)),
    )


@_g("percent", 0x25, left=24, right=24)
def percent():
    return strokes(
        loop(0, 420, 150, CTOP, overlap=0.2), loop(250, BOT, 400, 290, overlap=0.2),
        L((340, CT + 6), (60, B - 10)),
    )


@_g("perthousand", 0x2030, left=24, right=24)
def perthousand():
    return strokes(percent(), loop(430, BOT, 580, 290, overlap=0.2))


@_g("ampersand", 0x26, left=30, right=20)
def ampersand():
    return strokes(
        S((350, B + 4), (150, 330), (72, 480), (92, 615), (175, CTOP), (252, 615), (240, 518), (140, 420),
          (38, 292), (34, 140), (120, BOT), (244, 60), (344, 250))
    )


@_g("at", 0x40, left=36, right=36)
def at():
    return strokes(
        Path(420, 380).c((410, 450), (360, 480), (310, 480)).c((230, 480), (190, 410), (190, 330))
        .c((190, 250), (240, 210), (300, 210)).c((360, 210), (410, 260), (420, 330)),
        Path(420, 470).l((420, 260)).c((420, 200), (450, 180), (490, 190)).c((560, 210), (590, 300), (590, 380))
        .c((590, 560), (470, CTOP), (330, CTOP)).c((140, CTOP), (0, 540), (0, 330)).c((0, 110), (150, -40), (330, -40))
        .c((410, -40), (470, -20), (520, 10)),
    )


@_g("dollar", 0x24, left=30, right=30)
def dollar():
    return strokes(
        Path(300, 560).c((276, 620), (220, 650), (160, 650)).c((90, 650), (30, 610), (30, 530))
        .c((30, 440), (110, 410), (170, 390)).c((260, 360), (318, 320), (318, 230))
        .c((318, 130), (250, 70), (160, 70)).c((90, 70), (30, 100), (0, 160)),
        L((168, CT + 60), (160, B - 50)),
    )


@_g("cent", 0xA2, left=30, right=30)
def cent():
    return strokes(
        Path(280, 470).c((250, 520), (210, 540), (160, 540)).c((70, 540), (10, 460), (10, 320))
        .c((10, 180), (70, 100), (160, 100)).c((220, 100), (260, 130), (285, 170)),
        L((170, 640), (160, 0)),
    )


@_g("sterling", 0xA3, left=30, right=30)
def sterling():
    return strokes(
        Path(320, 580).c((300, 640), (250, CTOP), (190, CTOP)).c((110, CTOP), (70, 610), (70, 520))
        .c((70, 400), (100, 250), (80, 150)).c((70, 90), (40, 60), (0, B)).l((330, B + 6)),
        L((0, 370), (230, 378)),
    )


@_g("yen", 0xA5, left=20, right=20)
def yen():
    return strokes(
        L((0, CT), (180, 350)), L((360, CT), (180, 350), (180, B)),
        L((40, 300), (320, 306)), L((40, 170), (320, 176)),
    )


@_g("Euro", 0x20AC, left=24, right=30)
def Euro():
    return strokes(
        Path(390, 560).c((360, 640), (300, CTOP), (230, CTOP)).c((110, CTOP), (50, 520), (50, 345))
        .c((50, 150), (110, BOT), (235, BOT)).c((310, BOT), (360, 60), (395, 120)),
        L((0, 420), (270, 426)), L((0, 270), (250, 276)),
    )


@_g("ruble", 0x20BD, left=24, right=30)
def ruble():
    return strokes(
        L((60, CT), (60, B)),
        Path(60, CT).l((190, CT)).c((290, CT), (340, 600), (340, 505)).c((340, 405), (280, 350), (190, 350)).l((0, 350)),
        L((0, 210), (240, 216)),
    )


@_g("won", 0x20A9, left=14, right=14)
def won():
    return strokes(
        L((0, CT), (130, B), (270, 540), (410, B), (540, CT)),
        L((0, 420), (540, 428)), L((20, 270), (520, 278)),
    )


@_g("currency", 0xA4, left=30, right=30)
def currency():
    return strokes(
        loop(60, 170, 300, 410, overlap=0.2),
        L((0, 110), (70, 180)), L((360, 110), (290, 180)), L((0, 470), (70, 400)), L((360, 470), (290, 400)),
    )


@_g("numero", 0x2116, left=40, right=30)
def numero():
    return strokes(
        L((0, B), (0, CT), (330, B), (330, CT)),
        loop(420, 330, 580, 560, overlap=0.2),
        L((410, 200), (590, 206)),
    )


@_g("section", 0xA7, left=30, right=30)
def section():
    return strokes(
        Path(290, 600).c((270, 650), (220, CTOP), (160, CTOP)).c((90, CTOP), (40, 640), (40, 580))
        .c((40, 500), (140, 470), (200, 440)).c((280, 400), (300, 350), (300, 300))
        .c((300, 230), (240, 200), (180, 200)),
        Path(120, 480).c((60, 470), (20, 420), (20, 370)).c((20, 300), (100, 270), (160, 240))
        .c((240, 200), (280, 160), (280, 100)).c((280, 40), (220, -20), (150, -20))
        .c((90, -20), (40, 10), (20, 60)),
    )


@_g("paragraph", 0xB6, left=30, right=40)
def paragraph():
    return strokes(
        Path(200, CT).l((120, CT)).c((50, CT), (0, 600), (0, 520)).c((0, 440), (50, 380), (120, 380)).l((200, 380)),
        L((200, CT + 4), (200, DB + 30)), L((300, CT + 4), (300, DB + 30)), L((200, CT + 2), (320, CT + 4)),
    )


@_g("degree", 0xB0, left=30, right=30)
def degree():
    return strokes(loop(0, 470, 190, CTOP, overlap=0.25))


@_g("dagger", 0x2020, left=30, right=30)
def dagger():
    return strokes(L((150, CT + 20), (150, DB + 20)), L((0, 480), (300, 488)))


@_g("daggerdbl", 0x2021, left=30, right=30)
def daggerdbl():
    return strokes(L((150, CT + 20), (150, DB + 20)), L((0, 500), (300, 508)), L((0, 120), (300, 128)))


def _circled(inner):
    ring = loop(0, -20, 720, CTOP + 20, k=0.56, overlap=0.15)
    return strokes(ring, inner)


@_g("copyright", 0xA9, left=36, right=36)
def copyright():
    c = (
        Path(480, 480).c((460, 520), (420, 540), (370, 540)).c((290, 540), (230, 470), (230, 330))
        .c((230, 190), (290, 120), (370, 120)).c((420, 120), (460, 140), (485, 180))
    )
    return _circled(c)


@_g("registered", 0xAE, left=36, right=36)
def registered():
    r = [
        L((260, 540), (260, 130)),
        Path(260, 540).l((370, 540)).c((440, 540), (480, 500), (480, 440)).c((480, 380), (440, 340), (370, 340)).l((260, 340)),
        L((370, 340), (480, 130)),
    ]
    return _circled(r)


@_g("trademark", 0x2122, left=30, right=30)
def trademark():
    return light(
        [L((0, CT), (240, CT + 4)), L((120, CT), (120, 380)),
         L((300, 380), (310, CT), (420, 470), (530, CT), (540, 380))],
        0.72,
    )


@_g("ordfeminine", 0xAA, left=30, right=30)
def ordfeminine():
    return light(moved(strokes(
        Path(300, 400).c((290, 480), (230, TOP), (160, TOP)).c((60, TOP), (0, 420), (0, 270))
        .c((0, 110), (65, BOT), (150, BOT)).c((225, BOT), (285, 70), (300, 160)),
        L((300, XT), (300, B))), scale_about(0.55, 0.55)), 0.75) + light(
        moved(strokes(L((0, -120), (300, -114))), lambda p: p * 0.55 + [0, 370]), 0.7)


@_g("ordmasculine", 0xBA, left=30, right=30)
def ordmasculine():
    return light(moved(strokes(loop(0, BOT, 320, TOP, overlap=0.2), L((0, -120), (320, -114))),
                       lambda p: p * 0.55 + [0, 370]), 0.75)


def _sup(fn):
    return lambda: light(moved(fn(), lambda p: p * 0.56 + [0, 330]), 0.72)


_g("onesuperior", 0xB9, left=24, right=24)(_sup(one))
_g("twosuperior", 0xB2, left=24, right=24)(_sup(two))
_g("threesuperior", 0xB3, left=24, right=24)(_sup(three))


def _frac(num, den):
    def draw():
        n = light(moved(num(), lambda p: p * 0.5 + [0, 340]), 0.7)
        d = light(moved(den(), lambda p: p * 0.5 + [300, 0]), 0.7)
        return n + d + light(strokes(L((40, 20), (440, CT))), 0.8)

    return draw


_g("onehalf", 0xBD, left=30, right=30)(_frac(one, two))
_g("onequarter", 0xBC, left=30, right=30)(_frac(one, four))
_g("threequarters", 0xBE, left=30, right=30)(_frac(three, four))


@_g("fraction", 0x2044, left=-40, right=-40)
def fraction():
    return strokes(L((0, -20), (360, CT + 20)))


@_g("logicalnot", 0xAC, left=36, right=36)
def logicalnot():
    return strokes(L((0, MATH + 60), (300, MATH + 66), (298, MATH - 90)))


@_g("mu", 0xB5, left="stem", right="stem")
def mu():
    return strokes(
        Path(0, XT).l((0, 190)).c((0, 80), (55, BOT), (148, BOT)).c((238, BOT), (296, 80), (300, 200)),
        L((300, XT), (300, B)), L((0, 200), (0, DB)),
    )


# arrows


def _arrow(angle):
    head = [L((330, 140 + MATH), (500, MATH), (330, -140 + MATH))]
    shaft = L((0, MATH), (490, MATH + 8))
    t = np.radians(angle)
    c, s = np.cos(t), np.sin(t)
    rot = np.array([[c, -s], [s, c]])
    ctr = np.array([250, MATH])
    return moved([shaft] + head, lambda p: (p - ctr) @ rot.T + ctr)


@_g("arrowright", 0x2192, left=30, right=30)
def arrowright():
    return _arrow(0)


@_g("arrowleft", 0x2190, left=30, right=30)
def arrowleft():
    return _arrow(180)


@_g("arrowup", 0x2191, left=30, right=30)
def arrowup():
    return _arrow(90)


@_g("arrowdown", 0x2193, left=30, right=30)
def arrowdown():
    return _arrow(-90)


# hearts, stars, marks


def _heart_outline():
    return (
        Path(205, 452)
        .c((184, 530), (136, 586), (82, 584))
        .c((26, 582), (0, 522), (0, 452))
        .c((0, 330), (102, 222), (205, 52))
        .c((308, 222), (410, 330), (410, 452))
        .c((410, 522), (384, 582), (328, 584))
        .c((274, 586), (226, 530), (205, 452))
        .pts
    )


@_g("heart", 0x2665, left=36, right=36)
def heart():
    return strokes(filled(_heart_outline()), _heart_outline())


@_g("heartwhite", 0x2661, left=36, right=36)
def heartwhite():
    return strokes(_heart_outline())


def _star(r_out=240, r_in=100, cx=240, cy=330):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = np.radians(90 + 36 * i)
        pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    pts.append(pts[0])
    return pts


@_g("star", 0x2605, left=24, right=24)
def star():
    p = _star()
    return strokes(filled(np.array(p)), L(*p))


@_g("starwhite", 0x2606, left=24, right=24)
def starwhite():
    return strokes(L(*_star()))


@_g("sparkle", 0x2726, left=24, right=24)
def sparkle():
    cx, cy = 220, 330
    pts = [(cx, cy + 250), (cx + 50, cy + 50), (cx + 220, cy), (cx + 50, cy - 50),
           (cx, cy - 250), (cx - 50, cy - 50), (cx - 220, cy), (cx - 50, cy + 50), (cx, cy + 250)]
    return strokes(filled(np.array(pts)), L(*pts))


@_g("checkmark", 0x2713, left=30, right=30)
def checkmark():
    return strokes(Path(0, 330).l((140, 120)).c((200, 280), (300, 500), (420, CT)))


@_g("ballotx", 0x2717, left=30, right=30)
def ballotx():
    return strokes(L((20, 560), (380, 60)), L((360, 600), (0, 40)))


@_g("referencemark", 0x203B, left=40, right=40)
def referencemark():
    return strokes(
        L((20, 550), (380, 110)), L((380, 550), (20, 110)),
        dot(200, 560, 6), dot(200, 100, 6), dot(10, 330, 6), dot(390, 330, 6),
    )


# CJK punctuation used in Korean text


@_g("cornerbracketleft", 0x300C, left=160, right=60)
def cornerbracketleft():
    return strokes(L((150, AT), (0, AT - 6), (4, 250)))


@_g("cornerbracketright", 0x300D, left=60, right=160)
def cornerbracketright():
    return strokes(L((146, 380), (150, DB + 30), (0, DB + 36)))


@_g("whitecornerbracketleft", 0x300E, left=140, right=50)
def whitecornerbracketleft():
    return strokes(L((190, AT), (0, AT - 6), (4, 200)), L((190, AT - 100), (100, AT - 104), (102, 250)))


@_g("whitecornerbracketright", 0x300F, left=50, right=140)
def whitecornerbracketright():
    return strokes(L((188, 400), (190, DB + 30), (0, DB + 36)), L((90, 350), (90, DB + 130), (0, DB + 134)))


@_g("anglebracketleft", 0x3008, left=150, right=60)
def anglebracketleft():
    return strokes(L((150, AT), (0, 280), (150, DB + 40)))


@_g("anglebracketright", 0x3009, left=60, right=150)
def anglebracketright():
    return strokes(L((0, AT), (150, 280), (0, DB + 40)))


@_g("dblanglebracketleft", 0x300A, left=120, right=50)
def dblanglebracketleft():
    return strokes(L((150, AT), (0, 280), (150, DB + 40)), L((260, AT), (110, 280), (260, DB + 40)))


@_g("dblanglebracketright", 0x300B, left=50, right=120)
def dblanglebracketright():
    return strokes(L((0, AT), (150, 280), (0, DB + 40)), L((110, AT), (260, 280), (110, DB + 40)))


@_g("ideographiccomma", 0x3001, left=60, right=300)
def ideographiccomma():
    return strokes(L((0, 150), (90, 40)))


@_g("ideographicfullstop", 0x3002, left=60, right=300)
def ideographicfullstop():
    return strokes(loop(0, B - 10, 120, 150, overlap=0.25))


@_g("fullwidthtilde", 0xFF5E, left=100, right=100)
def fullwidthtilde():
    return strokes(S((0, MATH - 30), (130, MATH + 70), (330, MATH - 40), (500, MATH - 70), (640, MATH + 40)))


@_g("fullwidthexclam", 0xFF01, left=300, right=300)
def fullwidthexclam():
    return exclam()


@_g("fullwidthquestion", 0xFF1F, left=240, right=240)
def fullwidthquestion():
    return question()


@_g("middledotkatakana", 0x30FB, left=300, right=300)
def middledotkatakana():
    return strokes(dot(0, MATH, 8))


@_g("waveDash", 0x301C, left=100, right=100)
def waveDash():
    return fullwidthtilde()
