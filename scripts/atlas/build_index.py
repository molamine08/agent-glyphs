"""Combine per-set metrics into one searchable SQLite index (atlas.db).

    python -m atlas.build_index --metrics data/metrics --out data/atlas.db
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from . import vision
from .classify import STROKE_CLASSES, classify, concept_of, license_tier, name_tokens
from .semantics import arabic_terms, categories_for, map_set_category, norm_ar
from .taxonomy import CATEGORIES, STYLE_TOKENS

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sets(
  prefix TEXT PRIMARY KEY, name TEXT, total INT, author TEXT, author_url TEXT,
  license TEXT, license_url TEXT, license_tier TEXT, category TEXT, grid INT,
  palette INT, version TEXT, last_modified INT, samples TEXT
);
CREATE TABLE families(
  id INTEGER PRIMARY KEY, prefix TEXT, variant TEXT, label TEXT, n INT,
  style TEXT, weight REAL, roundness REAL, curviness REAL, contrast REAL,
  density REAL, padding REAL, corners TEXT, weight_class TEXT
);
CREATE TABLE icons(
  id INTEGER PRIMARY KEY, prefix TEXT, name TEXT, family_id INT, concept TEXT,
  cat TEXT, cat2 TEXT, style TEXT, style_conf TEXT, weight REAL, weight_class TEXT,
  weight_conf TEXT, corners TEXT, corners_conf TEXT, roundness REAL,
  curviness REAL, curves TEXT, contrast REAL, contrast_class TEXT,
  density REAL, density_class TEXT, padding REAL, container TEXT,
  complexity TEXT, w REAL, h REAL, license_tier TEXT, shape TEXT, color TEXT, stroke TEXT, animated INT
);
CREATE TABLE concepts(concept TEXT PRIMARY KEY, sets INT);
CREATE VIRTUAL TABLE icons_fts USING fts5(
  en, ar, extra, content = "", detail = column,
  tokenize = "unicode61 remove_diacritics 2"
);
"""

FAMILY_STYLE_TOKENS = STYLE_TOKENS | {"16", "20", "24", "32", "48", "12"}


def variant_of(name: str, suffixes: dict, prefixes: dict) -> str:
    """Style variant inside a set: 'bold', 'outline-rounded', '20-solid'..."""
    for sfx in sorted((s for s in suffixes if s), key=len, reverse=True):
        if name.endswith("-" + sfx):
            return sfx
    for pfx in sorted((p for p in prefixes if p), key=len, reverse=True):
        if name.startswith(pfx + "-"):
            return pfx
    toks = [t for t in name_tokens(name) if t in FAMILY_STYLE_TOKENS]
    return "-".join(toks)


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


ANIMATION = ("<animate", "<set ", "@keyframes", "animation:")


def animated_names(src_dir: Path | None, prefix: str) -> set:
    """Icons that move (SMIL or CSS animation), read from the set's own SVG data."""
    if not src_dir or not (src_dir / f"{prefix}.json").exists():
        return set()
    data = json.loads((src_dir / f"{prefix}.json").read_text())
    return {n for n, ic in data.get("icons", {}).items() if any(a in ic.get("body", "") for a in ANIMATION)}


