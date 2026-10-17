#!/usr/bin/env python3
"""Match my style: find icon families that look like your icons, then fill
the gaps in your set with the closest-looking icons.

Examples
  python scripts/match.py ./my-icons/                     # which families look like my set?
  python scripts/match.py ./my-icons/ --need cart wallet bell "سلة"   # fetch missing icons in that look
  python scripts/match.py lucide --need mosque calendar   # same, using a known family as the reference
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import store  # noqa: E402
from atlas.profile import resolve_like  # noqa: E402
from atlas.query import Filters, families, search, style_distance  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="SVG file, folder of SVGs, set prefix (lucide) or icon (tabler:home)")
    ap.add_argument("--need", nargs="*", default=[], help="concepts you are missing (English or Arabic)")
    ap.add_argument("--license", choices=["commercial", "permissive", "any"], default="commercial")
    ap.add_argument("--families", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    db = store.connect()
    prof = resolve_like(db, a.reference)
    fams = families(db, prof, limit=a.families, license=a.license)
    result = {"profile": prof, "families": fams, "picks": {}}

    for concept in a.need:
        # 1) best: the concept exists in one of the closest families
        pick = None
        for fam in fams:
            # inside a chosen family, meaning decides; the look is already right
            rows = search(db, concept, Filters(sets=[fam["prefix"]], license=a.license),
                          limit=10, per_set=10)
            rows = [r for r in rows if r["family_id"] == fam["id"]]
            if rows:
                pick = {**rows[0], "via": "close family",
                        "style_distance": round(style_distance(prof, rows[0]), 2)}
                break
        # 2) otherwise: any icon with that meaning, ranked by visual distance
        if pick is None:
            rows = search(db, concept, Filters(license=a.license), limit=5, per_set=1, like=prof)
            if rows:
                pick = {**rows[0], "via": "nearest look"}
        result["picks"][concept] = pick

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
        return
    p = prof
    print(f"your style: {p['style']}, weight {p['weight'] and round(p['weight'], 2)}, "
          f"roundness {p['roundness'] and round(p['roundness'], 2)}, curviness {p['curviness'] and round(p['curviness'], 2)}")
    print("\nclosest families (lower = closer):")
    for f in fams:
        print(f"  {f['style_distance']:5.2f}  {f['prefix']}{':' + f['variant'] if f['variant'] else ''}  "
              f"— {f['label']}  ({f['n']} icons, {f['license']})")
    if a.need:
        print("\npicks for what you need:")
        for concept, r in result["picks"].items():
            if r:
                print(f"  {concept:<16} → {r['prefix']}:{r['name']}  (match {r.get('style_distance')}, {r['via']})")
            else:
                print(f"  {concept:<16} → nothing found")
        refs = " ".join(f"{r['prefix']}:{r['name']}" for r in result["picks"].values() if r)
        if refs:
            print(f"\nexport them:  python scripts/get.py {refs}")


if __name__ == "__main__":
    main()
