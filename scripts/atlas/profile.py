"""Style profiles: what "looks like X" means, for a set, an icon or your own SVGs."""

from __future__ import annotations

import re
import sqlite3
import statistics
from pathlib import Path

from .analyze import analyze
from .classify import classify, concept_of

KEYS = ("weight", "roundness", "curviness", "contrast", "density", "padding")


def parse_svg(text: str) -> tuple[str, float, float, float, float]:
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>", text, re.S | re.I)
    if not m:
        raise ValueError("not an SVG file")
    attrs, body = m.group(1), m.group(2)
    vb = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)', attrs)
    if vb:
        left, top, w, h = map(float, vb.groups())
    else:
        w = float(re.search(r'width="([\d.]+)', attrs).group(1))
        h = float(re.search(r'height="([\d.]+)', attrs).group(1))
        left = top = 0.0
    # attributes set on the root <svg> (fill="none" stroke=...) must reach the body
    inherit = " ".join(re.findall(r'\s((?:fill|stroke|stroke-width|stroke-linecap|stroke-linejoin)="[^"]*")', attrs))
    if inherit:
        body = f"<g {inherit}>{body}</g>"
    return body, left, top, w, h


def concepts_from_filename(stem: str) -> list[str]:
    """'tabler-home', 'ic_home_24px', 'IconHome' -> candidate concepts ['tabler-home', 'home', ...]."""
    stem = re.sub(r"([a-z])([A-Z])", r"\1-\2", stem)
    toks = [t for t in re.split(r"[^a-zA-Z0-9]+", stem.lower()) if t]
    toks = [t for t in toks if t not in ("icon", "ic", "svg") and not re.fullmatch(r"\d+(px)?", t)]
    out = []
    for i in range(len(toks)):  # drop leading library prefixes one by one
        c = concept_of("-".join(toks[i:]))
        if c and c not in out:
            out.append(c)
    return out[:4]


def profile_from_svgs(paths: list[Path]) -> dict:
    labs = []
    for p in paths:
        body, l, t, w, h = parse_svg(p.read_text())
        m = analyze(body, l, t, w, h)
        m["w"], m["h"] = w, h
        lab = classify("", p.stem, m, False)
        lab["concepts"] = concepts_from_filename(p.stem)
        labs.append(lab)
    styles = [x.get("style") for x in labs]
    prof = {"style": max(set(styles), key=styles.count), "n": len(labs), "items": labs}
    for k in KEYS:
        vals = [x[k] for x in labs if x.get(k) is not None]
        prof[k] = statistics.median(vals) if vals else None
    return prof


def resolve_like(db: sqlite3.Connection, spec: str) -> dict:
    """Accepts: path to an SVG file or a folder of SVGs, 'prefix:name' (an
    icon), 'prefix' or 'prefix:variant' (a family)."""
    p = Path(spec).expanduser()
    if p.exists():
        files = sorted(p.glob("*.svg")) if p.is_dir() else [p]
        if not files:
            raise SystemExit(f"no .svg files in {p}")
        return profile_from_svgs(files[:40])
    prefix, _, rest = spec.partition(":")
    if rest:
        row = db.execute("SELECT * FROM icons WHERE prefix=? AND name=?", (prefix, rest)).fetchone()
        if row:
            return {**{k: row[k] for k in ("style",) + KEYS}, "prefix": prefix}
        row = db.execute("SELECT * FROM families WHERE prefix=? AND variant=?", (prefix, rest)).fetchone()
    else:
        row = db.execute("SELECT * FROM families WHERE prefix=? ORDER BY (variant='') DESC, n DESC",
                         (prefix,)).fetchone()
    if not row:
        raise SystemExit(f"unknown style reference '{spec}' (try a set prefix like lucide, or a .svg path)")
    return {**{k: row[k] for k in ("style",) + KEYS}, "prefix": prefix}
