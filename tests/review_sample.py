#!/usr/bin/env python3
"""Draw a random sample of icons as numbered contact sheets + a CSV of the
labels the index gives them, for a human (or independent agent) to grade.

    python tests/review_sample.py --n 200 --out review/
"""

import argparse
import csv
import io
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import resvg_py  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from atlas import store  # noqa: E402
from atlas.svg import to_svg  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="review")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(store.ensure_index())
    db.row_factory = sqlite3.Row
    ids = [r[0] for r in db.execute("SELECT id FROM icons WHERE style NOT IN ('unknown')")]
    random.seed(a.seed)
    pick = random.sample(ids, a.n)
    rows = [dict(db.execute("SELECT * FROM icons WHERE id=?", (i,)).fetchone()) for i in pick]
    by_set = defaultdict(list)
    for r in rows:
        by_set[r["prefix"]].append(r["name"])
    data = {}
    for p, names in by_set.items():
        for n, d in store.icon_data(p, names).items():
            data[(p, n)] = d
    font = ImageFont.load_default()
    per_sheet, cols, cell = 40, 8, 120
    for s in range(0, len(rows), per_sheet):
        chunk = rows[s:s + per_sheet]
        img = Image.new("RGB", (cols * cell, -(-len(chunk) // cols) * cell), "#EDEDED")
        draw = ImageDraw.Draw(img)
        for k, r in enumerate(chunk):
            x, y = (k % cols) * cell, (k // cols) * cell
            d = data.get((r["prefix"], r["name"]))
            draw.rectangle([x, y, x + cell - 1, y + cell - 1], outline="#DDDDDD")
            draw.text((x + 4, y + 3), str(s + k + 1), fill="#C00000", font=font)
            if not d:
                continue
            svg = to_svg(d, size=None, color="#111")
            svg = svg.replace("<svg ", '<svg width="72" height="72" ', 1)
            png = resvg_py.svg_to_bytes(svg_string=svg, width=72, height=72, skip_system_fonts=True)
            ic = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
            img.paste(ic, (x + 24, y + 22), ic)
        img.save(out / f"sheet_{s // per_sheet + 1:02d}.png")
    with open(out / "labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["no", "icon", "style", "weight", "weight_class", "corners", "cat", "cat2", "style_conf", "corners_conf"])
        for k, r in enumerate(rows, 1):
            w.writerow([k, f"{r['prefix']}:{r['name']}", r["style"], r["weight"], r["weight_class"],
                        r["corners"], r["cat"], r["cat2"], r["style_conf"], r["corners_conf"]])
    print(f"{len(rows)} icons → {out}")


if __name__ == "__main__":
    main()
