"""Geometric analysis of a single icon.

Every metric is computed from the rendered icon, so icons whose strokes were
converted to filled outlines are measured the same way as true stroke icons.
All lengths are normalised to a 24-unit grid (the size most UI icon sets are
drawn on), so a value of 2.0 means "looks like a 2px stroke on a 24px icon"
whatever the source viewBox is.
"""

from __future__ import annotations

import io
import math
import re

import numpy as np
import resvg_py
from PIL import Image
from scipy import ndimage
from scipy.spatial import ConvexHull
from skimage.measure import find_contours
from skimage.morphology import skeletonize

RENDER = 120  # px on the longest side; 5 px per unit on a 24 grid

# ---------------------------------------------------------------------------
# SVG source parsing
# ---------------------------------------------------------------------------
_COLOR = re.compile(r'(?:fill|stroke|stop-color|color)\s*[=:]\s*"?\s*(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|[a-z]+)', re.I)
_STROKE_W = re.compile(r'stroke-width="?([0-9.]+)')
_CAP = re.compile(r'stroke-linecap="?(\w+)')
_JOIN = re.compile(r'stroke-linejoin="?(\w+)')
_OPACITY = re.compile(r'(?:fill-|stroke-)?opacity="?(0?\.[0-9]+|0)"?')
_PATH_D = re.compile(r'\sd="([^"]*)"')
_CURVE_CMDS = set("CcSsQqTtAa")
_LINE_CMDS = set("LlHhVv")
_NAMED = {"black": (0, 0, 0), "white": (255, 255, 255), "gray": (128, 128, 128), "grey": (128, 128, 128),
          "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0),
          "orange": (255, 165, 0), "purple": (128, 0, 128)}
_IGNORE = {"none", "currentcolor", "transparent", "inherit", "url", "context"}
_ANIM = [
    re.compile(r"<animate\w*\b[^>]*/>|<animate\w*\b.*?</animate\w*>|<set\b[^>]*/>", re.S),
    re.compile(r'\s(?:stroke-dasharray|stroke-dashoffset)="[^"]*"'),
    re.compile(r'\s(?:fill-)?opacity="0"'),
]


def static_body(body: str) -> str:
    """Animated icons (e.g. line-md) start from an empty or partial first frame.
    Dropping the animation leaves the finished drawing."""
    if "<animate" not in body and "<set" not in body:
        return body
    for pat in _ANIM:
        body = pat.sub("", body)
    return body


def _rgb(c: str):
    c = c.strip().lower()
    if c.startswith("#"):
        h = c[1:]
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h[:3])
        try:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None
    if c.startswith("rgb"):
        nums = re.findall(r"[\d.]+", c)[:3]
        return tuple(int(float(n)) for n in nums) if len(nums) == 3 else None
    return _NAMED.get(c)


def colour_kind(body: str) -> str:
    """mono | duotone | multicolor (own fixed colours)."""
    cols = set()
    for raw in _COLOR.findall(body):
        if raw.lower() in _IGNORE:
            continue
        rgb = _rgb(raw)
        if rgb:
            cols.add(rgb)
    if not cols:
        return "mono"
    chromatic = [c for c in cols if max(c) - min(c) > 24]
    if chromatic:
        return "multicolor"
    greys = {round(sum(c) / 3 / 32) for c in cols}  # quantised grey levels
    themeable = "currentColor" in body
    if len(greys) >= 2 and not ({0, 8} >= greys):  # real grey tones, not black/white knock-outs
        return "duotone"
    if not themeable and greys != {0}:  # a single fixed non-black colour (e.g. white logos)
        return "multicolor"
    return "mono"


