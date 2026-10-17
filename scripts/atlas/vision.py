"""Looking at icons instead of reading their names.

An open image-text model (CLIP, run locally — no API key) looks at one
rendered icon per concept and scores how well it matches each content
category. Those scores become extra *votes* in the category decision
(semantics.categories_for); they never replace the name-based votes.

The weight of those votes lives in config.json ("vision_weight"). It stays at
0 until `tests/eval_vision.py` shows, on icons graded by a reviewer, that the
votes improve accuracy. The workflow .github/workflows/vision.yml runs both.

    python -m atlas.vision build --src <iconify-json> --out data/vision --hours 5
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import sys
import time
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VISION_DIR = Path(os.environ.get("ICON_ATLAS_VISION", ROOT / "data" / "vision"))
MODEL = ("ViT-B-32", "laion2b_s34b_b79k")
VISION_VERSION = 1
SKIP_SET_CATEGORIES = {"Emoji", "Logos"}  # category is decided by the set itself


# ---------------------------------------------------------------------------
# Reading votes (used when building the index; no ML dependencies needed)
# ---------------------------------------------------------------------------
def _config_weight() -> float:
    try:
        return float(json.loads((ROOT / "config.json").read_text()).get("vision_weight", 0.0))
    except Exception:
        return 0.0


@lru_cache(maxsize=512)
def _load(prefix: str) -> dict:
    p = VISION_DIR / f"{prefix}.json.gz"
    if not p.exists():
        return {}
    with gzip.open(p, "rt") as f:
        return json.load(f).get("concepts", {})


def votes(prefix: str, name: str, concept: str, weight: float | None = None) -> dict:
    """{category: vote} from the vision model for this icon's concept."""
    w = _config_weight() if weight is None else weight
    if w <= 0:
        return {}
    scores = _load(prefix).get(concept)
    if not scores:
        return {}
    return {cat: w * p for cat, p in scores}


# ---------------------------------------------------------------------------
# Computing scores (needs torch + open_clip; runs in CI)
# ---------------------------------------------------------------------------
class Scorer:
    def __init__(self, device: str = "cpu"):
        import open_clip
        import torch

        from .semantics import terms
        from .taxonomy import CATEGORIES

        self.torch = torch
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(MODEL[0], pretrained=MODEL[1])
        self.model.eval().to(device)
        self.device = device
        tok = open_clip.get_tokenizer(MODEL[0])
        # Each category is described by the words icon authors use for it:
        # its label plus its most frequent nouns and verbs in icon names.
        by_cat: dict[str, list[tuple[int, str]]] = {}
        for word, e in terms().items():
            if e.get("cat") in CATEGORIES and e.get("kind") in ("noun", "action") and e["cat"] != "other":
                by_cat.setdefault(e["cat"], []).append((e.get("n", 1), word))
        self.cats, embs = [], []
        with torch.no_grad():
            for cat, (label, _) in CATEGORIES.items():
                if cat in ("other", "emoji", "brands", "flags"):
                    continue
                words = [w for _, w in sorted(by_cat.get(cat, []), reverse=True)[:40]]
                prompts = [f"an icon about {label.lower()}"] + [f"a simple icon of {w}" for w in words]
                t = self.model.encode_text(tok(prompts).to(device))
                t = t / t.norm(dim=-1, keepdim=True)
                e = t.mean(0)
                embs.append(e / e.norm())
                self.cats.append(cat)
        self.text = torch.stack(embs)

    def image(self, icon: dict):
        import resvg_py
        from PIL import Image

        from .svg import to_svg

        svg = to_svg(icon, size=None, color="#000000").replace("<svg ", '<svg width="180" height="180" ', 1)
        png = resvg_py.svg_to_bytes(svg_string=svg, width=180, height=180, skip_system_fonts=True)
        fg = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
        bg = Image.new("RGBA", (224, 224), "white")
        bg.alpha_composite(fg, (22, 22))
        return self.preprocess(bg.convert("RGB"))

    def score(self, icons: list[dict], top: int = 3) -> list[list[tuple[str, float]]]:
        torch = self.torch
        batch = torch.stack([self.image(i) for i in icons]).to(self.device)
        with torch.no_grad():
            f = self.model.encode_image(batch)
            f = f / f.norm(dim=-1, keepdim=True)
            probs = (100.0 * f @ self.text.T).softmax(dim=-1).cpu().numpy()
        out = []
        for row in probs:
            idx = row.argsort()[::-1][:top]
            out.append([(self.cats[i], round(float(row[i]), 3)) for i in idx])
        return out


def _icon(data: dict, name: str) -> dict:
    i = data["icons"][name]
    return {"body": i["body"], "left": i.get("left", data.get("left", 0)), "top": i.get("top", data.get("top", 0)),
            "width": i.get("width", data.get("width", 16)), "height": i.get("height", data.get("height", 16))}


def representatives(data: dict) -> dict:
    """One icon per concept — style variants of a concept share its meaning."""
    from .classify import concept_of, name_tokens
    from .taxonomy import STYLE_TOKENS

    reps: dict[str, str] = {}
    for name, icon in data["icons"].items():
        if icon.get("hidden"):
            continue
        c = concept_of(name)
        plain = not (set(name_tokens(name)) & STYLE_TOKENS)
        if c not in reps or (plain and set(name_tokens(reps[c])) & STYLE_TOKENS):
            reps[c] = name
    return reps


def build(src: Path, out: Path, hours: float, batch: int = 64) -> None:
    out.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + hours * 3600
    scorer = None
    files = sorted(src.glob("*.json"), key=lambda p: p.stat().st_size)
    for i, path in enumerate(files, 1):
        data = json.loads(path.read_text())
        info = data.get("info", {})
        prefix = data["prefix"]
        if info.get("category") in SKIP_SET_CATEGORIES or info.get("palette") or "brand" in prefix or "logo" in prefix:
            continue
        stamp = {"lastModified": data.get("lastModified"), "version": VISION_VERSION, "model": list(MODEL)}
        target = out / f"{prefix}.json.gz"
        if target.exists():
            with gzip.open(target, "rt") as f:
                if json.load(f).get("stamp") == stamp:
                    continue
        if time.time() > deadline:
            print(f"time budget reached; {len(files) - i + 1} sets left for the next run", flush=True)
            return
        scorer = scorer or Scorer()
        reps = representatives(data)
        concepts, t0 = {}, time.time()
        items = list(reps.items())
        for k in range(0, len(items), batch):
            chunk = items[k:k + batch]
            icons, keep = [], []
            for concept, name in chunk:
                try:
                    icons.append(_icon(data, name))
                    keep.append(concept)
                except Exception:
                    pass
            if not icons:
                continue
            try:
                for concept, sc in zip(keep, scorer.score(icons)):
                    concepts[concept] = sc
            except Exception as e:  # one broken batch must not stop the run
                print(f"! {prefix} batch {k}: {e}", flush=True)
        tmp = target.with_suffix(".tmp")
        with gzip.open(tmp, "wt") as f:
            json.dump({"prefix": prefix, "stamp": stamp, "concepts": concepts}, f, separators=(",", ":"))
        os.replace(tmp, target)
        print(f"[{i}/{len(files)}] {prefix}: {len(concepts)} concepts in {time.time() - t0:.0f}s", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--src", required=True)
    b.add_argument("--out", default=str(VISION_DIR))
    b.add_argument("--hours", type=float, default=5.0, help="stop after this long; the next run continues")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(Path(a.src), Path(a.out), a.hours)


if __name__ == "__main__":
    sys.exit(main())
