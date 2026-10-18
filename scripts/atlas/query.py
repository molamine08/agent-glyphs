"""Search and style matching over atlas.db."""

from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass

from . import glyphs as glyph_catalog
from .concepts import expand, level
from .semantics import has_arabic, norm_ar

COMMERCIAL_TIERS = ("permissive", "attribution")

# Widely used, actively maintained, internally consistent libraries rank first
# when several icons match equally well.
POPULAR = {
    "lucide", "tabler", "ph", "heroicons", "material-symbols", "ic", "mdi", "ri", "iconoir",
    "solar", "hugeicons", "fluent", "carbon", "bi", "mingcute", "radix-icons", "octicon",
    "majesticons", "akar-icons", "uil", "ion", "f7", "fa6-solid", "fa6-regular", "simple-icons",
    "lineicons", "basil", "streamline", "mynaui", "lets-icons", "proicons", "humbleicons",
    "gravity-ui", "line-md", "svg-spinners", "material-symbols-light", "icon-park-outline",
    "fluent-emoji-flat", "twemoji", "noto", "flag", "circle-flags", "logos", "devicon",
}


def set_prior(prefix: str, category: str | None, total: int | None) -> float:
    score = 1.2 if prefix in POPULAR else 0.0
    if category == "Archive / Unmaintained":
        score -= 1.5
    if total:
        score += 0.25 * math.log10(max(total, 10))
    return score

# Style features compared when matching "looks like X". Weights express how
# much a difference matters visually.
FEATURES = {
    "weight": 2.2,     # compared on a log scale
    "roundness": 1.6,
    "curviness": 0.5,   # depends on what is drawn, so it counts less
    "contrast": 0.7,
    "density": 0.35,
    "padding": 0.5,
}
SCALE = {"weight": 0.25, "roundness": 0.15, "curviness": 0.12, "contrast": 0.15, "density": 0.06, "padding": 0.04}


def style_distance(a: dict, b: dict) -> float:
    if a.get("style") and b.get("style") and a["style"] != b["style"]:
        mismatch = 0.0 if {a["style"], b["style"]} <= {"outline", "duotone"} else 6.0
    else:
        mismatch = 0.0
    total = wsum = 0.0
    for f, w in FEATURES.items():
        x, y = a.get(f), b.get(f)
        if x is None or y is None:
            continue
        if f == "weight":
            d = abs(math.log(max(x, 0.05)) - math.log(max(y, 0.05))) / SCALE[f]
        else:
            d = abs(x - y) / SCALE[f]
        total += w * min(d, 6) ** 2
        wsum += w
    return mismatch + (math.sqrt(total / wsum) if wsum else 3.0)


@dataclass
class Filters:
    style: str | None = None  # older single label: outline | filled | mixed (shape) or duotone | multicolor (color)
    shape: str | None = None  # outline | filled | mixed
    color: str | None = None  # mono | duotone | multicolor
    density: str | None = None  # airy | balanced | heavy
    stroke: str | None = None  # thin | light | regular | bold
    weight: float | None = None
    weight_tol: float = 0.3
    weight_class: str | None = None
    corners: str | None = None
    curves: str | None = None
    contrast: str | None = None
    container: str | None = None
    complexity: str | None = None
    cat: str | None = None
    sets: list[str] | None = None
    license: str = "commercial"  # commercial | permissive | any
    min_conf: str | None = None  # high | medium
    kind: str | None = None  # icon (still) | animated | glyph (None: all)

    def shape_filtered(self) -> bool:
        """Filters about how an icon is drawn, which a character does not have."""
        return any(v is not None for v in (self.style, self.shape, self.color, self.density, self.stroke, self.weight, self.weight_class, self.corners, self.curves,
                                            self.contrast, self.container, self.complexity, self.min_conf)) \
            or bool(self.sets and glyph_catalog.PREFIX not in self.sets)


