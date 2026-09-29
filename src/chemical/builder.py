"""Assemble inked glyphs into OpenType fonts (CFF .otf, TrueType .ttf, .woff2)."""

import multiprocessing as mp
import os
import time
from dataclasses import dataclass

from fontTools.cu2qu import curve_to_quadratic
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from . import metrics
from .registry import REGISTRY, side_value

FAMILY = "chemical"
VERSION = "0.1"


@dataclass(frozen=True)
class Job:
    out: str  # glyph name in the font
    src: str  # registry name whose skeleton is drawn
    variant: int
    nib: str


def _work(job):
    from . import glyphset  # noqa: F401 - fills the registry in worker processes
    from .ink import draw_glyph

    contours, bounds = draw_glyph(job.src, job.variant, nib_name=job.nib, seed_name=job.out)
    return job, contours, bounds


def plan(filter_fn=None):
    """Every glyph the font will contain, in order."""
    from . import glyphset  # noqa: F401
    from .ink import variant_name

    jobs = []
    for name, gd in REGISTRY.items():
        if filter_fn and not filter_fn(gd):
            continue
        for v in range(max(1, gd.variants)):
            jobs.append(Job(variant_name(name, v), name, v, gd.nib))
    from .features import extra_jobs

    jobs += extra_jobs(jobs, filter_fn)
    return jobs


def render(jobs, processes=None):
    processes = processes or max(1, (os.cpu_count() or 2) - 1)
    t = time.time()
    if processes == 1 or len(jobs) < 40:
        results = [_work(j) for j in jobs]
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes) as pool:
            results = pool.map(_work, jobs, chunksize=max(1, len(jobs) // (processes * 8)))
    print(f"  inked {len(jobs)} glyphs in {time.time() - t:.1f}s")
    return results


def _r(p, dx):
    return (int(round(p[0] + dx)), int(round(p[1])))


def _draw(pen, contours, dx, quadratic):
    for c in contours:
        pen.moveTo(_r(c[0][1], dx))
        for seg in c:
            if seg[0] == "line":
                pen.lineTo(_r(seg[2], dx))
            elif quadratic:
                q = curve_to_quadratic([tuple(p) for p in seg[1:]], 1.0)
                pen.qCurveTo(*[_r(p, dx) for p in q[1:]])
            else:
                pen.curveTo(_r(seg[2], dx), _r(seg[3], dx), _r(seg[4], dx))
        pen.closePath()


def layout(results):
    """Place ink inside advance widths: name -> (contours, dx, advance)."""
    placed = {}
    for job, contours, (x0, y0, x1, y1) in results:
        gd = REGISTRY[job.src]
        if not contours:
            placed[job.out] = (contours, 0.0, gd.advance or 0)
            continue
        if gd.advance is not None:
            adv = gd.advance
            dx = (adv - (x1 - x0)) / 2 - x0 if gd.center else 0.0
        else:
            lsb, rsb = side_value(gd.left), side_value(gd.right)
            adv = (x1 - x0) + lsb + rsb
            dx = lsb - x0
        placed[job.out] = (contours, dx, int(round(adv)))
    return placed


def _notdef(pen):
    pen.moveTo((60, 0))
    pen.lineTo((60, 700))
    pen.lineTo((440, 700))
    pen.lineTo((440, 0))
    pen.closePath()
    pen.moveTo((120, 60))
    pen.lineTo((380, 60))
    pen.lineTo((380, 640))
    pen.lineTo((120, 640))
    pen.closePath()


def assemble(placed, order, cmap, fea, path, fmt="ttf"):
    tt = fmt == "ttf"
    fb = FontBuilder(metrics.UPM, isTTF=tt)
    glyph_order = [".notdef"] + [g for g in order if g != ".notdef"]
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    advances = {}
    if tt:
        glyphs = {}
        for g in glyph_order:
            pen = TTGlyphPen(None)
            if g == ".notdef":
                _notdef(ReverseContourPen(pen))
                advances[g] = 500
            else:
                contours, dx, adv = placed[g]
                _draw(ReverseContourPen(pen), contours, dx, quadratic=True)
                advances[g] = adv
            glyphs[g] = pen.glyph()
        fb.setupGlyf(glyphs)
        glyf = fb.font["glyf"]
        hmtx = {}
        for g in glyph_order:
            gl = glyf[g]
            gl.recalcBounds(glyf)
            hmtx[g] = (advances[g], getattr(gl, "xMin", 0) if gl.numberOfContours else 0)
    else:
        charstrings = {}
        hmtx = {}
        for g in glyph_order:
            if g == ".notdef":
                adv = 500
                pen = T2CharStringPen(adv, None)
                _notdef(pen)
            else:
                contours, dx, adv = placed[g]
                pen = T2CharStringPen(adv, None)
                _draw(pen, contours, dx, quadratic=False)
            charstrings[g] = pen.getCharString()
            hmtx[g] = (adv, 0)
        fb.setupCFF(
            f"{FAMILY}-Regular",
            {"FullName": f"{FAMILY} Regular", "FamilyName": FAMILY, "Weight": "Regular"},
            charstrings,
            {},
        )
        cff = fb.font["CFF "].cff
        cs = cff[cff.fontNames[0]].CharStrings
        for g in glyph_order:
            b = cs[g].calcBounds(cs)
            hmtx[g] = (hmtx[g][0], b[0] if b else 0)

    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=metrics.ASCENDER, descent=metrics.DESCENDER, lineGap=metrics.LINE_GAP)
    fb.setupNameTable(
        {
            "copyright": "Copyright 2026 chemical pink",
            "familyName": FAMILY,
            "styleName": "Regular",
            "uniqueFontIdentifier": f"{VERSION};CHEM;{FAMILY}-Regular",
            "fullName": f"{FAMILY} Regular",
            "version": f"Version {VERSION}",
            "psName": f"{FAMILY}-Regular",
            "manufacturer": "chemical pink",
            "designer": "chemical pink",
            "description": "A hand-drawn marker typeface for Latin, Cyrillic and Hangul.",
        }
    )
    ymax = max([0] + [max(p[1] for s in c for p in s[1:]) for g in placed for c in placed[g][0]])
    ymin = min([0] + [min(p[1] for s in c for p in s[1:]) for g in placed for c in placed[g][0]])
    fb.setupOS2(
        sTypoAscender=metrics.ASCENDER,
        sTypoDescender=metrics.DESCENDER,
        sTypoLineGap=metrics.LINE_GAP,
        usWinAscent=int(max(metrics.ASCENDER, ymax + 10)),
        usWinDescent=int(max(-metrics.DESCENDER, -ymin + 10)),
        sxHeight=metrics.XH,
        sCapHeight=metrics.CAP,
        achVendID="CHEM",
        fsType=0,
        fsSelection=0x40 | 0x80,
        usWeightClass=400,
        usWidthClass=5,
        version=4,
    )
    fb.setupPost(keepGlyphNames=tt)
    if fea:
        fb.addOpenTypeFeatures(fea)
    font = fb.font
    font["OS/2"].recalcUnicodeRanges(font)
    font["OS/2"].recalcCodePageRanges(font)
    font["head"].fontRevision = float(VERSION)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    font.save(path)
    return path


def woff2(src, dst):
    f = TTFont(src)
    f.flavor = "woff2"
    f.save(dst)
    return dst