def source_features(body: str) -> dict:
    """Facts that can be read straight from the SVG markup."""
    stroke_widths = [float(x) for x in _STROKE_W.findall(body)]
    has_stroke = 'stroke="currentColor"' in body or "stroke:currentColor" in body
    curve = line = 0
    for d in _PATH_D.findall(body):
        for ch in d:
            if ch in _CURVE_CMDS:
                curve += 1
            elif ch in _LINE_CMDS:
                line += 1
    curve += 4 * (body.count("<circle") + body.count("<ellipse"))
    line += 4 * body.count("<rect")
    caps = set(_CAP.findall(body))
    joins = set(_JOIN.findall(body))
    kind = colour_kind(body)
    return {
        "multicolor": kind == "multicolor",
        "translucent": bool(_OPACITY.search(body)) or kind == "duotone",
        "declared_stroke": max(stroke_widths) if (has_stroke and stroke_widths) else None,
        "stroke_based": has_stroke,
        "linecap": next(iter(caps)) if len(caps) == 1 else ("mixed" if caps else None),
        "linejoin": next(iter(joins)) if len(joins) == 1 else ("mixed" if joins else None),
        "curve_cmd_ratio": curve / (curve + line) if (curve + line) else None,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_alpha(body: str, left: float, top: float, w: float, h: float, size: int = RENDER):
    scale = size / max(w, h)
    pw, ph = max(1, round(w * scale)), max(1, round(h * scale))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="{left} {top} {w} {h}" width="{pw}" height="{ph}" color="#000">{body}</svg>'
    )
    png = resvg_py.svg_to_bytes(svg_string=svg, width=pw, height=ph, skip_system_fonts=True)
    img = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    return np.asarray(img)[:, :, 3].astype(np.float32) / 255.0, scale


# ---------------------------------------------------------------------------
# Contour geometry
# ---------------------------------------------------------------------------
def _resample(c: np.ndarray, step: float = 1.0) -> np.ndarray:
    seg = np.sqrt((np.diff(c, axis=0) ** 2).sum(1))
    total = seg.sum()
    if total < 4 * step:
        return c
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, total, step)
    return np.stack([np.interp(t, s, c[:, 0]), np.interp(t, s, c[:, 1])], 1)


