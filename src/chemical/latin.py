"""Latin letters.

Lowercase is tall (x-height 550 against capitals at 700), so mixed-case
setting like "JAne" sits naturally. Bowls are drawn slightly square, the way
a quick marker hand flattens its curves.
"""

from .metrics import AT, B, CT, DB, OS, XT
from .registry import glyph
from .skel import L, Path, dot, loop, strokes

TOP = XT + OS  # top of a lowercase bowl
BOT = B - OS  # bottom of any bowl
CTOP = CT + OS  # top of a capital bowl


# -- shared parts -------------------------------------------------------------


def arch(x0, x1, top=XT + 2, start=350, down=B):
    """The shoulder of n, h, m: leaves the stem low, turns, runs down."""
    w = x1 - x0
    return (
        Path(x0 + 8, start)
        .c((x0 + 0.07 * w, top - 60), (x0 + 0.3 * w, top), (x0 + 0.56 * w, top))
        .c((x0 + 0.88 * w, top), (x1, top - 60), (x1, top - 160))
        .l((x1, down))
    )


def bowl_left(x1=300, top=TOP, bot=BOT, lift=400, drop=160):
    """Bowl hanging on a right-hand stem (a, d, g, q)."""
    return (
        Path(x1, lift)
        .c((x1 - 10, top - 45), (x1 - 70, top), (x1 - 140, top))
        .c((x1 - 240, top), (x1 - 300, top - 110), (x1 - 300, (top + bot) / 2))
        .c((x1 - 300, bot + 90), (x1 - 235, bot), (x1 - 150, bot))
        .c((x1 - 75, bot), (x1 - 15, bot + 50), (x1, drop))
    )


def bowl_right(x0=0, w=310, top=TOP, bot=BOT, lift=400, drop=160):
    """Bowl hanging on a left-hand stem (b, p)."""
    return (
        Path(x0, drop)
        .c((x0 + 12, bot + 50), (x0 + 75, bot), (x0 + 155, bot))
        .c((x0 + 260, bot), (x0 + w, bot + 100), (x0 + w, (top + bot) / 2))
        .c((x0 + w, top - 100), (x0 + 255, top), (x0 + 165, top))
        .c((x0 + 90, top), (x0 + 25, top - 45), (x0, lift))
    )


def c_curve(x1=292, top=TOP, bot=BOT, w=300, open_top=430, open_bot=108):
    x0 = x1 - w
    return (
        Path(x1, open_top)
        .c((x1 - 30, top - 30), (x1 - 77, top), (x0 + 160, top))
        .c((x0 + 58, top), (x0, top - 110), (x0, (top + bot) / 2))
        .c((x0, bot + 100), (x0 + 62, bot), (x0 + 162, bot))
        .c((x0 + 222, bot), (x1 - 24, bot + 32), (x1 + 4, open_bot))
    )


# -- lowercase ------------------------------------------------------------------


@glyph("a", 0x61, "round", "stem")
def a():
    return strokes(bowl_left(), L((300, XT), (300, B)))


@glyph("b", 0x62, "stem", "round")
def b():
    return strokes(L((0, AT), (0, B)), bowl_right())


@glyph("c", 0x63, "round", "open")
def c():
    return strokes(c_curve())


@glyph("d", 0x64, "round", "stem")
def d():
    return strokes(bowl_left(), L((300, AT), (300, B)))


@glyph("e", 0x65, "round", "open")
def e():
    # one movement: out along the bar, up and round the bowl
    return strokes(
        Path(14, 268)
        .l((258, 294))
        .c((290, 298), (300, 330), (300, 372))
        .c((300, 470), (238, TOP), (156, TOP))
        .c((58, TOP), (0, 420), (0, 275))
        .c((0, 120), (62, BOT), (162, BOT))
        .c((222, BOT), (268, 52), (296, 106))
    )


@glyph("f", 0x66, "arm", "arm")
def f():
    return strokes(
        Path(92, B).l((92, 560)).c((92, 680), (140, AT), (206, AT)).c((244, AT), (270, 726), (286, 708)),
        L((0, XT - 8), (242, XT + 4)),
    )


@glyph("g", 0x67, "round", "stem")
def g():
    return strokes(
        bowl_left(),
        Path(300, XT).l((300, 10)).c((300, -120), (235, DB), (145, DB)).c((75, DB), (25, -160), (5, -115)),
    )


@glyph("h", 0x68, "stem", "stem")
def h():
    return strokes(L((0, AT), (0, B)), arch(0, 300))


@glyph("i", 0x69, "stem", "stem")
def i():
    return strokes(L((0, XT), (0, B)), dot(0, 700, 5))


