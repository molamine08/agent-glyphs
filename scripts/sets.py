#!/usr/bin/env python3
"""List icon libraries (families) with their measured style and licence.

  python scripts/sets.py                      # all libraries
  python scripts/sets.py --search material    # filter by name/prefix
  python scripts/sets.py --style outline --corners rounded --weight 1.5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import store  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search")
    ap.add_argument("--style")
    ap.add_argument("--corners")
    ap.add_argument("--weight", type=float)
    ap.add_argument("--license", choices=["commercial", "permissive", "any"], default="any")
    ap.add_argument("--min-icons", type=int, default=20)
    a = ap.parse_args(argv)
    db = store.connect()
    sql = ("SELECT f.*, s.name AS set_name, s.license, s.license_tier, s.grid FROM families f "
           "JOIN sets s ON s.prefix=f.prefix WHERE f.n >= ?")
    args: list = [a.min_icons]
    if a.search:
        sql += " AND (f.prefix LIKE ? OR s.name LIKE ?)"; args += [f"%{a.search}%"] * 2
    if a.style:
        sql += " AND f.style = ?"; args.append(a.style)
    if a.corners:
        sql += " AND f.corners = ?"; args.append(a.corners)
    if a.weight is not None:
        sql += " AND f.weight BETWEEN ? AND ?"; args += [a.weight - 0.25, a.weight + 0.25]
    if a.license == "commercial":
        sql += " AND s.license_tier IN ('permissive','attribution')"
    elif a.license == "permissive":
        sql += " AND s.license_tier = 'permissive'"
    sql += " ORDER BY f.prefix, f.n DESC"
    for r in db.execute(sql, args):
        ref = r["prefix"] + (f":{r['variant']}" if r["variant"] else "")
        w = f"{r['weight']:.2f}" if r["weight"] else "-"
        print(f"{ref:<34} {r['n']:>6}  {r['style'] or '-':<10} w={w:<5} {r['corners'] or '-':<8} "
              f"{r['license']} ({r['license_tier']})  {r['set_name']}")


if __name__ == "__main__":
    main()
