#!/usr/bin/env python3
"""Find open icon libraries that are not in the index yet and add them.

With "discover_auto_add": true in config.json (the default), a library whose
licence allows commercial use (permissive or attribution) and that passes the
quality checks is written to sources/external.json with "approved": true; the
workflow commits it, opens an issue with the report and previews, and starts
the index update. Set "approved": false (or delete the entry) to remove one.

With "discover_auto_add": false, candidates are written with "approved": false
and the workflow opens a pull request instead: merging after flipping
"approved" to true is the approval.

    GITHUB_TOKEN=... python scripts/discover.py --days 30
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import external  # noqa: E402
from atlas.classify import license_tier  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources" / "external.json"
SEEN = ROOT / "sources" / "seen.json"
PREVIEWS = ROOT / "sources" / "previews"

QUERIES = [
    "topic:icons topic:svg",
    "topic:svg-icons",
    "topic:icon-set",
    "topic:icon-library",
    "topic:iconset",
    "icons svg in:name,description",
]


def gh(path: str, token: str | None) -> dict:
    return json.loads(external.http("https://api.github.com" + path, token))


def known_repos(db_path: Path) -> set[str]:
    """Repos already covered (from Iconify set metadata)."""
    out = set()
    if db_path.exists():
        db = sqlite3.connect(db_path)
        for url, lic in db.execute("SELECT author_url, license_url FROM sets"):
            for u in (url or "", lic or ""):
                m = re.search(r"github\.com/([^/]+/[^/#?]+)", u)
                if m:
                    out.add(m.group(1).lower().removesuffix(".git"))
    return out


def auto_add() -> bool:
    cfg = json.loads((ROOT / "config.json").read_text()) if (ROOT / "config.json").exists() else {}
    return bool(cfg.get("discover_auto_add", True))


def looks_like_icon_library(r: dict) -> bool:
    """Repos tagged "icons" are sometimes apps that merely contain icons."""
    text = f"{r.get('name', '')} {r.get('description') or ''} {' '.join(r.get('topics') or [])}".lower()
    return any(w in text for w in ("icon", "glyph", "pictogram", "emoji", "symbol"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="look at repos pushed within N days")
    ap.add_argument("--min-stars", type=int, default=60)
    ap.add_argument("--min-svgs", type=int, default=40)
    ap.add_argument("--max", type=int, default=5, help="max new candidates per run")
    ap.add_argument("--review", action="store_true", help="propose only, even if auto-add is on")
    a = ap.parse_args(argv)
    auto = auto_add() and not a.review
    token = os.environ.get("GITHUB_TOKEN")
    since = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()

    sources = json.loads(SOURCES.read_text()) if SOURCES.exists() else []
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    known = known_repos(ROOT / "data" / "atlas.db") | {s["repo"].lower() for s in sources}

    candidates = {}
    for q in QUERIES:
        query = f"{q} stars:>={a.min_stars} pushed:>={since} archived:false"
        try:
            res = gh("/search/repositories?" + urllib.parse.urlencode({"q": query, "sort": "stars", "per_page": 50}), token)
        except Exception as e:
            print(f"! search failed for '{q}': {e}")
            continue
        for r in res.get("items", []):
            full = r["full_name"].lower()
            if full in known or full in seen:
                continue
            candidates[full] = r

    proposed, skipped = [], []
    for full, r in sorted(candidates.items(), key=lambda kv: -kv[1]["stargazers_count"]):
        if len(proposed) >= a.max:
            break
        seen.add(full)
        spdx = (r.get("license") or {}).get("spdx_id")
        tier = license_tier(spdx)
        if tier not in ("permissive", "attribution"):
            skipped.append(f"{r['full_name']} — licence {spdx or 'none'} ({tier})")
            continue
        if not looks_like_icon_library(r):
            skipped.append(f"{r['full_name']} — does not describe itself as an icon library")
            continue
        try:
            tar = external.repo_tarball(r["full_name"], None, token)
            members = external.svg_members(tar)
            folder = external.guess_icon_dir(members)
            in_folder = [m for m in members if str(Path(*Path(m.name).parts[1:]).parent) == folder]
            n = len(in_folder)
            ok = sum(1 for m in in_folder[:200]
                     if external.parse_svg_file(tar.extractfile(m).read().decode("utf-8", "replace")))
        except Exception as e:
            skipped.append(f"{r['full_name']} — could not read ({e})")
            continue
        if n < a.min_svgs:
            skipped.append(f"{r['full_name']} — only {n} SVGs")
            continue
        if ok < 0.9 * min(n, 200):
            skipped.append(f"{r['full_name']} — {min(n, 200) - ok} of {min(n, 200)} sampled SVGs are unreadable")
            continue
        prefix = "x-" + re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")
        entry = {
            "prefix": prefix, "name": r["name"], "repo": r["full_name"], "folder": folder,
            "license": spdx, "license_url": r["html_url"] + "/blob/HEAD/LICENSE",
            "stars": r["stargazers_count"], "svgs": n, "description": (r.get("description") or "")[:200],
            "approved": auto, "auto": auto, "found": dt.date.today().isoformat(),
        }
        _preview(tar, members, folder, prefix)
        sources.append(entry)
        proposed.append(entry)

    SOURCES.parent.mkdir(exist_ok=True)
    SOURCES.write_text(json.dumps(sources, indent=1, ensure_ascii=False) + "\n")
    SEEN.write_text(json.dumps(sorted(seen), indent=0) + "\n")

    if auto:
        body = ["These libraries were **added automatically**: their licence allows commercial use and they "
                "passed the checks (stars, SVG count, readable files, describes itself as an icon library). "
                "They are indexed by the next index update.", "",
                "To remove one: set `\"approved\": false` for it in `sources/external.json` (or delete the entry). "
                "To go back to reviewing every library first: set `\"discover_auto_add\": false` in `config.json`.", ""]
    else:
        body = ["Libraries found outside the index. **Nothing is added until you approve it**: "
                "set `\"approved\": true` for the ones you want in `sources/external.json`, delete the others, then merge.", ""]
    for e in proposed:
        body += [f"### {e['name']}  ·  [{e['repo']}](https://github.com/{e['repo']})",
                 f"{e['description']}", "",
                 f"- ⭐ {e['stars']} · {e['svgs']} SVGs in `{e['folder']}` · licence **{e['license']}** ({license_tier(e['license'])})",
                 f"- preview: ![{e['name']}](https://raw.githubusercontent.com/{_repo()}/main/sources/previews/{e['prefix']}.png)", ""]
    if skipped:
        body += ["<details><summary>Skipped</summary>", ""] + [f"- {s}" for s in skipped] + ["", "</details>"]
    (ROOT / ".work").mkdir(exist_ok=True)
    (ROOT / ".work" / "discover.md").write_text("\n".join(body) + "\n")
    print("\n".join(body))
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"found={len(proposed)}\nauto={'true' if auto else 'false'}\n")


def _repo() -> str:
    cfg = ROOT / "config.json"
    return os.environ.get("GITHUB_REPOSITORY") or (json.loads(cfg.read_text()).get("repo", "") if cfg.exists() else "")


def _preview(tar, members, folder, prefix):
    """Contact sheet of up to 24 icons so the reviewer can judge quality."""
    try:
        import io

        import resvg_py
        from PIL import Image

        PREVIEWS.mkdir(parents=True, exist_ok=True)
        pick = [m for m in members if str(Path(*Path(m.name).parts[1:]).parent) == folder][:24]
        cell, cols = 64, 8
        img = Image.new("RGB", (cols * cell, -(-len(pick) // cols) * cell), "white")
        for i, m in enumerate(pick):
            icon = external.parse_svg_file(tar.extractfile(m).read().decode("utf-8", "replace"))
            if not icon:
                continue
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{icon["left"]} {icon["top"]} '
                   f'{icon["width"]} {icon["height"]}" width="40" height="40" color="#111">{icon["body"]}</svg>')
            png = resvg_py.svg_to_bytes(svg_string=svg, width=40, height=40, skip_system_fonts=True)
            ic = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
            img.paste(ic, ((i % cols) * cell + 12, (i // cols) * cell + 12), ic)
        img.save(PREVIEWS / f"{prefix}.png")
    except Exception as e:
        print(f"! preview failed for {prefix}: {e}")


if __name__ == "__main__":
    main()
