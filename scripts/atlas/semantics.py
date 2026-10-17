"""Meaning layer: concept, content category and bilingual search terms."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .classify import concept_of, name_tokens
from .taxonomy import CATEGORIES, STYLE_TOKENS

DICT_PATH = Path(__file__).with_name("terms_ar.json")

# Category names used by the icon sets themselves → our taxonomy.
SET_CATEGORY_RULES = [
    (r"arrow|direction", "arrows"),
    (r"emoji|smil|\bfaces?\b|emotion", "emoji"),
    (r"\bflags?\b|countr", "flags"),
    (r"brand|logo|\bsocial media\b", "brands"),
    (r"weather|climate", "weather"),
    (r"money|financ|bank|payment|currenc|crypto", "finance"),
    (r"commerce|shop|retail|\bstores?\b", "commerce"),
    (r"people|\busers?\b|person|account|avatar|gender|human", "people"),
    (r"health|medic|hospital|fitness|\bbody\b", "health"),
    (r"\bfood|drink|kitchen|cook|restaurant", "food"),
    (r"transport|vehicle|transit|\bcars?\b|aviation|logistic|automotive", "transport"),
    (r"\bmaps?\b|location|\bplaces?\b|\bgeo|navigation|travel", "maps"),
    (r"nature|animal|plant|ecolog|environment|agricult", "nature"),
    (r"building|architect|construct|real.?estate|\bcity", "buildings"),
    (r"\bhome\b|household|furniture|appliance", "home"),
    (r"security|privacy|\block|protect", "security"),
    (r"\bchat|message|\bmail|communicat|\bphone|\bcall|notification|contact", "communication"),
    (r"\bmedia\b|audio|video|music|photo|image|camera|movie|multimedia", "media"),
    (r"\bfiles?\b|document|folder|archive", "files"),
    (r"\btext\b|typograph|\bfonts?\b|editor|format|writing", "text"),
    (r"design|\bdraw|paint|\barts?\b|colou?r|graphic", "design"),
    (r"device|hardware|computer|electronic|mobile|gadget|android", "devices"),
    (r"develop|\bcode|programm|devops|dev.?tool|software|\bgit\b|database", "development"),
    (r"chart|graph|\bdata\b|analytic|statistic|report", "data"),
    (r"cloud|network|connect|wifi|internet|server|signal", "network"),
    (r"\bai\b|artificial|agent|robot|automat|\brag\b|machine learning", "ai"),
    (r"\btime\b|calendar|\bdate|clock|schedul", "time"),
    (r"educat|school|science|learn|\bmath|\bbooks?\b|\blab\b", "education"),
    (r"sport|\bgames?\b|gaming|leisure|entertainment|activit|hobb|\btoys?\b", "sports"),
    (r"relig|holiday|celebrat|culture|festiv|christmas|halloween", "culture"),
    (r"business|office|\bwork|organi[sz]|management|marketing|company", "business"),
    (r"alert|status|warning|feedback|indicator", "status"),
    (r"\bactions?\b|\bedit|operation", "actions"),
    (r"\btools?\b|setting|system|control|configur", "tools"),
    (r"shape|symbol|geometr|\bsigns?\b", "shapes"),
    (r"interface|\bui\b|essential|layout|\bgrid|window|\bmenu|\bforms?\b", "interface"),
]

SET_LEVEL_CATEGORY = {"Emoji": "emoji", "Flags / Maps": "flags", "Logos": "brands"}

_AR_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي", "ـ": None})


def norm_ar(text: str) -> str:
    """Normalise Arabic for matching: strip diacritics, unify alef/ya/ta
    marbuta and drop the definite article, so "السلة" matches "سلة"."""
    text = "".join(ch for ch in unicodedata.normalize("NFC", text) if not unicodedata.combining(ch))
    text = re.sub(r"[ً-ْٰ]", "", text).translate(_AR_NORM).lower()
    words = []
    for w in text.split():
        for art in ("وال", "بال", "لل", "ال"):
            if w.startswith(art) and len(w) - len(art) >= 2:
                w = w[len(art):]
                break
        words.append(w)
    return " ".join(words)


def has_arabic(text: str) -> bool:
    return bool(re.search(r"[؀-ۿ]", text))


@lru_cache(maxsize=1)
def terms() -> dict:
    return json.loads(DICT_PATH.read_text()) if DICT_PATH.exists() else {}


@lru_cache(maxsize=1)
def reverse_terms() -> dict:
    """normalised Arabic phrase -> English tokens that use it."""
    rev: dict = {}
    for tok, e in terms().items():
        for w in e.get("ar", []):
            rev.setdefault(norm_ar(w), []).append(tok)
    return rev


def arabic_to_tokens(text: str) -> tuple[set, list[set]]:
    """Exact-phrase tokens, and per-word token sets, for an Arabic query."""
    rev = reverse_terms()
    q = norm_ar(text)
    exact = set(rev.get(q, []))
    per_word = [set(rev.get(w, [])) | {t for k, v in rev.items() if k.split()[:1] == [w] for t in v}
                for w in q.split()]
    return exact, per_word


def map_set_category(label: str) -> str | None:
    low = label.lower()
    for pat, cat in SET_CATEGORY_RULES:
        if re.search(pat, low):
            return cat
    return None


def lookup(tok: str):
    """Dictionary entry for a name word, tolerating plurals ("tags") and
    glued compounds ("spiderchart" -> "chart"). Returns (entry, confidence)."""
    t = terms()
    if tok in t:
        return t[tok], 1.0
    for cand in (tok[:-1] if tok.endswith("s") else None, tok[:-2] if tok.endswith("es") else None):
        if cand and cand in t:
            return t[cand], 1.0
    if len(tok) >= 7:
        for cut in range(3, len(tok) - 3):
            tail = tok[cut:]
            if tail in t and t[tail].get("kind") == "noun":
                return t[tail], 0.6
    return None, 0.0


KIND_WEIGHT = {"noun": 2.0, "brand": 2.0, "action": 1.0, "modifier": 0.5, "code": 0.5}


def categories_for(name: str, set_cat: str | None, given: str | None, prefix: str = "",
                   extra_votes: dict | None = None) -> list[str]:
    """Content categories, best first (at most two).

    Every known word of the name votes for its category (nouns count most,
    rare words more than common ones); the set's own label for the icon
    votes too. Whole-set categories (emoji, logos) win outright."""
    if set_cat in ("Emoji", "Logos"):
        return [SET_LEVEL_CATEGORY[set_cat]]
    if re.search(r"brand|logo", prefix) or name.startswith("brand-"):
        return ["brands"]
    t = terms()
    votes: dict[str, float] = {}
    for tok in name_tokens(name):
        tok = re.sub(r"\d+$", "", tok)
        if tok in STYLE_TOKENS:
            continue
        e, scale = lookup(tok)
        if not e or e.get("cat") not in CATEGORIES or e["cat"] == "other":
            continue
        w = scale * KIND_WEIGHT.get(e.get("kind"), 0.0) / math.log10(e.get("n", 1) + 10)
        votes[e["cat"]] = votes.get(e["cat"], 0.0) + w
    if given:
        votes[given] = votes.get(given, 0.0) + 0.9
    for c, w in (extra_votes or {}).items():  # e.g. what a vision model sees
        if c in CATEGORIES and c != "other":
            votes[c] = votes.get(c, 0.0) + w
    if not votes:
        if set_cat == "Programming":
            return ["development"]
        if set_cat in SET_LEVEL_CATEGORY:
            return [SET_LEVEL_CATEGORY[set_cat]]
        return ["other"]
    ranked = sorted(votes.items(), key=lambda kv: -kv[1])
    out = [ranked[0][0]]
    if len(ranked) > 1 and ranked[1][1] >= 0.5 * ranked[0][1]:
        out.append(ranked[1][0])
    return out


def category_for(name: str, set_cat: str | None, given: str | None, prefix: str = "") -> str:
    return categories_for(name, set_cat, given, prefix)[0]


def arabic_terms(name: str) -> list[str]:
    out: list[str] = []
    for tok in name_tokens(name):
        tok = re.sub(r"\d+$", "", tok)
        if tok in STYLE_TOKENS:
            continue
        e, _ = lookup(tok)
        for w in (e or {}).get("ar", []):
            if w not in out:
                out.append(w)
    return out


__all__ = ["concept_of", "category_for", "arabic_terms", "map_set_category", "norm_ar"]
