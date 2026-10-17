#!/usr/bin/env python3
"""Export icons as SVG files (or React components) ready to drop into a project.

Examples
  python scripts/get.py lucide:house tabler:shopping-cart --out src/icons
  python scripts/get.py ph:bell --stroke 1.5 --size 20 --color "#0F766E"
  python scripts/get.py lucide:search --format tsx --out src/components/icons
  python scripts/get.py lucide:arrow-right --mirror        # RTL: points left
  python scripts/get.py mdi:home --stdout
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import store  # noqa: E402
from atlas.svg import to_svg  # noqa: E402


def component_name(name: str) -> str:
    base = "".join(p.capitalize() for p in re.split(r"[^a-zA-Z0-9]+", name) if p)
    return ("Icon" + base) if not base[:1].isalpha() else base + "Icon"


def jsx(svg: str, name: str, ts: bool) -> str:
    inner = re.sub(r'\s(width|height)="[^"]*"', "", svg)
    inner = re.sub(r"([a-z]+)-([a-z])([a-z-]*)=", lambda m: m.group(1) + m.group(2).upper()
                   + re.sub(r"-([a-z])", lambda n: n.group(1).upper(), m.group(3)) + "=", inner)
    inner = inner.replace("xlink:href", "xlinkHref").replace("xmlns:xlink", "xmlnsXlink")
    inner = re.sub(r'style="color:([^"]*)"', r'style={{ color: "\1" }}', inner)
    inner = inner.replace("<svg ", "<svg width={size} height={size} {...props} ", 1)
    props = "{ size = 24, ...props }: { size?: number | string } & React.SVGProps<SVGSVGElement>" if ts \
        else "{ size = 24, ...props }"
    head = 'import * as React from "react";\n\n' if ts else ""
    return f"{head}export default function {component_name(name)}({props}) {{\n  return (\n    {inner}\n  );\n}}\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="+", help="prefix:name")
    ap.add_argument("--out", default="icons")
    ap.add_argument("--size", default="24", help="px, or 'none' to keep only the viewBox")
    ap.add_argument("--color", help="sets CSS color; icons use currentColor")
    ap.add_argument("--stroke", type=float, help="new stroke width (24-grid units), stroke icons only")
    ap.add_argument("--mirror", action="store_true", help="flip horizontally (directional icons in RTL/Arabic UIs)")
    ap.add_argument("--format", choices=["svg", "jsx", "tsx"], default="svg")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing files")
    a = ap.parse_args(argv)

    by_set = defaultdict(list)
    for ref in a.refs:
        prefix, _, name = ref.partition(":")
        if not name:
            raise SystemExit(f"'{ref}': use prefix:name, e.g. lucide:house")
        by_set[prefix].append(name)

    db = store.connect()
    size = None if a.size == "none" else a.size
    out = Path(a.out)
    notes = []
    for prefix, names in by_set.items():
        found = store.icon_data(prefix, names)
        s = db.execute("SELECT * FROM sets WHERE prefix=?", (prefix,)).fetchone()
        for name in names:
            if name not in found:
                print(f"! {prefix}:{name} not found", file=sys.stderr)
                continue
            data = found[name]
            if a.mirror:
                data = {**data, "hFlip": not data.get("hFlip", False)}
            svg = to_svg(data, size=size, color=a.color, stroke=a.stroke)
            text = svg if a.format == "svg" else jsx(svg, name, a.format == "tsx")
            if a.stdout:
                print(text)
            else:
                out.mkdir(parents=True, exist_ok=True)
                ext = a.format if a.format != "svg" else "svg"
                fname = f"{prefix}-{name}.{ext}" if a.format == "svg" else f"{component_name(name)}.{ext}"
                (out / fname).write_text(text)
                print(f"wrote {out / fname}")
            if s:
                notes.append((f"{prefix}:{name}", s["name"], s["author"], s["license"], s["license_url"], s["license_tier"]))
    if notes and not a.stdout:
        att = out / "ATTRIBUTION.md"
        header = ["# Icon attributions", "", "| Icon | Set | Author | License | Credit required |",
                  "|---|---|---|---|---|"]
        old = [ln for ln in att.read_text().splitlines() if ln.startswith("| ") and not ln.startswith("| Icon")] \
            if att.exists() else []
        new = [f"| {i} | {n} | {au} | [{lic}]({url}) | {'no' if tier == 'permissive' else 'YES'} |"
               for i, n, au, lic, url, tier in notes]
        att.write_text("\n".join(header + list(dict.fromkeys(old + new))) + "\n")
        need = [i for i, *_, tier in notes if tier != "permissive"]
        if need:
            print(f"note: credit the author for {', '.join(need)} — see {att}")


if __name__ == "__main__":
    main()
