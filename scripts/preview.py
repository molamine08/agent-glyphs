#!/usr/bin/env python3
"""Render a labelled contact sheet (PNG) so a person or an agent can *see*
candidate icons before choosing.

Examples
  python scripts/preview.py lucide:house tabler:home ph:house-bold -o home.png
  python scripts/preview.py --search "wallet" --style outline -o wallets.png
"""

from __future__ import annotations

import argparse
import io
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import resvg_py  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from atlas import store  # noqa: E402
from atlas.query import Filters, search  # noqa: E402
from atlas.svg import to_svg  # noqa: E402


def render(svg: str, px: int) -> Image.Image:
    png = resvg_py.svg_to_bytes(svg_string=svg, width=px, height=px, skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def sheet(refs: list[str], out: Path, cell: int = 128, cols: int = 6, labels: dict | None = None):
    by_set = defaultdict(list)
    for r in refs:
        p, _, n = r.partition(":")
        by_set[p].append(n)
    icons = {}
    for p, names in by_set.items():
        for n, data in store.icon_data(p, names).items():
            icons[f"{p}:{n}"] = data
    refs = [r for r in refs if r in icons]
    rows = max(1, -(-len(refs) // cols))
    label_h = 30
    W, H = cols * cell, rows * (cell + label_h)
    img = Image.new("RGBA", (W, H), "#F2F2F2")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 10)
    except OSError:
        font = ImageFont.load_default()
    icon_px = int(cell * 0.5)
    for i, ref in enumerate(refs):
        x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
        data = icons[ref]
        svg = to_svg(data, size=None, color="#111111")
        svg = svg.replace("<svg ", f'<svg width="{icon_px}" height="{icon_px}" ', 1)
        ic = render(svg, icon_px)
        img.alpha_composite(ic, (x + (cell - icon_px) // 2, y + (cell - icon_px) // 2))
        text = ref if len(ref) <= 22 else ref[:21] + "…"
        draw.text((x + 4, y + cell + 1), text, fill="#333333", font=font)
        if labels and ref in labels:
            draw.text((x + 4, y + cell + 14), labels[ref][:24], fill="#888888", font=font)
        draw.rectangle([x, y, x + cell - 1, y + cell + label_h - 1], outline="#EEEEEE")
    img.convert("RGB").save(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="*", help="prefix:name")
    ap.add_argument("--search", help="query instead of refs")
    ap.add_argument("--style")
    ap.add_argument("--set", nargs="*", dest="sets")
    ap.add_argument("--limit", type=int, default=32)
    ap.add_argument("-o", "--out", default="preview.png")
    a = ap.parse_args(argv)
    refs, labels = list(a.refs), {}
    if a.search:
        db = store.connect()
        rows = search(db, a.search, Filters(style=a.style, sets=a.sets), limit=a.limit)
        for r in rows:
            ref = f"{r['prefix']}:{r['name']}"
            refs.append(ref)
            w = f" w{r['weight']:.1f}" if r.get("weight") else ""
            labels[ref] = f"{r['style']}{w} {r['corners'] or ''}"
    if not refs:
        raise SystemExit("nothing to preview")
    print(sheet(refs, Path(a.out), labels=labels))


if __name__ == "__main__":
    main()
