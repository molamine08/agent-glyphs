"""Measure every icon of every Iconify set and store raw metrics per set.

Incremental: a set is re-measured only when its `lastModified` stamp or the
analyzer version changed, which is what makes the daily update cheap.

    python -m atlas.build_metrics --src <iconify-json>/json --out data/metrics
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

from .analyze import analyze, analyze_light

ANALYZER_VERSION = 5  # 5: corner events, tint share


def icon_box(data: dict, icon: dict):
    return (
        icon.get("left", data.get("left", 0)),
        icon.get("top", data.get("top", 0)),
        icon.get("width", data.get("width", 16)),
        icon.get("height", data.get("height", 16)),
    )


def _work(args):
    name, body, box, light = args
    try:
        m = (analyze_light if light else analyze)(body, *box)
    except Exception as e:  # a broken icon must not stop the run
        m = {"error": str(e)[:200]}
    m["w"], m["h"] = box[2], box[3]
    return name, m


def measure_set(path: Path, out_dir: Path, pool: Pool, force: bool = False) -> str:
    data = json.loads(path.read_text())
    prefix = data["prefix"]
    out = out_dir / f"{prefix}.json.gz"
    stamp = {"lastModified": data.get("lastModified"), "analyzer": ANALYZER_VERSION}
    if out.exists() and not force:
        with gzip.open(out, "rt") as f:
            old = json.load(f)
        if old.get("stamp") == stamp:
            return "skip"
    info = data.get("info", {})
    light = bool(info.get("palette"))  # full-colour sets: style is "multicolor" anyway
    jobs = [
        (name, icon["body"], icon_box(data, icon), light)
        for name, icon in data["icons"].items()
        if not icon.get("hidden")
    ]
    t = time.time()
    icons = dict(pool.imap_unordered(_work, jobs, chunksize=64))
    record = {
        "prefix": prefix,
        "stamp": stamp,
        "info": info,
        "aliases": {k: v.get("parent") for k, v in data.get("aliases", {}).items()},
        "categories": data.get("categories", {}),
        "suffixes": data.get("suffixes", {}),
        "prefixes": data.get("prefixes", {}),
        "light": light,
        "icons": icons,
    }
    tmp = out.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as f:
        json.dump(record, f, separators=(",", ":"))
    os.replace(tmp, out)
    return f"{len(icons)} icons in {time.time() - t:.0f}s"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder with Iconify <prefix>.json files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", help="limit to these prefixes")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args(argv)
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.json"), key=lambda p: p.stat().st_size)
    if a.only:
        files = [p for p in files if p.stem in set(a.only)]
    with Pool(a.workers) as pool:
        for i, p in enumerate(files, 1):
            status = measure_set(p, out, pool, a.force)
            print(f"[{i}/{len(files)}] {p.stem}: {status}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
