#!/usr/bin/env python3
"""Search ~400k open icons by meaning (English or Arabic) and by style.

Examples
  python scripts/search.py "shopping cart"
  python scripts/search.py "سلة تسوق" --style outline --weight 1.5 --corners rounded
  python scripts/search.py "bell" --like lucide          # rank by visual match to Lucide
  python scripts/search.py "wallet" --like ./my-icon.svg  # rank by match to your own icon
  python scripts/search.py --cat finance --style filled --limit 40
  python scripts/search.py "صلى الله عليه وسلم" --kind glyph   # Unicode characters: ﷺ U+FDFA
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import store  # noqa: E402
from atlas.query import Filters, search  # noqa: E402
from atlas.profile import resolve_like  # noqa: E402

SHOW = ["prefix", "name", "family", "style", "weight", "weight_class", "corners", "curves",
        "contrast_class", "density_class", "container", "cat", "license", "license_tier"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="what the icon means, English or Arabic")
    ap.add_argument("--style", choices=["outline", "filled", "duotone", "multicolor", "mixed"])
    ap.add_argument("--weight", type=float, help="stroke width on a 24px grid, e.g. 1.5 or 2")
    ap.add_argument("--weight-tol", type=float, default=0.3)
    ap.add_argument("--weight-class", choices=["hairline", "thin", "light", "regular", "medium", "bold", "heavy", "solid"])
    ap.add_argument("--corners", choices=["rounded", "mixed", "sharp"])
    ap.add_argument("--curves", choices=["geometric", "balanced", "organic"])
    ap.add_argument("--contrast", choices=["monoline", "moderate", "high"])
    ap.add_argument("--container", choices=["circle", "square", "none"])
    ap.add_argument("--complexity", choices=["simple", "medium", "detailed"])
    ap.add_argument("--cat", help="content category key (see SKILL.md)")
    ap.add_argument("--set", nargs="*", dest="sets", help="limit to icon set prefixes, e.g. lucide tabler")
    ap.add_argument("--license", choices=["commercial", "permissive", "any"], default="commercial")
    ap.add_argument("--min-conf", choices=["high", "medium"])
    ap.add_argument("--like", help="family/set (lucide, ph:bold), an icon (tabler:home) or an SVG file")
    ap.add_argument("--kind", choices=["icon", "glyph"], help="only icons (SVG) or only glyphs (Unicode characters)")
    ap.add_argument("--per-set", type=int, default=2, help="max results per icon set (variety)")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true", help="full JSON output")
    a = ap.parse_args(argv)

    db = store.connect()
    like = resolve_like(db, a.like) if a.like else None
    f = Filters(style=a.style, weight=a.weight, weight_tol=a.weight_tol, weight_class=a.weight_class,
                corners=a.corners, curves=a.curves, contrast=a.contrast, container=a.container,
                complexity=a.complexity, cat=a.cat, sets=a.sets, license=a.license, min_conf=a.min_conf, kind=a.kind)
    rows = search(db, a.query, f, limit=a.limit, per_set=a.per_set, like=like)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    if not rows:
        print("no match — try fewer filters, another synonym, or --license any")
        return
    for r in rows:
        if r.get("kind") == "glyph":
            print(f"{r['prefix']}:{r['name']:<34} glyph  {r['char']}  {r['codepoint']:<8} HTML {r['html']:<10} "
                  f"(a Unicode character: paste it as text, like an emoji)")
            continue
        w = f"{r['weight']:.2f}" if r.get("weight") is not None else "-"
        dist = f"  match={r['style_distance']}" if "style_distance" in r else ""
        print(f"{r['prefix']}:{r['name']:<34} {r['style'] or '-':<10} w={w:<5} {r['corners'] or '-':<8} "
              f"{r['cat']:<13} {r['license']} ({r['license_tier']}){dist}")


if __name__ == "__main__":
    main()
