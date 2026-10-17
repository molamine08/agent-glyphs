#!/usr/bin/env python3
"""Does looking at icons improve their categories? Decide with evidence.

Uses icons whose categories were judged by an independent reviewer
(tests/fixtures/gold_categories.json). The vision weight is chosen on the
'tune' half and reported on the untouched 'test' half. It is only adopted
when it helps on BOTH halves; otherwise it stays 0 (names only).

    python tests/eval_vision.py --src .work/iconify [--apply]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas.classify import concept_of  # noqa: E402
from atlas.semantics import categories_for, map_set_category  # noqa: E402
from atlas.vision import MODEL, Scorer, _icon  # noqa: E402

WEIGHTS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--apply", action="store_true", help="write the chosen weight to config.json")
    ap.add_argument("--report", default=str(ROOT / "VISION_EVAL.md"))
    a = ap.parse_args()
    gold = json.loads((ROOT / "tests" / "fixtures" / "gold_categories.json").read_text())["icons"]
    src = Path(a.src)
    sets, rows = {}, []
    for ref in gold:
        prefix, name = ref.split(":", 1)
        if prefix not in sets:
            p = src / f"{prefix}.json"
            sets[prefix] = json.loads(p.read_text()) if p.exists() else None
        d = sets[prefix]
        if not d or name not in d["icons"]:
            continue
        given = None
        for label, names in (d.get("categories") or {}).items():
            if name in names and map_set_category(label):
                given = given or map_set_category(label)
        rows.append({"ref": ref, "prefix": prefix, "name": name, "set_cat": d.get("info", {}).get("category"),
                     "given": given, "icon": _icon(d, name), **gold[ref]})
    scorer = Scorer()
    for k in range(0, len(rows), 32):
        chunk = rows[k:k + 32]
        for r, sc in zip(chunk, scorer.score([r["icon"] for r in chunk])):
            r["vision"] = sc

    def accuracy(weight, split):
        sel = [r for r in rows if r["split"] == split]
        prim = either = 0
        for r in sel:
            v = {c: weight * p for c, p in r["vision"]} if weight else {}
            cats = categories_for(r["name"], r["set_cat"], r["given"], r["prefix"], v)
            prim += cats[0] in r["ok"]
            either += any(c in r["ok"] for c in cats)
        return 100 * prim / len(sel), 100 * either / len(sel), len(sel)

    table = {w: {"tune": accuracy(w, "tune"), "test": accuracy(w, "test")} for w in WEIGHTS}
    base = table[0.0]
    best = max(WEIGHTS, key=lambda w: (table[w]["tune"][0], table[w]["tune"][1], -w))
    helps = lambda s: table[best][s][0] >= base[s][0] + 1.0 and table[best][s][1] >= base[s][1] - 0.5  # noqa: E731
    chosen = best if best > 0 and helps("tune") and helps("test") else 0.0

    lines = ["# Vision model evaluation", "",
             f"Model: CLIP {MODEL[0]} ({MODEL[1]}), "
             f"{len(rows)} reviewer-graded icons.", "",
             "| vision weight | tune: primary | tune: either | test: primary | test: either |",
             "|---|---|---|---|---|"]
    for w in WEIGHTS:
        t, s = table[w]["tune"], table[w]["test"]
        mark = " **chosen**" if w == chosen else ""
        lines.append(f"| {w}{mark} | {t[0]:.1f}% | {t[1]:.1f}% | {s[0]:.1f}% | {s[1]:.1f}% |")
    verdict = (f"Adopted weight {chosen}: test accuracy {base['test'][0]:.1f}% → {table[chosen]['test'][0]:.1f}% (primary)."
               if chosen else "Not adopted: the vision votes did not improve both halves. Names only (weight 0).")
    lines += ["", verdict]
    report = "\n".join(lines) + "\n"
    Path(a.report).write_text(report)
    print(report)
    if a.apply:
        cfg_path = ROOT / "config.json"
        cfg = json.loads(cfg_path.read_text())
        cfg["vision_weight"] = chosen
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")


if __name__ == "__main__":
    main()
