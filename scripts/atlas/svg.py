"""Build ready-to-use SVG markup from Iconify icon data."""

from __future__ import annotations

import re


def to_svg(icon: dict, size: int | str | None = 24, color: str | None = None,
           stroke: float | None = None) -> str:
    """Return a standalone <svg>. `stroke` rewrites the stroke width of
    stroke-based icons (value in 24-grid units, so 1.5 means "1.5px at 24px")."""
    body = icon["body"]
    left, top, w, h = icon["left"], icon["top"], icon["width"], icon["height"]
    if stroke is not None and "stroke-width" in body:
        native = stroke * h / 24.0
        body = re.sub(r'stroke-width="[0-9.]+"', f'stroke-width="{native:g}"', body)
    transforms = []
    rot = icon.get("rotate", 0) % 4
    # flips mirror the icon inside its own box: x -> 2*left + w - x
    if icon.get("hFlip"):
        transforms.append(f"translate({2 * left + w} 0) scale(-1 1)")
    if icon.get("vFlip"):
        transforms.append(f"translate(0 {2 * top + h}) scale(1 -1)")
    if rot:
        transforms.append(f"rotate({90 * rot} {left + w / 2} {top + h / 2})")
    if transforms:
        body = f'<g transform="{" ".join(transforms)}">{body}</g>'
    if size is None:
        dims = ""
    else:
        hh = size
        ww = round(float(size) * w / h, 3) if not isinstance(size, str) else size
        dims = f' width="{ww}" height="{hh}"'
    style = f' style="color:{color}"' if color else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
            f'{dims} viewBox="{icon["left"]} {icon["top"]} {w} {h}"{style}>{body}</svg>')
