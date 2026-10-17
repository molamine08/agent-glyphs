#!/usr/bin/env python3
"""How well do Arabic queries find the right icons?

For each query in tests/fixtures/arabic_queries.json, look at the top 10
results (two per library, as the skill returns them). A result counts when
its name uses one of the accepted words.

    python tests/eval_arabic.py [--db data/atlas.db]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas.query import Filters, search  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "atlas.db"))
    ap.add_argument("--show-misses", action="store_true")
    a = ap.parse_args()
    db = sqlite3.connect(a.db)
    db.row_factory = sqlite3.Row
    queries = json.loads((ROOT / "tests" / "fixtures" / "arabic_queries.json").read_text())["queries"]
    found = hit1 = zero = 0
    prec = 0.0
    misses = []
    for q, ok in queries.items():
        ok = set(ok)
        res = search(db, q, Filters(license="any"), limit=10)
        good = [bool(set(r["name"].replace("_", "-").split("-")) & ok or set(r["concept"].split("-")) & ok) for r in res]
        zero += not res
        found += any(good)
        hit1 += bool(good and good[0])
        prec += (sum(good) / len(good)) if good else 0
        if not any(good):
            misses.append(f"{q} -> {', '.join(r['name'] for r in res[:3]) or 'no results'}")
    n = len(queries)
    print(f"{n} Arabic queries")
    print(f"  any right icon in top 10: {100 * found / n:.1f}%")
    print(f"  first result right:       {100 * hit1 / n:.1f}%")
    print(f"  right icons in top 10:    {100 * prec / n:.1f}%")
    print(f"  no results at all:        {100 * zero / n:.1f}%")
    if a.show_misses and misses:
        print("misses:\n  " + "\n  ".join(misses))


if __name__ == "__main__":
    main()
