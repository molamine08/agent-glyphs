"""Search and style matching over atlas.db."""

from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass

from .semantics import arabic_to_tokens, has_arabic, norm_ar

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
    style: str | None = None
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


def _fts_query(text: str) -> str:
    """Prefix-match every word; Arabic goes to the ar column."""
    parts = []
    for word in re.findall(r"[\w؀-ۿ]+", text.lower()):
        if has_arabic(word):
            word = norm_ar(word)
            if word:
                parts.append(f'ar:"{word}"*')
        else:
            parts.append(f'{{en extra}}:"{word}"*')
    return " AND ".join(parts)


def search(db: sqlite3.Connection, text: str | None, f: Filters, limit: int = 20,
           per_set: int = 2, like: dict | None = None) -> list[dict]:
    where, args = [], []
    if f.style:
        where.append("i.style = ?"); args.append(f.style)
    if f.weight is not None:
        where.append("i.weight BETWEEN ? AND ?"); args += [f.weight - f.weight_tol, f.weight + f.weight_tol]
    for col, val in (("weight_class", f.weight_class), ("corners", f.corners), ("curves", f.curves),
                     ("contrast_class", f.contrast), ("container", f.container),
                     ("complexity", f.complexity)):
        if val:
            where.append(f"i.{col} = ?"); args.append(val)
    if f.cat:
        where.append("(i.cat = ? OR i.cat2 = ?)"); args += [f.cat, f.cat]
    if f.sets:
        where.append(f"i.prefix IN ({','.join('?' * len(f.sets))})"); args += f.sets
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
    q = _fts_query(text) if text else ""
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
    target = "-".join(words)
    ar_exact, ar_words = arabic_to_tokens(text) if text and has_arabic(text) else (set(), [])
    ar_union = set().union(*ar_words) if ar_words else set()
    results = []
    for r in rows:
        d = dict(r)
        score = -d.pop("rank")  # bm25: lower is better
        # exact concept / exact name beat partial matches ("cart" vs "cart-arrow-down")
        if target and d["concept"] == target:
            score += 8
        elif target and d["concept"].startswith(target):
            score += 2
        if ar_words:
            ctoks = set(d["concept"].split("-"))
            if d["concept"] in ar_exact:
                score += 8
            elif ctoks <= ar_union and all(ctoks & w for w in ar_words if w):
                score += 6
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