def _fts_query(parts) -> str:
    """Every query part must match (AND); within a part, the word itself
    (prefix match, Arabic in the ar column) or any token that means the same
    thing or is closely related to it (OR)."""
    clauses = []
    for p in parts:
        alts = []
        if has_arabic(p.text):
            words = [w for w in (norm_ar(x) for x in p.text.split()) if w]
            if words:  # a phrase ("رضي الله عنه") needs all its words, not any one of them
                alts.append("(" + " AND ".join(f'ar:"{w}"*' for w in words) + ")" if len(words) > 1
                            else f'ar:"{words[0]}"*')
        else:
            alts.append(f'{{en extra}}:"{p.text}"*')
        for tok in sorted(p.strong | p.related):
            if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", tok) and tok != p.text:
                # the index has no word positions, so "log-out" means: uses both words
                alts.append("(" + " AND ".join(f'en:"{x}"' for x in tok.split("-")) + ")" if "-" in tok else f'en:"{tok}"')
        clauses.append("(" + " OR ".join(alts) + ")")
    return " AND ".join(clauses)


def search(db: sqlite3.Connection, text: str | None, f: Filters, limit: int = 20,
           per_set: int = 2, like: dict | None = None) -> list[dict]:
    """Icons and glyphs (Unicode characters) for a query. Glyphs that are exactly
    what was asked for (by name or by their Arabic words) come first; other
    matching glyphs follow the first icons."""
    parts = expand(text) if text else []
    glyphs = []
    if f.kind not in ("icon", "animated") and not f.shape_filtered() and not like and f.cat in (None, "culture"):
        glyphs = glyph_catalog.search(text or "", parts, limit=limit if f.kind == "glyph" else 6)
        if not text and f.kind == "glyph":
            glyphs = [glyph_catalog.public(g) for g in glyph_catalog.catalog()][:limit]
    if f.kind == "glyph":
        return glyphs
    icons = _search_icons(db, text, parts, f, limit, per_set, like)
    for d in icons:
        d.setdefault("kind", "icon")
    first = [g for g in glyphs if g["level"] >= 4][:3]
    later = [g for g in glyphs if g not in first]
    return (first + icons[:4] + later + icons[4:])[:limit] if glyphs else icons


def _search_icons(db, text, parts, f: Filters, limit, per_set, like) -> list[dict]:
    where, args = [], []
    shape, color = f.shape, f.color
    if f.style in ("duotone", "multicolor"):
        color = color or f.style
    elif f.style:
        shape = shape or f.style
    if shape:
        where.append("i.shape = ?"); args.append(shape)
    if color:
        where.append("i.color = ?"); args.append(color)
    if f.density:
        where.append("i.density_class = ?"); args.append(f.density)
    filled = f.shape == "filled" or f.style == "filled"
    if f.stroke and not filled:
        where.append("i.stroke = ?"); args.append(f.stroke)
    if f.weight is not None and not filled:  # a filled icon has no stroke: the weight filter does not apply
        where.append("i.weight BETWEEN ? AND ?"); args += [f.weight - f.weight_tol, f.weight + f.weight_tol]
    for col, val in (("weight_class", f.weight_class), ("corners", f.corners), ("curves", f.curves),
                     ("contrast_class", f.contrast), ("container", f.container),
                     ("complexity", f.complexity)):
        if val:
            where.append(f"i.{col} = ?"); args.append(val)
    if f.kind == "animated":
        where.append("i.animated = 1")
    elif f.kind == "icon":
        where.append("COALESCE(i.animated, 0) = 0")
    if f.cat:
        where.append("(i.cat = ? OR i.cat2 = ?)"); args += [f.cat, f.cat]
    sets = [x for x in (f.sets or []) if x != glyph_catalog.PREFIX]
    if f.sets and not sets:
        return []
    if sets:
        where.append(f"i.prefix IN ({','.join('?' * len(sets))})"); args += sets
    if f.license == "commercial":
        where.append("i.license_tier IN ('permissive','attribution')")
    elif f.license == "permissive":
        where.append("i.license_tier = 'permissive'")
    if f.min_conf == "high":
        where.append("i.style_conf = 'high'")
    elif f.min_conf == "medium":
        where.append("i.style_conf IN ('high','medium')")

    cols = ("i.*, s.name AS set_name, s.license, s.license_url, s.author, s.category AS set_category, "
            "s.total AS set_total, fam.label AS family, COALESCE(c.sets, 1) AS concept_sets")
    joins = ("JOIN sets s ON s.prefix = i.prefix JOIN families fam ON fam.id = i.family_id "
             "LEFT JOIN concepts c ON c.concept = i.concept")
    q = _fts_query(parts) if parts else ""
    pool = max(limit * 300, 6000)
    if q:
        sql = (f"SELECT {cols}, bm25(icons_fts, 4.0, 3.0, 0.5) AS rank FROM icons_fts "
               f"JOIN icons i ON i.id = icons_fts.rowid {joins} WHERE icons_fts MATCH ? "
               + ("AND " + " AND ".join(where) if where else "") + " ORDER BY rank LIMIT ?")
        rows = db.execute(sql, [q] + args + [pool]).fetchall()
    else:
        sql = (f"SELECT {cols}, 0 AS rank FROM icons i {joins} "
               + ("WHERE " + " AND ".join(where) if where else "") + " LIMIT ?")
        rows = db.execute(sql, args + [pool]).fetchall()

    words = [w for w in re.findall(r"[a-z0-9]+", (text or "").lower())]
    target = "-".join(words) if text and not has_arabic(text) else ""
    results = []
    for r in rows:
        d = dict(r)
        score = -d.pop("rank")  # bm25: lower is better
        # exact concept / exact name beat partial matches ("cart" vs "cart-arrow-down")
        if target and d["concept"] == target:
            score += 8
        elif target and d["concept"].startswith(target):
            score += 2
        if parts and not (target and d["concept"].startswith(target)):
            # meaning: same meaning first, then names that use it, then related things
            ctoks = set(d["concept"].split("-"))
            lv = [level(ctoks, d["concept"], p) for p in parts]
            top = 8 if has_arabic(text) else 6  # an English synonym ranks just below the word itself
            if min(lv) == 3 or (len(parts) > 1 and min(lv) >= 2 and ctoks <= set().union(*(p.strong for p in parts))):
                score += top
            elif min(lv) >= 2:
                score += top - 3
            elif min(lv) >= 1:
                score += 1.5
            d["match"] = "related" if min(lv) == 1 else "same"
        if like and like.get("prefix") == d["prefix"]:
            score += 3
        score -= 0.15 * d["concept"].count("-")
        score += 0.5 * math.log(d.pop("concept_sets"))  # widely drawn concepts are the canonical ones
        score += set_prior(d["prefix"], d.pop("set_category"), d.pop("set_total"))
        if like:
            dist = style_distance(like, d)
            d["style_distance"] = round(dist, 2)
            score -= 3.0 * dist
        d["score"] = round(score, 3)
        results.append(d)
    results.sort(key=lambda d: d["score"], reverse=True)
    out, seen = [], {}
    for d in results:
        key = d["prefix"]
        if seen.get(key, 0) >= per_set:
            continue
        seen[key] = seen.get(key, 0) + 1
        out.append(d)
        if len(out) >= limit:
            break
    return out


