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

from atlas.query import set_prior  # noqa: E402
from atlas.semantics import norm_ar, terms  # noqa: E402
from atlas.taxonomy import CATEGORIES, STYLE_TOKENS  # noqa: E402

STYLES = ["outline", "filled", "duotone", "multicolor", "mixed", "unknown"]
CORNERS = ["rounded", "mixed", "sharp"]
TIERS = ["permissive", "attribution", "share-alike", "non-commercial", "unknown"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/atlas.db")
    ap.add_argument("--out", default="web/data")
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

    for r in db.execute("SELECT prefix, name, concept, cat, cat2, style, weight, corners, density, curves "
                        "FROM icons ORDER BY prefix, name"):
        prior = set_prior(r["prefix"], set_meta[r["prefix"]]["c"], set_meta[r["prefix"]]["k"])
        prior += 0.5 * math.log(concept_sets.get(r["concept"], 1))
        rows_by_set[r["prefix"]].append([
            r["name"],
            STYLES.index(r["style"] or "unknown"),
            round(r["weight"] * 10) if r["weight"] is not None else -1,
            CORNERS.index(r["corners"]) if r["corners"] else -1,
            cats.index(r["cat"]) if r["cat"] in cats else cats.index("other"),
            cats.index(r["cat2"]) if r["cat2"] in cats else -1,
            max(0, min(99, round(prior * 10))),
        ])

    icons = [{"p": p, "i": rows} for p, rows in rows_by_set.items()]
    stats = json.loads(db.execute("SELECT value FROM meta WHERE key='stats'").fetchone()[0])
    version = db.execute("SELECT value FROM meta WHERE key='iconify_version'").fetchone()[0]
    meta = {
        "version": version, "icons": stats["icons"], "sets": len(sets),
        "styles": STYLES, "corners": CORNERS, "tiers": TIERS,
        "categories": [[k, en, ar] for k, (en, ar) in CATEGORIES.items()],
        "styleTokens": sorted(STYLE_TOKENS),
    }
    # Arabic search: normalised Arabic phrase -> English name words
    ar = {}
    for tok, e in terms().items():
        for w in e.get("ar", []):
            ar.setdefault(norm_ar(w), []).append(tok)
    terms_out = {tok: e.get("ar", [])[:3] for tok, e in terms().items() if e.get("ar")}

    (out / "meta.json").write_text(json.dumps({**meta, "setsInfo": sets}, ensure_ascii=False, separators=(",", ":")))
    (out / "icons.json").write_text(json.dumps(icons, separators=(",", ":")))
    (out / "ar.json").write_text(json.dumps({"rev": ar, "terms": terms_out}, ensure_ascii=False, separators=(",", ":")))
    for f in ("meta.json", "icons.json", "ar.json"):
        print(f"{f}: {(out / f).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
