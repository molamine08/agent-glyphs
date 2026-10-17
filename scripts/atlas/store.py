"""Where the index and the icon sources live, and how to get them.

The index (data/atlas.db) is built by the daily workflow and published as a
GitHub release asset. Icon SVG bodies are not redistributed by this project:
they are fetched on demand from the official Iconify packages on npm (or the
public Iconify API), so every icon keeps travelling with its own licence.
"""

from __future__ import annotations

import gzip
import io
import json
import os
import shutil
import sqlite3
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config.json").read_text()) if (ROOT / "config.json").exists() else {}
DATA = Path(os.environ.get("ICON_ATLAS_DATA", ROOT / "data"))
CACHE = Path(os.environ.get("ICON_ATLAS_CACHE", Path.home() / ".cache" / "icon-atlas"))
DB_PATH = DATA / "atlas.db"
UA = {"User-Agent": "icon-atlas"}


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def ensure_index() -> Path:
    """Return the path to atlas.db, downloading the latest release if missing."""
    if DB_PATH.exists():
        return DB_PATH
    url = CONFIG.get("index_url")
    if not url:
        raise SystemExit("atlas.db not found and no index_url in config.json")
    DATA.mkdir(parents=True, exist_ok=True)
    blob = _get(url, timeout=300)
    tmp = DB_PATH.with_suffix(".tmp")
    tmp.write_bytes(gzip.decompress(blob) if url.endswith(".gz") else blob)
    tmp.replace(DB_PATH)
    return DB_PATH


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(ensure_index())
    db.row_factory = sqlite3.Row
    return db


# ---------------------------------------------------------------------------
# Icon sources
# ---------------------------------------------------------------------------
def _local_set(prefix: str) -> dict | None:
    """Look for an already-downloaded Iconify JSON file."""
    candidates = [CACHE / "sets" / f"{prefix}.json"]
    src = os.environ.get("ICONIFY_JSON_DIR")
    if src:
        candidates.insert(0, Path(src) / f"{prefix}.json")
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())
    return None


def _npm_set(prefix: str) -> dict:
    """Download the single-set package @iconify-json/<prefix> from npm."""
    meta = json.loads(_get(f"https://registry.npmjs.org/@iconify-json/{prefix}/latest"))
    tgz = _get(meta["dist"]["tarball"], timeout=180)
    with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as tar:
        member = tar.getmember("package/icons.json")
        data = json.load(tar.extractfile(member))
    (CACHE / "sets").mkdir(parents=True, exist_ok=True)
    (CACHE / "sets" / f"{prefix}.json").write_text(json.dumps(data))
    return data


def _api_icons(prefix: str, names: list[str]) -> dict:
    url = f"https://api.iconify.design/{prefix}.json?icons={','.join(names)}"
    return json.loads(_get(url))


def icon_data(prefix: str, names: list[str]) -> dict:
    """Return {name: {"body", "left", "top", "width", "height"}} for icons of one set."""
    data = _local_set(prefix)
    if data is None:
        errors = []
        for loader in (lambda: _npm_set(prefix), lambda: _api_icons(prefix, names)):
            try:
                data = loader()
                break
            except Exception as e:  # network may be restricted; try the next source
                errors.append(str(e))
        if data is None:
            raise SystemExit(f"could not fetch icons for '{prefix}': {'; '.join(errors)}")
    out = {}
    aliases = data.get("aliases", {})
    for name in names:
        icon, transforms, cur = None, {}, name
        for _ in range(5):  # resolve alias chains
            if cur in data.get("icons", {}):
                icon = data["icons"][cur]
                break
            if cur in aliases:
                transforms.update({k: v for k, v in aliases[cur].items() if k != "parent"})
                cur = aliases[cur]["parent"]
            else:
                break
        if icon is None:
            continue
        merged = {**icon, **transforms}
        out[name] = {
            "body": merged["body"],
            "left": merged.get("left", data.get("left", 0)),
            "top": merged.get("top", data.get("top", 0)),
            "width": merged.get("width", data.get("width", 16)),
            "height": merged.get("height", data.get("height", 16)),
            "rotate": merged.get("rotate", 0),
            "hFlip": merged.get("hFlip", False),
            "vFlip": merged.get("vFlip", False),
        }
    return out


def clear_cache():
    shutil.rmtree(CACHE, ignore_errors=True)