def families(db: sqlite3.Connection, profile: dict, limit: int = 10, license: str = "commercial",
             min_icons: int = 50) -> list[dict]:
    """Families ranked by how close they look to `profile`.

    When the profile comes from real icons with recognisable names, each one is
    also compared with the *same concept* in every candidate family (a house
    against a house), which is far more precise than comparing averages."""
    sql = ("SELECT f.*, s.name AS set_name, s.license, s.license_tier FROM families f "
           "JOIN sets s ON s.prefix = f.prefix WHERE f.n >= ?")
    args: list = [min_icons]
    if license == "commercial":
        sql += " AND s.license_tier IN ('permissive','attribution')"
    elif license == "permissive":
        sql += " AND s.license_tier = 'permissive'"
    rows = [dict(r) for r in db.execute(sql, args)]
    for r in rows:
        r["style_distance"] = round(style_distance(profile, r), 3)
    rows.sort(key=lambda r: r["style_distance"])
    items = [i for i in profile.get("items", []) if i.get("concepts")]
    if items:
        shortlist = rows[:80]
        for r in shortlist:
            dists = []
            for it in items:
                ph = ",".join("?" * len(it["concepts"]))
                ic = db.execute(f"SELECT * FROM icons WHERE family_id=? AND concept IN ({ph}) LIMIT 1",
                                [r["id"], *it["concepts"]]).fetchone()
                if ic:
                    dists.append(style_distance(it, dict(ic)))
            if len(dists) >= max(1, len(items) // 3):
                r["concept_matches"] = len(dists)
                r["style_distance"] = round(0.3 * r["style_distance"] + 0.7 * (sum(dists) / len(dists)), 3)
            else:
                r["style_distance"] = round(r["style_distance"] + 0.25, 3)
        rows = sorted(shortlist, key=lambda r: r["style_distance"])
    return rows[:limit]
