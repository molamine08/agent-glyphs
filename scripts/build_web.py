#!/usr/bin/env python3
"""Build the data files for the web page (web/) from atlas.db.

The page never downloads the 160 MB index. It loads one compact table of
every icon's name and labels, plus the Arabic dictionary, and fetches the
icons themselves from the public Iconify API as they come on screen.

    python scripts/build_web.py --db data/atlas.db --out web/data
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import glyphs as glyph_catalog  # noqa: E402
from atlas.query import set_prior  # noqa: E402
from atlas.concepts import groups as concept_groups, tables as concept_tables  # noqa: E402
from atlas.semantics import norm_ar, terms  # noqa: E402
from atlas.taxonomy import CATEGORIES, STYLE_TOKENS  # noqa: E402

SHAPES = ["outline", "filled", "mixed", "unknown"]
COLORS = ["mono", "duotone", "multicolor"]
DENSITY = ["airy", "balanced", "heavy"]
STROKES = ["thin", "light", "regular", "bold"]
CORNERS = ["rounded", "mixed", "sharp"]
TIERS = ["permissive", "attribution", "share-alike", "non-commercial", "unknown"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/atlas.db")
    ap.add_argument("--out", default="web/data")
    ap.add_argument("--external", help="external-sets.json.gz from the release (libraries outside Iconify)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(a.db)
    db.row_factory = sqlite3.Row
    cats = list(CATEGORIES)
    concept_sets = dict(db.execute("SELECT concept, sets FROM concepts"))

    sets, rows_by_set = [], {}
    for s in db.execute("SELECT * FROM sets ORDER BY prefix"):
        sets.append({
            "p": s["prefix"], "n": s["name"], "a": s["author"], "au": s["author_url"],
            "l": s["license"], "lu": s["license_url"], "t": TIERS.index(s["license_tier"]),
            "g": s["grid"], "c": s["category"], "k": s["total"],
        })
        rows_by_set[s["prefix"]] = []
    set_meta = {s["p"]: s for s in sets}

    # an index built by older code may lack the newest labels: derive them, so the
    # page can always be published (the next index update fills them in properly)
    have = {c[1] for c in db.execute("PRAGMA table_info(icons)")}
    from atlas.classify import STROKE_CLASSES
    cols = ["prefix", "name", "concept", "cat", "cat2", "weight", "corners", "density_class", "style"]
    cols += [c for c in ("shape", "color", "stroke") if c in have]

    def labels(r):
        r = dict(r)
        st = r.get("style")
        r.setdefault("shape", st if st in ("outline", "filled", "mixed") else ("filled" if st == "multicolor" else "outline"))
        r.setdefault("color", st if st in ("duotone", "multicolor") else "mono")
        if "stroke" not in r:
            w = r["weight"]
            r["stroke"] = next(label for top, label in STROKE_CLASSES if w < top) if w is not None else None
        return r

    for r in map(labels, db.execute(f"SELECT {', '.join(cols)} FROM icons ORDER BY prefix, name")):
        prior = set_prior(r["prefix"], set_meta[r["prefix"]]["c"], set_meta[r["prefix"]]["k"])
        prior += 0.5 * math.log(concept_sets.get(r["concept"], 1))
        rows_by_set[r["prefix"]].append([
            r["name"],
            SHAPES.index(r["shape"] if r["shape"] in SHAPES else "unknown"),
            COLORS.index(r["color"] if r["color"] in COLORS else "mono"),
            round(r["weight"] * 10) if r["weight"] is not None else -1,
            CORNERS.index(r["corners"]) if r["corners"] else -1,
            cats.index(r["cat"]) if r["cat"] in cats else cats.index("other"),
            cats.index(r["cat2"]) if r["cat2"] in cats else -1,
            max(0, min(99, round(prior * 10))),
            DENSITY.index(r["density_class"]) if r["density_class"] in DENSITY else -1,
            STROKES.index(r["stroke"]) if r["stroke"] in STROKES else -1,
        ])

    icons = [{"p": p, "i": rows} for p, rows in rows_by_set.items()]
    # glyphs: Unicode characters, searched by their own words (scripts/atlas/glyphs.py)
    glyphs_out = []
    for g in glyph_catalog.catalog():
        glyphs_out.append({"n": g["name"], "ch": g["char"], "cp": g["cp"], "un": g["unicode_name"],
                           "t": sorted(g["_tags"]), "a": g["_ar"], "f": sorted(g["_forms"]),
                           **({"e": 1} if g.get("kind") == "emoji" else {}), **({"w": 1} if g.get("wide") else {})})
    stats = json.loads(db.execute("SELECT value FROM meta WHERE key='stats'").fetchone()[0])
    version = db.execute("SELECT value FROM meta WHERE key='iconify_version'").fetchone()[0]
    meta = {
        "version": version, "icons": stats["icons"], "sets": len(sets), "glyphs": len(glyphs_out),
        "shapes": SHAPES, "colors": COLORS, "density": DENSITY, "strokes": STROKES, "corners": CORNERS, "tiers": TIERS,
        "categories": [[k, en, ar] for k, (en, ar) in CATEGORIES.items()],
        "styleTokens": sorted(STYLE_TOKENS),
    }
    # Meaning-aware search (same tables as scripts/atlas/concepts.py): concept
    # groups as [same-meaning tokens, related tokens], and the Arabic/English
    # words that lead to them. Tokens absent from every icon name are dropped.
    vocab = set()
    for (c,) in db.execute("SELECT DISTINCT concept FROM icons"):
        vocab.update(c.split("-"))
    for g in glyph_catalog.catalog():
        vocab.update(g["_tags"])  # so the meaning groups keep the words only glyphs use
    ar_exact, ar_stem, en_words = concept_tables()
    known = lambda t: all(x in vocab for x in t.split("-"))  # noqa: E731
    groups_out = [[[t for t in g["en"] if known(t)], [t for t in g["rel"] if known(t)]] for g in concept_groups()]
    # an Arabic name for each token, for the "also includes" chips
    labels = {}
    for g in concept_groups():
        if g["en"] and g["ar"] and g["en"][0] in vocab:
            labels.setdefault(g["en"][0], g["ar"][0])
    ar = {"g": groups_out, "ax": ar_exact, "as": ar_stem, "en": en_words, "lab": labels}
    terms_out = {tok: e.get("ar", [])[:3] for tok, e in terms().items() if e.get("ar")}

    (out / "meta.json").write_text(json.dumps({**meta, "setsInfo": sets}, ensure_ascii=False, separators=(",", ":")))
    (out / "icons.json").write_text(json.dumps(icons, separators=(",", ":")))
    (out / "glyphs.json").write_text(json.dumps(glyphs_out, ensure_ascii=False, separators=(",", ":")))
    (out / "ar.json").write_text(json.dumps({**ar, "terms": terms_out}, ensure_ascii=False, separators=(",", ":")))
    if a.external and Path(a.external).exists():
        # icons outside Iconify cannot come from its API: serve them from the page itself
        import gzip
        ext_dir = out / "ext"
        ext_dir.mkdir(exist_ok=True)
        for p, data in json.loads(gzip.decompress(Path(a.external).read_bytes())).items():
            (ext_dir / f"{p}.json").write_text(json.dumps(
                {"prefix": p, "icons": data["icons"], "width": data.get("width", 24), "height": data.get("height", 24)},
                separators=(",", ":")))
        print(f"ext/: {len(list(ext_dir.glob('*.json')))} libraries outside Iconify")
    for f in ("meta.json", "icons.json", "ar.json", "glyphs.json"):
        print(f"{f}: {(out / f).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
