#!/usr/bin/env python3
"""Islamic and Arabic glyphs as icons, drawn from open fonts.

Characters such as ﷽ ﷺ ۞ ۩ are not in any icon library: they live in fonts.
This script takes their outlines from fonts under the SIL Open Font License
and writes one SVG per character and font to sources/glyphs/islamic/. The
folder is an external library like any other (sources/external.json), so the
daily update measures, classifies and indexes it.

    python scripts/make_glyph_icons.py --fonts <dir with the .woff2/.ttf files>
"""

import argparse
import re
import unicodedata
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sources" / "glyphs" / "islamic"

CALLIGRAPHY = (
    list(range(0xFDF0, 0xFDFE))            # ﷰ … ﷽  (Allah, Muhammad, ﷺ, ﷻ, rial sign, bismillah)
    + [0xFDCF, 0xFDFE, 0xFDFF]             # Unicode 14 honorifics
    + list(range(0xFD40, 0xFD50))          # Unicode 14 honorific ligatures (رحمه الله …)
    + [0x06DD, 0x06DE, 0x06E9, 0xFD3E, 0xFD3F, 0x060E, 0x060F]  # end of ayah, rub el hizb, sajdah, ornate brackets, verse signs
)
EMOJI = [0x1F54C, 0x1F54B, 0x1F4FF, 0x1F319, 0x262A, 0x1F932, 0x1F9D5, 0x1F334, 0x1F42A]

# friendlier names than the Unicode ones where people search for them
NAMES = {
    0xFDF2: "allah", 0xFDF3: "akbar", 0xFDF4: "muhammad", 0xFDF5: "salam-abbreviation", 0xFDF6: "rasul",
    0xFDF7: "alayhi", 0xFDF8: "wasallam", 0xFDF9: "salla", 0xFDFA: "sallallahu-alayhi-wasallam",
    0xFDFB: "jalla-jalaluhu", 0xFDFC: "rial-sign", 0xFDFD: "bismillah",
    0xFDFE: "subhanahu-wa-taala", 0xFDFF: "azza-wa-jall", 0xFDCF: "salamuhu-alayna",
    0x06DD: "end-of-ayah", 0x06DE: "rub-el-hizb", 0x06E9: "sajdah",
    0xFD3E: "ornate-parenthesis-left", 0xFD3F: "ornate-parenthesis-right",
    0x060E: "poetic-verse-sign", 0x060F: "misra-sign",
    0x1F54C: "mosque", 0x1F54B: "kaaba", 0x1F4FF: "prayer-beads", 0x1F319: "crescent-moon",
    0x262A: "star-and-crescent", 0x1F932: "palms-up-dua", 0x1F9D5: "woman-hijab",
    0x1F334: "palm-tree", 0x1F42A: "camel",
}

SKIP_WIDE_BISMILLAH = {"amiri", "naskh"}

FONTS = [  # (file name pattern, style suffix, code points, licence holder)
    ("amiri-arabic-400-normal", "amiri", CALLIGRAPHY, "Amiri, Khaled Hosny"),
    ("scheherazade-new-arabic-400-normal", "scheherazade", CALLIGRAPHY, "Scheherazade New, SIL International"),
    ("noto-naskh-arabic-arabic-400-normal", "naskh", CALLIGRAPHY, "Noto Naskh Arabic, Google"),
    ("noto-emoji-emoji-400-normal", "", EMOJI, "Noto Emoji, Google"),
]


def name_of(cp: int) -> str:
    if cp in NAMES:
        return NAMES[cp]
    n = unicodedata.name(chr(cp), f"u{cp:04x}").lower()
    n = re.sub(r"^arabic (ligature )?|( isolated form)$", "", n)
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def glyph_svg(font: TTFont, cp: int) -> str | None:
    cmap = font.getBestCmap()
    if cp not in cmap:
        return None
    gs = font.getGlyphSet()
    g = gs[cmap[cp]]
    bp = BoundsPen(gs)
    g.draw(bp)
    if not bp.bounds:
        return None
    x0, y0, x1, y1 = bp.bounds
    pen = SVGPathPen(gs)
    g.draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))  # fonts point y up, SVG points y down
    d = pen.getCommands()
    w, h = x1 - x0, y1 - y0
    pad = 0.08 * max(w, h)
    # small marks get a square box; wide calligraphy keeps its own proportions
    side = max(w, h)
    bw, bh = (side, side) if w / max(h, 1) < 1.6 else (w, h)
    vx, vy = x0 - (bw - w) / 2 - pad, -y1 - (bh - h) / 2 - pad
    vb = f"{vx:.0f} {vy:.0f} {bw + 2 * pad:.0f} {bh + 2 * pad:.0f}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><path fill="currentColor" d="{d}"/></svg>\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="folder holding the font files")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    made, credits = 0, []
    for pattern, suffix, cps, holder in FONTS:
        files = sorted(Path(a.fonts).rglob(f"{pattern}.woff2")) or sorted(Path(a.fonts).rglob(f"{pattern}*.[ot]tf"))
        if not files:
            print(f"! missing font {pattern}")
            continue
        font = TTFont(files[0])
        n = 0
        for cp in cps:
            svg = glyph_svg(font, cp)
            if not svg:
                continue
            if cp == 0xFDFD and suffix in SKIP_WIDE_BISMILLAH:
                continue  # drawn as one long stretched line: unreadable at icon size
            name = name_of(cp) + (f"-{suffix}" if suffix else "")
            (OUT / f"{name}.svg").write_text(svg)
            n += 1
        made += n
        credits.append(f"- {holder}: {n} glyphs (SIL Open Font License 1.1)")
        print(f"{pattern}: {n}")
    (OUT / "LICENSE.md").write_text(
        "# Islamic and Arabic glyphs\n\nOutlines of Unicode characters taken from fonts licensed under the "
        "SIL Open Font License 1.1 (https://openfontlicense.org). They are redistributed under the same licence.\n\n"
        + "\n".join(credits) + "\n")
    print("total", made)


if __name__ == "__main__":
    main()