@glyph("j", 0x6A, "arm", "stem")
def j():
    return strokes(
        Path(0, XT).l((0, -70)).c((0, -150), (-45, DB), (-110, DB)).c((-140, DB), (-160, -176), (-175, -162)),
        dot(0, 700, 5),
    )


@glyph("k", 0x6B, "stem", "diag")
def k():
    return strokes(L((0, AT), (0, B)), L((275, XT), (18, 235)), L((105, 300), (295, B)))


@glyph("l", 0x6C, "stem", "tail")
def l():
    return strokes(Path(0, AT).l((0, 130)).c((0, 60), (38, BOT), (92, BOT)).c((115, BOT), (130, 28), (142, 42)))


@glyph("m", 0x6D, "stem", "stem")
def m():
    return strokes(L((0, XT + 4), (0, B)), arch(0, 240), arch(240, 480))


@glyph("n", 0x6E, "stem", "stem")
def n():
    return strokes(L((0, XT + 4), (0, B)), arch(0, 300))


@glyph("o", 0x6F, "round", "round")
def o():
    return strokes(loop(0, BOT, 320, TOP, k=0.62, start=0, overlap=0.2))


@glyph("p", 0x70, "stem", "round")
def p():
    return strokes(L((0, XT + 4), (0, DB)), bowl_right())


@glyph("q", 0x71, "round", "stem")
def q():
    return strokes(bowl_left(), L((300, XT + 4), (300, DB)))


@glyph("r", 0x72, "stem", "arm")
def r():
    return strokes(
        L((0, XT + 4), (0, B)),
        Path(0, 340).c((22, 450), (85, TOP), (160, TOP)).c((195, TOP), (220, 520), (238, 505)),
    )


@glyph("s", 0x73, "open", "open")
def s():
    return strokes(
        Path(270, 445)
        .c((245, 500), (198, TOP), (145, TOP))
        .c((68, TOP), (18, 478), (18, 408))
        .c((18, 330), (98, 306), (158, 288))
        .c((238, 262), (292, 222), (292, 150))
        .c((292, 68), (228, BOT), (148, BOT))
        .c((78, BOT), (24, 48), (4, 108))
    )


@glyph("t", 0x74, "arm", "open")
def t():
    return strokes(
        Path(110, 686).l((110, 135)).c((110, 60), (150, BOT), (208, BOT)).c((236, BOT), (256, 30), (270, 45)),
        L((8, XT - 8), (250, XT + 4)),
    )


@glyph("u", 0x75, "stem", "stem")
def u():
    return strokes(
        Path(0, XT).l((0, 190)).c((0, 80), (55, BOT), (148, BOT)).c((238, BOT), (296, 80), (300, 200)),
        L((300, XT), (300, B)),
    )


@glyph("v", 0x76, "diag", "diag")
def v():
    return strokes(L((0, XT), (160, B), (320, XT)))


@glyph("w", 0x77, "diag", "diag")
def w():
    return strokes(L((0, XT), (118, B), (240, 430), (362, B), (480, XT)))


@glyph("x", 0x78, "diag", "diag")
def x():
    return strokes(L((0, XT), (300, B)), L((292, XT), (8, B)))


@glyph("y", 0x79, "diag", "diag")
def y():
    return strokes(L((0, XT), (160, 60)), L((318, XT), (72, DB)))


@glyph("z", 0x7A, "open", "open")
def z():
    return strokes(L((12, XT), (290, XT), (2, B), (302, B)))


# -- capitals -------------------------------------------------------------------


@glyph("A", 0x41, "Diag", "Diag")
def A():
    return strokes(L((0, B), (182, CT + 6), (364, B)), L((72, 250), (296, 250)))


@glyph("B", 0x42, "Stem", "Round")
def B_():
    return strokes(
        L((0, CT), (0, B)),
        Path(0, CT).l((140, CT)).c((225, CT), (268, 612), (268, 535)).c((268, 452), (212, 392), (135, 392)).l((0, 392)),
        Path(0, 392).l((155, 392)).c((248, 392), (298, 330), (298, 222)).c((298, 104), (236, B), (145, B)).l((0, B)),
    )


@glyph("C", 0x43, "Round", "Open")
def C():
    return strokes(c_curve(x1=390, top=CTOP, w=392, open_top=575, open_bot=125))


@glyph("D", 0x44, "Stem", "Round")
def D():
    return strokes(
        L((0, CT), (0, B)),
        Path(0, CT).l((120, CT)).c((290, CT), (372, 530), (372, 348)).c((372, 150), (285, B), (120, B)).l((0, B)),
    )


