"""Icon libraries that are not (yet) in Iconify.

Approved sources live in sources/external.json. Each one is a GitHub repo
whose SVG files are converted into an Iconify-style set so the rest of the
pipeline treats it like any other set. Files are read straight out of the
repo tarball in memory; nothing from the archive is written to disk except
the sanitised SVG paths.
"""

from __future__ import annotations

import io
import json
import re
import tarfile
import urllib.request
from collections import Counter
from pathlib import PurePosixPath

UA = {"User-Agent": "icon-atlas-bot", "Accept": "application/vnd.github+json"}
SKIP_DIRS = re.compile(r"(^|/)(node_modules|docs?|site|website|examples?|test[s]?|\.github|public/og|fonts?)(/|$)", re.I)

_BAD = [
    (re.compile(r"<script\b.*?</script>", re.S | re.I), ""),
    (re.compile(r"<foreignObject\b.*?</foreignObject>", re.S | re.I), ""),
    (re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*')", re.I), ""),
    (re.compile(r"(xlink:)?href\s*=\s*(\"(?!#)[^\"]*\"|'(?!#)[^']*')", re.I), ""),
    (re.compile(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", re.S), ""),
]


def sanitize(body: str) -> str:
    for pat, rep in _BAD:
        body = pat.sub(rep, body)
    return body.strip()


def http(url: str, token: str | None = None, timeout: int = 120) -> bytes:
    headers = dict(UA)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return r.read()


def repo_tarball(repo: str, ref: str | None, token: str | None) -> tarfile.TarFile:
    url = f"https://api.github.com/repos/{repo}/tarball" + (f"/{ref}" if ref else "")
    return tarfile.open(fileobj=io.BytesIO(http(url, token, timeout=300)), mode="r:gz")


def svg_members(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    out = []
    for m in tar.getmembers():
        if not m.isfile() or not m.name.lower().endswith(".svg") or m.size > 200_000:
            continue
        rel = "/".join(PurePosixPath(m.name).parts[1:])  # drop the "<repo>-<sha>/" root
        if SKIP_DIRS.search(rel):
            continue
        out.append(m)
    return out


def guess_icon_dir(members: list[tarfile.TarInfo]) -> str | None:
    """The folder holding the most SVGs is almost always the icon folder."""
    dirs = Counter(str(PurePosixPath(*PurePosixPath(m.name).parts[1:]).parent) for m in members)
    return dirs.most_common(1)[0][0] if dirs else None


def parse_svg_file(text: str):
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>", text, re.S | re.I)
    if not m:
        return None
    attrs, body = m.group(1), m.group(2)
    vb = re.search(r'viewBox=["\']\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)', attrs)
    if not vb:
        return None
    left, top, w, h = map(float, vb.groups())
    inherit = " ".join(re.findall(r'\s((?:fill|stroke|stroke-width|stroke-linecap|stroke-linejoin)="[^"]*")', attrs))
    body = sanitize(body)
    # hard-coded black is the usual "no colour" in icon repos → make it themeable
    body = re.sub(r'(fill|stroke)="(#000|#000000|black)"', r'\1="currentColor"', body)
    inherit = re.sub(r'(fill|stroke)="(#000|#000000|black)"', r'\1="currentColor"', inherit)
    if inherit:
        body = f"<g {inherit}>{body}</g>"
    return {"body": body, "left": left, "top": top, "width": w, "height": h}


def build_set(src: dict, token: str | None = None) -> dict:
    """Convert an approved external source into Iconify JSON."""
    tar = repo_tarball(src["repo"], src.get("ref"), token)
    members = svg_members(tar)
    folder = src.get("folder") or guess_icon_dir(members)
    icons = {}
    for m in members:
        rel = PurePosixPath(*PurePosixPath(m.name).parts[1:])
        if folder and str(rel.parent) != folder and not str(rel.parent).startswith(folder + "/"):
            continue
        name = re.sub(r"[^a-z0-9]+", "-", rel.stem.lower()).strip("-")
        sub = str(rel.parent)[len(folder):].strip("/") if folder else ""
        if sub and src.get("include_subfolders", True):
            name = re.sub(r"[^a-z0-9]+", "-", sub.lower()).strip("-") + "-" + name
        icon = parse_svg_file(tar.extractfile(m).read().decode("utf-8", "replace"))
        if icon and name:
            icons[name] = icon
    return {
        "prefix": src["prefix"],
        "info": {
            "name": src["name"], "total": len(icons),
            "author": {"name": src.get("author", src["repo"].split("/")[0]), "url": f"https://github.com/{src['repo']}"},
            "license": {"title": src["license"], "spdx": src["license"], "url": src.get("license_url", f"https://github.com/{src['repo']}")},
            "category": src.get("category", "External"),
        },
        "lastModified": src.get("updated", 0),
        "icons": icons,
    }


def write_external_sets(sources_file, out_dir, token=None) -> list[str]:
    sources = json.loads(open(sources_file).read()) if sources_file.exists() else []
    written = []
    for src in sources:
        if not src.get("approved"):
            continue
        try:
            meta = json.loads(http(f"https://api.github.com/repos/{src['repo']}", token))
            pushed = meta.get("pushed_at", "")
            if pushed:
                import datetime as dt
                src = {**src, "updated": int(dt.datetime.fromisoformat(pushed.replace("Z", "+00:00")).timestamp())}
            data = build_set(src, token)
        except Exception as e:
            print(f"! external {src.get('repo')}: {e}")
            continue
        (out_dir / f"{src['prefix']}.json").write_text(json.dumps(data))
        written.append(src["prefix"])
    return written
