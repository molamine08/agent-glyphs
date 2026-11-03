#!/usr/bin/env python3
"""Build "Agent Glyphs Riyal": a tiny fallback font that draws only the Saudi Riyal sign (U+20C1).

U+20C1 entered Unicode 17 (Sept 2025); most fonts do not draw it yet. List this font
after your text font and the browser / OS picks the sign from it automatically, so a
price stays one string ("45 \u20C1"), never text + SVG.

    python scripts/make_riyal_font.py            # -> fonts/riyal/

Weights follow a common Arabic UI sans (measured at 1000 UPM):
  digit height ~703-715, alef stem: Regular 66 / Medium 86 / Bold 108,
  line metrics: ascent 1250, descent 600 (so the fallback never grows the line box).
"""
import sys, pathlib
from svgpathtools import parse_path
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampNow

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / "fonts" / "riyal"
OUT.mkdir(parents=True, exist_ok=True)

# Official symbol outline (Saudi Central Bank), 24px box, filled path
D = ("M20.9285 18.3045C20.8106 19.2585 20.7583 19.6724 20.3176 20.6025L13.5507 22C13.7062 20.9948 13.9144 20.2195 14.2513 19.7543L20.9285 18.3045Z"
     "M11.5031 11.7226L13.5245 11.2835V4.89398C14.2777 4.04857 14.7416 3.66999 15.6507 3.1901V10.8221L20.9285 9.6768C20.8106 10.6309 20.7581 11.0449 20.3176 11.9748L15.6507 12.9612V15.106L20.9285 13.9907C20.8106 14.9449 20.7582 15.3586 20.3176 16.2887L15.6507 17.2508V17.2732L13.5245 17.7123V13.4096L11.5031 13.8375V16.5483L11.4675 16.5539C11.0024 17.3697 10.3463 18.3516 9.71323 19.134L3.07147 20.397C3.13103 19.5429 3.25691 19.0622 3.64317 18.2018L9.37694 16.9575V14.2859L4.06166 15.4124C4.12121 14.5579 4.24508 14.0761 4.63149 13.2153L9.37694 12.184V3.70575C10.1302 2.86022 10.5937 2.47999 11.5031 2V11.7226Z")

UPM, ASC, DESC = 1000, 1250, 600
BASE_STEM_24 = 11.5031 - 9.37694          # stroke width in the 24px source
WEIGHTS = {  # name: (usWeightClass, target stem, target height)
    "Regular": (400, 66, 706),
    "Medium": (500, 86, 710),
    "Bold": (700, 108, 714),
}
SIDE = 48  # side bearing, close to UI-font digits


def polygons():
    polys = []
    for sub in parse_path(D).continuous_subpaths():
        pts = []
        for seg in sub:
            n = 1 if seg.__class__.__name__ == "Line" else 12
            for i in range(n):
                p = seg.point(i / n)
                pts.append((p.real, -p.imag))  # flip y (SVG down -> font up)
        polys.append(Polygon(pts).buffer(0))
    return unary_union(polys)


def glyph_for(stem, height):
    g = polygons()
    minx, miny, maxx, maxy = g.bounds
    scale = height / (maxy - miny)
    g = affinity.scale(g, scale, scale, origin=(0, 0))
    base_stem = BASE_STEM_24 * scale
    g = g.buffer((stem - base_stem) / 2, join_style=2, mitre_limit=3)  # thicken/thin, sharp joins
    minx, miny, maxx, maxy = g.bounds
    g = affinity.translate(g, SIDE - minx, -miny)  # sit on baseline
    _, _, maxx, _ = g.bounds
    pen = TTGlyphPen(None)
    geoms = getattr(g, "geoms", [g])
    for poly in geoms:
        rings = [poly.exterior] + list(poly.interiors)
        for i, ring in enumerate(rings):
            coords = list(ring.coords)[:-1]
            # TrueType: outer contours clockwise, holes counter-clockwise
            cw = ring.is_ccw is False
            want_cw = i == 0
            if cw != want_cw:
                coords = coords[::-1]
            pen.moveTo(tuple(round(c) for c in coords[0]))
            for c in coords[1:]:
                pen.lineTo(tuple(round(v) for v in c))
            pen.closePath()
    return pen.glyph(), round(maxx + SIDE)


def notdef():
    pen = TTGlyphPen(None)
    pen.moveTo((60, 0)); pen.lineTo((60, 700)); pen.lineTo((440, 700)); pen.lineTo((440, 0)); pen.closePath()
    pen.moveTo((110, 50)); pen.lineTo((390, 50)); pen.lineTo((390, 650)); pen.lineTo((110, 650)); pen.closePath()
    return pen.glyph()


for style, (wclass, stem, height) in WEIGHTS.items():
    riyal, adv = glyph_for(stem, height)
    fb = FontBuilder(UPM, isTTF=True)
    order = [".notdef", "space", "riyal"]
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({0x20: "space", 0x20C1: "riyal"})
    empty = TTGlyphPen(None).glyph()
    fb.setupGlyf({".notdef": notdef(), "space": empty, "riyal": riyal})
    fb.setupHorizontalMetrics({".notdef": (500, 60), "space": (250, 0), "riyal": (adv, SIDE)})
    fb.setupHorizontalHeader(ascent=ASC, descent=-DESC)
    family = "Agent Glyphs Riyal"
    fb.setupNameTable({
        "familyName": family,
        "styleName": style,
        "uniqueFontIdentifier": f"AgentGlyphsRiyal-{style};1.000",
        "fullName": f"{family} {style}",
        "psName": f"AgentGlyphsRiyal-{style}",
        "version": "Version 1.000",
        "copyright": "Saudi Riyal sign: Saudi Central Bank (SAMA). Font: Agent Glyphs (github.com/molamine08/agent-glyphs).",
        "licenseDescription": "MIT License (see LICENSE in github.com/molamine08/agent-glyphs)",
        "licenseInfoURL": "https://github.com/molamine08/agent-glyphs/blob/main/LICENSE",
    })
    fb.setupOS2(usWeightClass=wclass, sTypoAscender=ASC, sTypoDescender=-DESC, sTypoLineGap=0,
                usWinAscent=ASC, usWinDescent=DESC, sxHeight=520, sCapHeight=703,
                fsSelection=(0x20 if style == "Bold" else 0x40), achVendID="AGLY",
                ulUnicodeRange1=1, ulUnicodeRange2=0)
    fb.setupPost()
    fb.setupHead(unitsPerEm=UPM, created=timestampNow(), modified=timestampNow())
    fb.font["head"].macStyle = 1 if style == "Bold" else 0
    ttf = OUT / f"AgentGlyphsRiyal-{style}.ttf"
    fb.save(str(ttf))
    f = TTFont(str(ttf)); f.flavor = "woff2"; f.save(str(OUT / f"AgentGlyphsRiyal-{style}.woff2"))
    print(style, "adv", adv, "stem", stem)
