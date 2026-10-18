"""Turn raw metrics into the labels people search by, with a confidence.

Thresholds were calibrated on sets whose drawing rules are published
(Lucide/Tabler 2px round, Heroicons 1.5px, Phosphor thin..bold, Material
sharp vs rounded, MDI). See tests/calibration.md.
"""

from __future__ import annotations

import re

from .taxonomy import STYLE_TOKENS

# bump when the labels change, so the daily update rebuilds the index
LABELS_VERSION = 3  # 3: four stroke classes; 2: shape and colour apart, corners from real corners, filters follow the drawing

FILLED_HINTS = {"fill", "filled", "solid", "glyph"}
OUTLINE_HINTS = {"outline", "outlined", "outlines", "line", "lines", "linear", "stroke", "stroked"}
DUO_HINTS = {"duotone", "twotone", "duo", "bulk", "two-tone"}

# Four classes people pick from, calibrated on libraries with published strokes
# (24-grid units): Phosphor Thin 0.75 / Light 1.1 -> thin; Heroicons, Phosphor,
# Iconoir, Solar, Carbon 1.5 -> light; Lucide, Tabler, Mingcute, Material 2 ->
# regular; Phosphor Bold 2.25 and heavier -> bold.
STROKE_CLASSES = [(1.25, "thin"), (1.75, "light"), (2.15, "regular"), (99, "bold")]

WEIGHT_CLASSES = [  # upper bounds, 24px grid units
    (0.6, "hairline"), (1.1, "thin"), (1.4, "light"), (1.75, "regular"),
    (2.25, "medium"), (2.9, "bold"), (99, "heavy"),
]

LICENSE_TIERS = {
    "permissive": {"MIT", "Apache-2.0", "ISC", "BSD-2-Clause", "BSD-3-Clause", "CC0-1.0", "Unlicense", "OFL-1.1", "0BSD"},
    "attribution": {"CC-BY-3.0", "CC-BY-4.0"},
    "share-alike": {"CC-BY-SA-3.0", "CC-BY-SA-4.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later", "MPL-2.0", "LGPL-3.0"},
    "non-commercial": {"CC-BY-NC-4.0", "CC-BY-NC-SA-4.0", "CC-BY-NC-3.0", "CC-BY-NC-ND-4.0"},
}


def license_tier(spdx: str | None) -> str:
    for tier, ids in LICENSE_TIERS.items():
        if spdx in ids:
            return tier
    return "unknown"


def name_tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[-_:]+", name.lower()) if t]


def concept_of(name: str) -> str:
    toks = [t for t in name_tokens(name) if t not in STYLE_TOKENS and not re.fullmatch(r"\d+(px)?", t)]
    return "-".join(toks) or name


def _hint(tokens: set[str]) -> str | None:
    if tokens & DUO_HINTS:
        return "duotone"
    if tokens & FILLED_HINTS:
        return "filled"
    if tokens & OUTLINE_HINTS:
        return "outline"
    return None


