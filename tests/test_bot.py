"""Offline tests for the discovery/import bot (GitHub calls are faked)."""

import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas import external  # noqa: E402

SVG_STROKE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" '
              'stroke-width="2" stroke-linecap="round"><path d="M{a} 4 L20 20 M4 20 L20 {a}"/></svg>')
SVG_EVIL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><script>alert(1)</script>'
            '<path onclick="x()" d="M2 2h20v20H2z" fill="black"/><image href="https://evil.example/x.png"/></svg>')


def fake_repo(n=50) -> tarfile.TarFile:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        def add(name, text):
            data = text.encode()
            info = tarfile.TarInfo(f"owner-repo-abc123/{name}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        for i in range(n):
            add(f"icons/outline/Icon Number {i}.svg", SVG_STROKE.format(a=4 + i % 10))
        add("icons/outline/evil.svg", SVG_EVIL)
        add("docs/logo.svg", SVG_STROKE.format(a=1))
        add("node_modules/x/y.svg", SVG_STROKE.format(a=2))
        add("../../escape.svg", SVG_STROKE.format(a=3))
    buf.seek(0)
    return tarfile.open(fileobj=buf, mode="r:gz")


class External(unittest.TestCase):
    def test_folder_guess_and_filters(self):
        members = external.svg_members(fake_repo())
        self.assertEqual(external.guess_icon_dir(members), "icons/outline")
        self.assertFalse(any("node_modules" in m.name or "docs/" in m.name for m in members))

    def test_sanitize(self):
        icon = external.parse_svg_file(SVG_EVIL)
        self.assertNotIn("<script", icon["body"])
        self.assertNotIn("onclick", icon["body"])
        self.assertNotIn("evil.example", icon["body"])
        self.assertIn('fill="currentColor"', icon["body"])

    def test_build_set(self):
        src = {"prefix": "x-test", "name": "Test", "repo": "owner/repo", "license": "MIT", "approved": True}
        with mock.patch.object(external, "repo_tarball", lambda *a, **k: fake_repo()):
            data = external.build_set(src)
        self.assertEqual(data["prefix"], "x-test")
        self.assertIn("icon-number-3", data["icons"])
        self.assertEqual(len(data["icons"]), 51)  # 50 + sanitised evil.svg
        body = data["icons"]["icon-number-3"]["body"]
        self.assertIn('stroke="currentColor"', body)  # root attributes carried + made themeable

    def test_measurable(self):
        from atlas.analyze import analyze
        from atlas.classify import classify
        icon = external.parse_svg_file(SVG_STROKE.format(a=4))
        m = analyze(icon["body"], icon["left"], icon["top"], icon["width"], icon["height"])
        m["w"], m["h"] = 24, 24
        lab = classify("x-test", "cross", m, False)
        self.assertEqual(lab["style"], "outline")
        self.assertAlmostEqual(lab["weight"], 2.0, delta=0.3)


class Discover(unittest.TestCase):
    def test_proposes_only_open_licences(self):
        import discover
        items = [
            {"full_name": "a/good-icons", "name": "good-icons", "stargazers_count": 900, "html_url": "https://github.com/a/good-icons",
             "license": {"spdx_id": "MIT"}, "description": "Nice icons"},
            {"full_name": "b/nc-icons", "name": "nc-icons", "stargazers_count": 800, "html_url": "https://github.com/b/nc-icons",
             "license": {"spdx_id": "CC-BY-NC-4.0"}, "description": "Non-commercial"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with mock.patch.object(discover, "ROOT", tmp), \
                 mock.patch.object(discover, "SOURCES", tmp / "sources" / "external.json"), \
                 mock.patch.object(discover, "SEEN", tmp / "sources" / "seen.json"), \
                 mock.patch.object(discover, "PREVIEWS", tmp / "sources" / "previews"), \
                 mock.patch.object(discover, "gh", lambda path, token: {"items": items}), \
                 mock.patch.object(external, "repo_tarball", lambda *a, **k: fake_repo()):
                (tmp / "sources").mkdir()
                discover.main(["--max", "5"])
                proposed = json.loads((tmp / "sources" / "external.json").read_text())
                self.assertEqual([p["repo"] for p in proposed], ["a/good-icons"])
                self.assertFalse(proposed[0]["approved"])
                self.assertTrue((tmp / "sources" / "previews" / "x-good-icons.png").exists())
                self.assertIn("b/nc-icons", (tmp / ".work" / "discover.md").read_text())
                # second run: nothing new (already seen / already proposed)
                discover.main(["--max", "5"])
                self.assertEqual(len(json.loads((tmp / "sources" / "external.json").read_text())), 1)


if __name__ == "__main__":
    unittest.main()