def build(metrics_dir: Path, out: Path, version: str | None, src_dir: Path | None = None) -> dict:
    if out.exists():
        out.unlink()
    db = sqlite3.connect(out)
    db.executescript(SCHEMA)
    stats = defaultdict(int)
    icon_id = 0
    fam_id = 0
    for path in sorted(metrics_dir.glob("*.json.gz")):
        with gzip.open(path, "rt") as f:
            rec = json.load(f)
        prefix, info = rec["prefix"], rec["info"]
        moving = animated_names(src_dir, prefix)
        lic = info.get("license", {})
        tier = license_tier(lic.get("spdx"))
        author = info.get("author", {})
        db.execute(
            "INSERT INTO sets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (prefix, info.get("name"), len(rec["icons"]), author.get("name"), author.get("url"),
             lic.get("spdx"), lic.get("url"), tier, info.get("category"), info.get("height"),
             int(bool(info.get("palette"))), info.get("version"), rec["stamp"].get("lastModified"),
             json.dumps(info.get("samples", []))),
        )
        # icon -> category label provided by the set itself
        given = {}
        for label, names in (rec.get("categories") or {}).items():
            cat = map_set_category(label)
            if cat:
                for n in names:
                    given.setdefault(n, cat)
        aliases = defaultdict(list)
        for alias, parent in rec.get("aliases", {}).items():
            if parent:
                aliases[parent].append(alias)

        rows, fams = [], defaultdict(list)
        for name, m in rec["icons"].items():
            lab = classify(prefix, name, m, rec.get("light", False))
            var = variant_of(name, rec.get("suffixes") or {}, rec.get("prefixes") or {})
            fams[var].append(lab)
            cats = categories_for(name, info.get("category"), given.get(name), prefix,
                                  vision.votes(prefix, name, concept_of(name)))
            cat = cats[0]
            concept = concept_of(name)
            ar = arabic_terms(name) + [w for a in aliases[name] for w in arabic_terms(a)]
            ar = list(dict.fromkeys(ar))
            en = " ".join(dict.fromkeys(name_tokens(name) + [t for a in aliases[name] for t in name_tokens(a)]))
            extra = f"{prefix} {info.get('name', '')}"
            for c in cats:
                c_en, c_ar = CATEGORIES.get(c, CATEGORIES["other"])
                extra += f" {c} {c_en} {norm_ar(c_ar)}"
            rows.append((name, var, concept, cats, lab, m, en, " ".join(norm_ar(w) for w in ar), extra))
            stats["icons"] += 1
            stats["animated"] += int(name in moving or bool(m.get("animated")))
            stats[f"shape:{lab.get('shape')}"] += 1
            stats[f"color:{lab.get('color')}"] += 1
            if ar:
                stats["with_ar"] += 1
            if cats[0] != "other":
                stats["with_cat"] += 1

        # Family consistency, only where the drawing itself is undecided:
        # a borderline "mixed" icon follows a clearly outline or filled family,
        # and an icon without corners (a circle, a wave) takes its family's
        # corners. An icon drawn with lines stays "outline" even inside a
        # filled family: filters show what the eye sees.
        fam_major, fam_corners, fam_weight = {}, {}, {}
        for var, labs in fams.items():
            ws = [l["weight"] for l in labs if l.get("weight") and l.get("shape") == "outline"]
            if len(ws) >= 20:
                fam_weight[var] = statistics.median(ws)
            shapes = [l.get("shape") for l in labs]
            top = max(set(shapes), key=shapes.count)
            fam_major[var] = (top, shapes.count(top) / len(shapes))
            cs = [l.get("corners") for l in labs if l.get("corners")]
            if cs:
                c = max(set(cs), key=cs.count)
                if cs.count(c) / len(cs) >= 0.6:
                    fam_corners[var] = c
        for row in rows:
            lab = row[4]
            top, share = fam_major[row[1]]
            if lab.get("shape") == "mixed" and top in ("outline", "filled") and share >= 0.7:
                lab["shape"], lab["style_conf"] = top, "medium"
                if lab.get("color", "mono") == "mono":
                    lab["style"] = top
            # a family is drawn with one stroke: icons close to its median (detail-heavy
            # icons measure a little heavier) take the family's stroke class
            fw = fam_weight.get(row[1])
            if fw and lab.get("weight") and abs(lab["weight"] - fw) <= 0.15 * fw:
                lab["stroke"] = next(label for top, label in STROKE_CLASSES if fw < top)
            if not lab.get("corners") and row[1] in fam_corners and lab.get("shape") not in (None, "unknown"):
                lab["corners"], lab["corners_conf"] = fam_corners[row[1]], "low"

        fam_ids = {}
        for var, labs in fams.items():
            fam_id += 1
            fam_ids[var] = fam_id
            styles = [l.get("style") for l in labs]
            main_style = max(set(styles), key=styles.count)
            corners = [l.get("corners") for l in labs if l.get("corners")]
            wcls = [l.get("weight_class") for l in labs if l.get("weight_class")]
            label = info.get("name", prefix) + (f" · {var}" if var else "")
            db.execute(
                "INSERT INTO families VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (fam_id, prefix, var, label, len(labs), main_style,
                 _median(l.get("weight") for l in labs), _median(l.get("roundness") for l in labs),
                 _median(l.get("curviness") for l in labs), _median(l.get("contrast") for l in labs),
                 _median(l.get("density") for l in labs), _median(l.get("padding") for l in labs),
                 max(set(corners), key=corners.count) if corners else None,
                 max(set(wcls), key=wcls.count) if wcls else None),
            )
        for name, var, concept, cats, lab, m, en, ar, extra in rows:
            icon_id += 1
            db.execute(
                "INSERT INTO icons VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (icon_id, prefix, name, fam_ids[var], concept, cats[0], cats[1] if len(cats) > 1 else None,
                 lab.get("style"), lab.get("style_conf"),
                 lab.get("weight"), lab.get("weight_class"), lab.get("weight_conf"), lab.get("corners"),
                 lab.get("corners_conf"), lab.get("roundness"), lab.get("curviness"), lab.get("curves"),
                 lab.get("contrast"), lab.get("contrast_class"), lab.get("density"), lab.get("density_class"),
                 lab.get("padding"), lab.get("container"), lab.get("complexity"), m.get("w"), m.get("h"), tier,
                 lab.get("shape"), lab.get("color"), lab.get("stroke"),
                 int(name in moving or bool(m.get("animated")))),
            )
            db.execute("INSERT INTO icons_fts(rowid,en,ar,extra) VALUES(?,?,?,?)", (icon_id, en, ar, extra))
        stats["sets"] += 1
    # how many libraries draw a concept: a strong hint of the canonical name
    db.execute("INSERT INTO concepts SELECT concept, COUNT(DISTINCT prefix) FROM icons GROUP BY concept")
    for col in ("prefix", "concept", "cat", "cat2", "style", "shape", "color", "stroke", "animated", "weight_class", "corners", "density_class",
                "family_id", "license_tier"):
        db.execute(f"CREATE INDEX ix_{col} ON icons({col})")
    db.execute("INSERT INTO meta VALUES('iconify_version', ?)", (version,))
    db.execute("INSERT INTO meta VALUES('stats', ?)", (json.dumps(stats),))
    db.commit()
    db.execute("VACUUM")
    db.close()
    return dict(stats)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--version")
    ap.add_argument("--src", help="Iconify JSON folder, to tell which icons are animated")
    a = ap.parse_args(argv)
    stats = build(Path(a.metrics), Path(a.out), a.version, Path(a.src) if a.src else None)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    sys.exit(main())