def classify(prefix: str, name: str, m: dict, set_light: bool) -> dict:
    out: dict = {}
    if m.get("error") or m.get("empty"):
        out["style"], out["style_conf"], out["shape"], out["color"] = "unknown", "low", "unknown", "mono"
        return out
    ntoks = name_tokens(name)
    toks = set(ntoks) | set(name_tokens(prefix))
    hint = _hint(toks)
    if hint is None and ntoks and ntoks[-1] == "f":  # e.g. jam:padlock-f
        hint = "filled"

    # ---- shape and colour --------------------------------------------------
    # Two separate questions, both answered by what the eye sees:
    #   shape: outline (lines only), filled, or mixed (lines with filled parts)
    #   color: mono, duotone (a second, lighter tone) or multicolor
    # The name only breaks a tie ("mixed" or unmeasured drawings): an icon called
    # "link-filled" that is drawn with lines is an outline icon.
    solidity = m.get("solidity")
    if m.get("multicolor"):
        color = "multicolor"
    elif m.get("translucent") and ((m.get("tint") or 0) >= 0.05 or hint == "duotone"):
        color = "duotone"
    else:
        color = "mono"
    if set_light and solidity is None:  # emoji / flag / logo sets: drawn as shapes
        shape, conf = "filled", "low"
    else:
        if solidity is None:
            raster = None
        elif solidity > 0.12 or (solidity >= 0.05 and (m.get("weight") or 0) >= 3.0):
            raster = "filled"
        elif solidity < 0.08:
            raster = "outline"
        else:
            raster = "mixed"
        shape_hint = hint if hint in ("filled", "outline") else None
        if raster in ("filled", "outline"):
            shape, conf = raster, ("high" if shape_hint in (None, raster) else "medium")
        elif raster == "mixed" and shape_hint:
            shape, conf = shape_hint, "medium"
        else:
            shape, conf = (raster or shape_hint or "unknown"), "medium" if raster else "low"
    style = color if color != "mono" else shape  # the older single label, kept for --style
    out["shape"], out["color"], out["style"], out["style_conf"] = shape, color, style, conf

    # ---- weight ----------------------------------------------------------
    w = m.get("weight")
    linear = solidity is not None and solidity < 0.08
    if w is not None and (shape in ("outline", "mixed") or linear):
        out["weight"] = round(w, 2)
        out["weight_class"] = next(label for top, label in WEIGHT_CLASSES if w < top)
        out["stroke"] = next(label for top, label in STROKE_CLASSES if w < top)
        declared = m.get("declared_stroke")
        if declared:
            ref = declared * 24 / m["h"]
            out["weight_conf"] = "high" if abs(ref - w) / ref < 0.15 else "medium"
        else:
            out["weight_conf"] = "medium"
    if shape == "filled" and not linear:
        out["weight_class"] = "solid"
        out["weight_conf"] = "high" if conf == "high" else "medium"

    # ---- corners & curves --------------------------------------------------
    # corner_roundness only counts real corners (two straight runs meeting) and
    # line ends; circles and arcs are not corners. None = the drawing has none,
    # and the icon then follows its family (build_index).
    r = m.get("corner_roundness") if "corner_roundness" in m else m.get("roundness")
    if r is not None:
        out["roundness"] = round(r, 2)
        out["corners"] = "rounded" if r >= 0.8 else ("sharp" if r <= 0.45 else "mixed")
        out["corners_conf"] = "high" if (r >= 0.92 or r <= 0.3) else ("medium" if r >= 0.8 or r <= 0.45 else "low")
        if m.get("linecap") in ("round", "square", "butt") and shape == "outline":
            cap_round = m["linecap"] == "round"
            if cap_round == (out["corners"] == "rounded"):
                out["corners_conf"] = "high"
    c = m.get("curviness")
    if c is not None:
        out["curviness"] = round(c, 2)
        out["curves"] = "geometric" if c < 0.3 else ("organic" if c > 0.58 else "balanced")

    # ---- contrast, density, padding ---------------------------------------
    sc = m.get("stroke_contrast")
    if sc is not None and shape in ("outline", "mixed"):
        out["contrast"] = round(sc, 2)
        out["contrast_class"] = "monoline" if sc < 0.15 else ("high" if sc > 0.45 else "moderate")
    d = m.get("density")
    if d is not None:
        out["density"] = round(d, 3)
        out["density_class"] = "airy" if d < 0.14 else ("heavy" if d > 0.32 else "balanced")
    if m.get("padding") is not None:
        out["padding"] = round(m["padding"], 3)

    # ---- silhouette & complexity -------------------------------------------
    circ, rect, ext = m.get("hull_circularity"), m.get("hull_rectangularity"), m.get("extent", 0)
    container = "none"
    if ext > 0.62:
        if circ and circ > 0.95:
            container = "circle"
        elif rect and rect > 0.96:
            container = "square"
    if "circle" in toks and container == "none" and circ and circ > 0.9:
        container = "circle"
    if "square" in toks and container == "none" and rect and rect > 0.9:
        container = "square"
    out["container"] = container
    L = m.get("outline_len")
    if L is not None:
        out["complexity"] = "simple" if L < 115 else ("detailed" if L > 180 else "medium")
    return out
