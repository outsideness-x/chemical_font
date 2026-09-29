"""The fineliner: capitals drawn with a thin pen, for ss01.

In the mixed credits look a few letters are written with a thin liner, always
as capitals. A lowercase letter's thin form is its capital, drawn a little
smaller so it still sits with the lowercase around it.
"""

from .marks import gname
from .metrics import B
from .registry import REGISTRY, glyph
from .skel import moved, scale_about

LATIN_UC = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
CYR_UC = [chr(c) for c in range(0x0410, 0x0430)] + ["Ё", "Є", "І", "Ї", "Ґ", "Ў"]


def _name(ch):
    return gname(ord(ch))


def pairs():
    """(thin glyph name, drawing source, lowercase?) for every thin letter."""
    out = []
    for ch in LATIN_UC + CYR_UC:
        src = _name(ch)
        if src not in REGISTRY:
            continue
        out.append((src, src, False))
        lo = ch.lower()
        if lo != ch and _name(lo) in REGISTRY:
            out.append((_name(lo), src, True))
    return out


def register():
    for base, src, small in pairs():
        gd = REGISTRY[src]
        if small:
            draw = (lambda s=src: moved(REGISTRY[s].draw(), scale_about(0.9, 0.9, 0.0, B)))
        else:
            draw = (lambda s=src: REGISTRY[s].draw())
        glyph(f"{base}.thin", None, gd.left, gd.right, variants=1, nib="thin")(draw)