@glyph("E", 0x45, "Stem", "Open")
def E():
    return strokes(L((0, CT), (0, B)), L((0, CT), (285, CT)), L((0, 362), (245, 362)), L((0, B), (295, B)))


@glyph("F", 0x46, "Stem", "Open")
def F():
    return strokes(L((0, CT), (0, B)), L((0, CT), (285, CT)), L((0, 350), (240, 350)))


@glyph("G", 0x47, "Round", "Stem")
def G():
    return strokes(
        Path(388, 575)
        .c((352, 640), (292, CTOP), (218, CTOP))
        .c((88, CTOP), (0, 525), (0, 342))
        .c((0, 150), (88, BOT), (220, BOT))
        .c((320, BOT), (392, 90), (392, 200))
        .l((392, 318)),
        L((228, 318), (402, 318)),
    )


@glyph("H", 0x48, "Stem", "Stem")
def H():
    return strokes(L((0, CT), (0, B)), L((350, CT), (350, B)), L((0, 360), (350, 360)))


@glyph("I", 0x49, "Stem", "Stem")
def I():
    return strokes(L((0, CT), (0, B)))


@glyph("J", 0x4A, "Open", "Stem")
def J():
    return strokes(Path(298, CT).l((298, 210)).c((298, 85), (228, BOT), (148, BOT)).c((68, BOT), (14, 64), (0, 140)))


@glyph("K", 0x4B, "Stem", "Diag")
def K():
    return strokes(L((0, CT), (0, B)), L((332, CT), (12, 282)), L((118, 386), (352, B)))


@glyph("L", 0x4C, "Stem", "Open")
def L_():
    return strokes(L((0, CT), (0, B), (286, B)))


@glyph("M", 0x4D, "Stem", "Stem")
def M():
    return strokes(L((0, B), (16, CT), (228, 250), (440, CT), (456, B)))


@glyph("N", 0x4E, "Stem", "Stem")
def N():
    return strokes(L((0, B), (0, CT), (360, B), (360, CT)))


@glyph("O", 0x4F, "Round", "Round")
def O_():
    return strokes(loop(0, BOT, 412, CTOP, k=0.6, start=0, overlap=0.2))


@glyph("P", 0x50, "Stem", "Round")
def P():
    return strokes(
        L((0, CT), (0, B)),
        Path(0, CT).l((145, CT)).c((255, CT), (312, 600), (312, 505)).c((312, 405), (248, 342), (145, 342)).l((0, 342)),
    )


@glyph("Q", 0x51, "Round", "Round")
def Q():
    return strokes(loop(0, BOT, 412, CTOP, k=0.6, start=0, overlap=0.2), L((236, 150), (418, -40)))


@glyph("R", 0x52, "Stem", "Diag")
def R():
    return strokes(
        L((0, CT), (0, B)),
        Path(0, CT).l((145, CT)).c((255, CT), (312, 600), (312, 505)).c((312, 405), (248, 342), (145, 342)).l((0, 342)),
        L((150, 346), (338, B)),
    )


@glyph("S", 0x53, "Open", "Open")
def S_():
    return strokes(
        Path(352, 572)
        .c((318, 640), (258, CTOP), (188, CTOP))
        .c((90, CTOP), (24, 612), (24, 512))
        .c((24, 410), (110, 380), (190, 356))
        .c((290, 326), (358, 282), (358, 186))
        .c((358, 80), (278, BOT), (178, BOT))
        .c((88, BOT), (28, 42), (0, 112))
    )


@glyph("T", 0x54, "Open", "Open")
def T():
    return strokes(L((0, CT), (380, CT)), L((190, CT), (190, B)))


@glyph("U", 0x55, "Stem", "Stem")
def U():
    return strokes(Path(0, CT).l((0, 235)).c((0, 92), (80, BOT), (184, BOT)).c((290, BOT), (368, 92), (368, 235)).l((368, CT)))


@glyph("V", 0x56, "Diag", "Diag")
def V():
    return strokes(L((0, CT), (188, B), (376, CT)))


@glyph("W", 0x57, "Diag", "Diag")
def W():
    return strokes(L((0, CT), (132, B), (286, 540), (440, B), (572, CT)))


@glyph("X", 0x58, "Diag", "Diag")
def X():
    return strokes(L((0, CT), (360, B)), L((352, CT), (8, B)))


@glyph("Y", 0x59, "Diag", "Diag")
def Y():
    return strokes(L((0, CT), (184, 330)), L((368, CT), (184, 330), (184, B)))


@glyph("Z", 0x5A, "Open", "Open")
def Z():
    return strokes(L((10, CT), (350, CT), (0, B), (362, B)))
