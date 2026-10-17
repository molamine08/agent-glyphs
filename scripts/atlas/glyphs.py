"""Glyphs: Unicode characters offered next to the icons.

A glyph is a character such as ﷺ, ۞ or 🕌, not a drawing. Agents paste it into
text like an emoji (or write its code point), so a glyph has no SVG, stroke or
corners: only the character, its code point and the words it answers to. The
catalogue is sources/glyphs/unicode.json (scripts/make_glyph_catalog.py).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .concepts import Part, ar_forms
from .semantics import has_arabic, norm_ar

CATALOG = Path(__file__).resolve().parents[2] / "sources" / "glyphs" / "unicode.json"
PREFIX = "unicode"
LICENSE = "Unicode character (no licence needed; the font that draws it has its own)"


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    if not CATALOG.exists():
        return []
    out = []
    for g in json.loads(CATALOG.read_text()):
        words = [norm_ar(a) for a in g.get("ar", [])]
        forms = {f for w in words for word in w.split() for f in ar_forms(word)}
        out.append({**g, "_tags": set(g.get("en", [])) | {g["name"]}, "_ar": words, "_forms": forms})
    return out


def by_name(name: str) -> dict | None:
    name = name.split(":", 1)[-1]
    for g in catalog():
        if g["name"] == name or g["char"] == name or g["cp"].lower() == name.lower():
            return g
    return None


def _level(g: dict, p: Part) -> int:
    """5 = the very Arabic words, 4 = its name is this meaning, 3 = it answers to a
    word of the same meaning, 2 = it includes the word, 1 = closely related, 0 = no link."""
    ar = has_arabic(p.text)
    if ar and norm_ar(p.text) in g["_ar"]:
        return 5
    if g["name"] in p.strong or (not ar and p.text in g["_tags"]):
        return 4
    if p.strong & g["_tags"]:
        return 3
    if ar:
        words = norm_ar(p.text).split()
        if words and all(set(ar_forms(w)) & g["_forms"] for w in words):
            return 2
    elif len(p.text) >= 3 and any(t.startswith(p.text) for t in g["_tags"]):
        return 2
    if p.related & g["_tags"]:
        return 1
    return 0


def search(text: str, parts: list[Part], limit: int = 6) -> list[dict]:
    """Glyphs for a query, best first. Closely related glyphs are left out as soon
    as one glyph matches the meaning itself."""
    out = []
    for g in catalog():
        if g["char"] in text:
            lv = 6
        elif parts:
            lv = min(_level(g, p) for p in parts)
        else:
            lv = 0
        if lv:
            overlap = sum(len(p.strong & g["_tags"]) for p in parts)
            out.append((lv, overlap, -len(g["name"]), g))
    out.sort(key=lambda x: x[:3], reverse=True)
    if out and out[0][0] >= 2:
        out = [x for x in out if x[0] >= 2]
    return [public(g, lv) for lv, _, _, g in out[:limit]]


def public(g: dict, lv: int = 4) -> dict:
    """lv: 4+ = the glyph is exactly what was asked for (it is shown before icons)."""
    return {
        "kind": "glyph", "prefix": PREFIX, "name": g["name"], "concept": g["name"], "char": g["char"], "codepoint": g["cp"],
        "unicode_name": g["unicode_name"], "html": "".join(f"&#x{ord(c):X};" for c in g["char"]),
        "css": "".join(f"\\{ord(c):X}" for c in g["char"]), "cat": g.get("cat"), "license": LICENSE,
        "license_tier": "permissive", "match": "related" if lv == 1 else "same", "level": lv,
    }
