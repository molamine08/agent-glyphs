#!/usr/bin/env python3
"""Daily update: pull the newest Iconify release (+ approved external
libraries), measure only what changed, rebuild the index and write a
changelog. Run by .github/workflows/daily-update.yml; safe to run by hand.

    python scripts/update.py            # no-op when nothing changed
    python scripts/update.py --force    # rebuild even if the version is the same
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import io
import json
import os
import shutil
import sqlite3
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import build_index, build_metrics, external  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WORK = ROOT / ".work"
STATE = ROOT / "state.json"
SOURCES = ROOT / "sources" / "external.json"


def fetch_iconify(dest: Path) -> str:
    meta = json.loads(urllib.request.urlopen("https://registry.npmjs.org/@iconify/json/latest", timeout=60).read())
    blob = urllib.request.urlopen(meta["dist"]["tarball"], timeout=600).read()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for m in tar.getmembers():
            # only the data we need, written under names we choose (no path traversal)
            if m.isfile() and m.name.startswith("package/json/") and m.name.endswith(".json"):
                (dest / Path(m.name).name).write_bytes(tar.extractfile(m).read())
    return meta["version"]


def latest_version() -> str:
    return json.loads(urllib.request.urlopen("https://registry.npmjs.org/@iconify/json/latest", timeout=60).read())["version"]


def vision_signature() -> str:
    """Changes when the vision results or their weight change (→ rebuild)."""
    import hashlib

    cfg = json.loads((ROOT / "config.json").read_text()) if (ROOT / "config.json").exists() else {}
    h = hashlib.sha1(str(cfg.get("vision_weight", 0)).encode())
    for p in sorted((DATA / "vision").glob("*.json.gz")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    return h.hexdigest()[:12]


def bundle_external(src: Path, prefixes: list[str]) -> Path:
    """Libraries outside Iconify have no npm package or public API, so their
    (sanitised) SVG data ships next to the index as one release asset."""
    out = DATA / "external-sets.json.gz"
    sets = {p: json.loads((src / f"{p}.json").read_text()) for p in prefixes if (src / f"{p}.json").exists()}
    with gzip.open(out, "wt", compresslevel=9) as g:
        json.dump(sets, g, separators=(",", ":"))
    return out


def snapshot(db_path: Path) -> dict:
    if not db_path.exists():
        return {}
    db = sqlite3.connect(db_path)
    return {p: n for p, n in db.execute("SELECT prefix, total FROM sets")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--src", help="use an already-extracted Iconify json folder (offline/testing)")
    a = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    sources = json.loads(SOURCES.read_text()) if SOURCES.exists() else []
    ext_sig = [[s["prefix"], s.get("ref")] for s in sources if s.get("approved")]
    vis_sig = vision_signature()
    from atlas.build_metrics import ANALYZER_VERSION
    from atlas.classify import LABELS_VERSION
    lab_sig = [ANALYZER_VERSION, LABELS_VERSION]

    version = latest_version() if not a.src else state.get("iconify_version", "local")
    if not a.force and version == state.get("iconify_version") and ext_sig == state.get("external") \
            and vis_sig == state.get("vision") and lab_sig == state.get("labels"):
        print(f"up to date (Iconify {version})")
        _output(changed=False)
        return

    src = Path(a.src) if a.src else WORK / "iconify"
    if not a.src:
        version = fetch_iconify(src)
    ext = external.write_external_sets(SOURCES, src, token)
    print(f"Iconify {version}; external sets: {ext or 'none'}")

    metrics = DATA / "metrics"
    build_metrics.main(["--src", str(src), "--out", str(metrics)])
    present = {p.stem for p in src.glob("*.json")}
    for old in metrics.glob("*.json.gz"):  # sets removed upstream
        if old.name[:-8] not in present:
            old.unlink()

    db_path = DATA / "atlas.db"
    before = snapshot(db_path)
    stats = build_index.build(metrics, db_path, version, src)
    after = snapshot(db_path)
    with open(db_path, "rb") as f, gzip.open(DATA / "atlas.db.gz", "wb", compresslevel=9) as g:
        shutil.copyfileobj(f, g)
    bundle_external(src, ext)

    today = dt.date.today().isoformat()
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    grown = {p: after[p] - before[p] for p in after if p in before and after[p] != before[p]}
    lines = [f"## {today} — Iconify {version}", "",
             f"- {stats['sets']} sets, {stats['icons']:,} icons"]
    if added:
        lines.append(f"- new libraries: {', '.join(added)}")
    if removed:
        lines.append(f"- removed: {', '.join(removed)}")
    if grown:
        lines.append("- changed: " + ", ".join(f"{p} ({d:+d})" for p, d in sorted(grown.items())))
    notes = "\n".join(lines) + "\n"
    (WORK).mkdir(exist_ok=True)
    (WORK / "release-notes.md").write_text(notes)
    log = ROOT / "CHANGELOG.md"
    old = log.read_text().split("\n", 2)[2] if log.exists() and log.read_text().startswith("# ") else ""
    log.write_text("# Changelog\n\n" + notes + "\n" + old)

    state.update({"iconify_version": version, "built": today, "external": ext_sig, "vision": vis_sig, "labels": lab_sig,
                  "sets": stats["sets"], "icons": stats["icons"]})
    STATE.write_text(json.dumps(state, indent=1) + "\n")
    print(notes)
    _output(changed=True, tag=f"data-{today}-{version}")


def _output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            for k, v in kv.items():
                f.write(f"{k}={str(v).lower() if isinstance(v, bool) else v}\n")


if __name__ == "__main__":
    main()