def contour_metrics(alpha: np.ndarray, px_per_unit: float, level: float = 0.5) -> dict:
    """Corner sharpness and curviness measured along the outline."""
    padded = np.pad(alpha, 2)
    contours = find_contours(padded, level)
    sharp = gradual = 0.0
    straight_len = curved_len = total_len = 0.0
    corner_lim = math.radians(60)  # turning packed into ~3px = a sharp corner
    pts = []
    for c in contours:
        r = _resample(c, 1.0)
        if len(r) < 8:
            continue
        pts.append(r)
        nxt = np.roll(r, -1, axis=0)
        prv = np.roll(r, 1, axis=0)
        d1, d2 = r - prv, nxt - r
        a1 = np.arctan2(d1[:, 0], d1[:, 1])
        a2 = np.arctan2(d2[:, 0], d2[:, 1])
        signed = (a2 - a1 + np.pi) % (2 * np.pi) - np.pi
        turn = np.abs(signed)
        # Only corners that point *out of the ink* describe the drawing style:
        # the inner side of a stroked join is sharp even with round joins.
        n = d2 - d1
        norm = np.linalg.norm(n, axis=1, keepdims=True)
        n = np.divide(n, norm, out=np.zeros_like(n), where=norm > 1e-9)
        probe = r + 1.5 * n
        inkside = ndimage.map_coordinates(padded, [probe[:, 0], probe[:, 1]], order=1) > level
        # turning summed over a 3px window: a rounded corner spreads its 90°
        # over many pixels, a sharp one packs it into one or two
        win = np.abs(np.convolve(np.concatenate([signed[-1:], signed, signed[:1]]), np.ones(3), mode="valid"))
        is_sharp = win >= corner_lim
        k = np.convolve(turn, np.ones(3) / 3, mode="same")
        total_len += len(turn)
        straight_len += float((k < math.radians(2.5)).sum())
        curved_len += float(((k >= math.radians(2.5)) & ~is_sharp).sum())
        sharp += float(turn[inkside & is_sharp].sum())
        gradual += float(turn[inkside & ~is_sharp].sum())
    turning = sharp + gradual
    out = {
        "roundness": (1 - sharp / turning) if turning > 0 else None,
        "curviness": (curved_len / total_len) if total_len else None,
        "outline_len": total_len / px_per_unit,  # in 24-grid units
        "contours": len(pts),
    }
    if pts:
        allp = np.vstack(pts)
        try:
            hull = ConvexHull(allp)
            area, perim = hull.volume, hull.area
            ys, xs = allp[:, 0], allp[:, 1]
            bbox = (ys.max() - ys.min()) * (xs.max() - xs.min())
            out["hull_circularity"] = 4 * math.pi * area / (perim**2) if perim else None
            out["hull_rectangularity"] = area / bbox if bbox else None
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def analyze(body: str, left: float, top: float, w: float, h: float) -> dict:
    animated = "<animate" in body or "<set" in body
    body = static_body(body)
    src = source_features(body)
    src["animated"] = animated
    alpha, scale = render_alpha(body, left, top, w, h)
    # px per 24-grid unit: the icon's height is treated as 24 units
    px_per_unit = scale * h / 24.0
    mask = alpha >= 0.5
    ink = float(alpha.sum())
    area = alpha.size
    out = dict(src)
    out["density"] = ink / area
    if not mask.any():
        out["empty"] = True
        return out

    ys, xs = np.nonzero(mask)
    H, W = mask.shape
    out["padding"] = min(ys.min(), xs.min(), H - 1 - ys.max(), W - 1 - xs.max()) / max(H, W)
    out["extent"] = ((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)) / area

    dt = ndimage.distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1]
    skel = skeletonize(mask)
    th = 2 * dt[skel] - 1 if skel.any() else np.array([2 * dt.max() - 1])
    th = th[th > 0] / px_per_unit
    if th.size:
        med = float(np.median(th))
        out["core_weight"] = med
        p25, p75 = np.percentile(th, [25, 75])
        out["stroke_contrast"] = float((p75 - p25) / med) if med else None
    # share of ink that sits deeper than 1.6 units from any edge: solid areas
    out["solidity"] = float((dt[mask] > 1.6 * px_per_unit).sum() / mask.sum())
    # two-tone icons: read corners from the combined silhouette, not from the
    # straight cut where the dark layer meets the light one
    out.update(contour_metrics(alpha, px_per_unit, level=0.2 if src["translucent"] else 0.5))
    # Mean stroke width = 2 * ink area / outline length. Uses the anti-aliased
    # coverage, so it is sub-pixel accurate for line icons.
    if out.get("outline_len"):
        out["weight"] = 2 * (ink / px_per_unit**2) / out["outline_len"]
    # Thin strokes are only a few pixels wide at the default size, which makes
    # round caps look square. Re-measure the outline at double resolution.
    if out.get("weight") and out["weight"] < 1.25 and out["solidity"] < 0.1:
        alpha2, scale2 = render_alpha(body, left, top, w, h, size=RENDER * 2)
        fine = contour_metrics(alpha2, scale2 * h / 24.0, level=0.2 if src["translucent"] else 0.5)
        out["roundness"], out["curviness"] = fine["roundness"], fine["curviness"]
    # plain floats only (numpy scalars do not serialise to JSON)
    return {k: (float(v) if isinstance(v, np.floating) else v) for k, v in out.items()}


def analyze_light(body: str, left: float, top: float, w: float, h: float) -> dict:
    """Cheaper pass for multicolour sets (emoji, flags, logos)."""
    body = static_body(body)
    out = source_features(body)
    alpha, _ = render_alpha(body, left, top, w, h, size=48)
    mask = alpha >= 0.5
    out["density"] = float(alpha.mean())
    if mask.any():
        ys, xs = np.nonzero(mask)
        H, W = mask.shape
        out["padding"] = min(ys.min(), xs.min(), H - 1 - ys.max(), W - 1 - xs.max()) / max(H, W)
        out["extent"] = ((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)) / alpha.size
    else:
        out["empty"] = True
    return out
