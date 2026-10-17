"""Meaning-aware query expansion, Arabic and English.

A query word is matched to concept groups (scripts/atlas/concepts.json), each
listing the Arabic words people type for one meaning (formal, dialect and
loanwords), its English synonyms, and closely related icon-name tokens:

    {"ar": ["مسلم", "إسلام", "إسلامي"], "en": ["islam", "muslim"],
     "rel": ["mosque", "crescent", "quran", "kaaba", "prayer"]}

expand("مسلمين") then returns, per query word, the tokens that mean the same
thing ("strong") and the tokens that are closely related ("related"). Search
ranks icons whose names use strong tokens first and related ones after.

Arabic words are compared after normalisation (norm_ar) and light stemming:
common prefixes (و ف ب ك ل) and suffixes (ات ون ين ان ية ي ...) are removed, so
"الإسلامية", "مسلمين" and "بالسلة" reach the same groups as "إسلام", "مسلم", "سلة".
The same rules are mirrored in web/worker.js.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .semantics import has_arabic, norm_ar, terms

CONCEPTS_PATH = Path(__file__).with_name("concepts.json")
# hand-written groups kept apart from the generated ones (e.g. the Islamic glyphs)
CURATED_PATH = Path(__file__).with_name("concepts_curated.json")

AR_PREFIXES = ("و", "ف", "ب", "ك", "ل")
# longest first; a suffix is only removed when at least 3 letters remain
AR_SUFFIXES = ("يات", "ات", "ون", "ين", "ان", "يه", "ها", "هم", "كم", "نا", "ه", "ي")
EN_SUFFIXES = (("ies", "y"), ("es", ""), ("s", ""), ("ing", ""), ("ed", ""))


def ar_forms(word: str) -> list[str]:
    """The word itself first, then lighter-to-heavier stripped forms."""
    w = norm_ar(word)
    if not w:
        return []
    out = [w]
    bases = [w]
    if len(w) >= 4 and w[0] in AR_PREFIXES:
        b = norm_ar(w[1:])  # "وال" / "بال" already handled by norm_ar
        if len(b) >= 3:
            bases.append(b)
            out.append(b)
    for b in bases:
        for s in AR_SUFFIXES:
            if b.endswith(s) and len(b) - len(s) >= 3:
                out.append(b[: -len(s)])
                break
    seen, res = set(), []
    for f in out:
        if f not in seen:
            seen.add(f)
            res.append(f)
    return res


def en_forms(word: str) -> list[str]:
    w = word.lower()
    out = [w]
    for suf, rep in EN_SUFFIXES:
        # "-ing"/"-ed" need a longer stem: "rating" is not "rat", "coding" not "cod"
        if w.endswith(suf) and len(w) - len(suf) >= (4 if suf in ("ing", "ed") else 3):
            out.append(w[: -len(suf)] + rep)
    return list(dict.fromkeys(out))


@lru_cache(maxsize=1)
def groups() -> list[dict]:
    """Concept groups plus the one-word translations of terms_ar.json."""
    data = json.loads(CURATED_PATH.read_text()) if CURATED_PATH.exists() else []
    data += json.loads(CONCEPTS_PATH.read_text()) if CONCEPTS_PATH.exists() else []
    out = [{"ar": g.get("ar", []), "en": [e.lower() for e in g.get("en", [])],
            "rel": [r.lower() for r in g.get("rel", [])]} for g in data]
    for tok, e in terms().items():
        if e.get("ar"):
            out.append({"ar": e["ar"], "en": [tok], "rel": []})
    return out


@lru_cache(maxsize=1)
def tables() -> tuple[dict, dict, dict]:
    """(arabic exact form -> group ids, arabic stem -> group ids, english word -> group ids)."""
    ar_exact: dict[str, list[int]] = {}
    ar_stem: dict[str, list[int]] = {}
    en: dict[str, list[int]] = {}
    for gi, g in enumerate(groups()):
        for w in g["ar"]:
            forms = ar_forms(w) if " " not in w.strip() else [norm_ar(w)]
            if not forms:
                continue
            ar_exact.setdefault(forms[0], []).append(gi)
            for f in forms[1:]:
                ar_stem.setdefault(f, []).append(gi)
        for w in g["en"]:
            en.setdefault(w, []).append(gi)
    return ar_exact, ar_stem, en


@dataclass
class Part:
    text: str                      # the query word or phrase as matched
    strong: set = field(default_factory=set)
    related: set = field(default_factory=set)
    groups: list = field(default_factory=list)


def _lookup_ar(phrase: str) -> list[int]:
    ar_exact, ar_stem, _ = tables()
    if " " in phrase:
        return ar_exact.get(norm_ar(phrase), [])
    forms = ar_forms(phrase)
    for f in forms:
        if f in ar_exact:
            return ar_exact[f]
    for f in forms:
        if f in ar_stem:
            return ar_stem[f]
    return []


def _lookup_en(word: str) -> list[int]:
    _, _, en = tables()
    for f in en_forms(word):
        if f in en:
            return en[f]
    return []


def expand(text: str) -> list[Part]:
    """Split a query into parts (longest known phrase first) and expand each."""
    words = re.findall(r"[\w؀-ۿ]+", text.lower())
    parts: list[Part] = []
    i = 0
    while i < len(words):
        hit = None
        for n in (5, 4, 3, 2):  # multi-word Arabic phrases such as "لوحة التحكم", "صلى الله عليه وسلم"
            if i + n <= len(words) and all(has_arabic(w) for w in words[i:i + n]):
                gids = _lookup_ar(" ".join(words[i:i + n]))
                if gids:
                    hit = (" ".join(words[i:i + n]), gids, n)
                    break
        if not hit:
            w = words[i]
            gids = _lookup_ar(w) if has_arabic(w) else _lookup_en(w)
            hit = (w, gids, 1)
        text_i, gids, n = hit
        p = Part(text_i, groups=gids)
        for gi in gids:
            g = groups()[gi]
            p.strong.update(g["en"])
            p.related.update(g["rel"])
        if not has_arabic(text_i):
            p.strong.add(text_i)
            p.strong.update(en_forms(text_i))
        p.related -= p.strong
        parts.append(p)
        i += n
    return parts


def level(concept_tokens: set, concept: str, part: Part) -> int:
    """3 = the icon is exactly this meaning, 2 = its name uses it,
    1 = its name uses a closely related word, 0 = no link."""
    if concept in part.strong:
        return 3
    if concept_tokens & part.strong:
        return 2
    if concept in part.related or concept_tokens & part.related:
        return 1
    return 0


def related_terms(parts: list[Part], limit: int = 8) -> list[str]:
    """Related tokens to show as 'also includes' chips."""
    out = []
    for p in parts:
        for gi in p.groups:
            for r in groups()[gi]["rel"]:
                if r not in out and r not in p.strong:
                    out.append(r)
    return out[:limit]
