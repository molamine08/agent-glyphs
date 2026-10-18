"""Calibration and sanity tests. Run: python -m unittest discover -s tests -v

The analyzer tests use icon sets whose drawing rules are published, so they
double as the accuracy contract of the project.
"""

import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas.analyze import analyze  # noqa: E402
from atlas.classify import classify  # noqa: E402
from atlas.semantics import norm_ar  # noqa: E402

SRC = Path(os.environ.get("ICONIFY_JSON_DIR", ROOT / ".work" / "iconify"))
DB = ROOT / "data" / "atlas.db"


def icon(prefix, name):
    d = json.loads((SRC / f"{prefix}.json").read_text())
    i = d["icons"][name]
    box = (i.get("left", d.get("left", 0)), i.get("top", d.get("top", 0)),
           i.get("width", d.get("width", 16)), i.get("height", d.get("height", 16)))
    m = analyze(i["body"], *box)
    m["w"], m["h"] = box[2], box[3]
    return classify(prefix, name, m, False)


@unittest.skipUnless((SRC / "lucide.json").exists(), "Iconify JSON not available")
class Calibration(unittest.TestCase):
    def test_stroke_weight(self):
        # published stroke widths on a 24px grid
        cases = [("lucide", "house", 2.0), ("tabler", "home", 2.0), ("heroicons", "home", 1.5),
                 ("ph", "house-thin", 0.75), ("ph", "house-light", 1.125), ("ph", "house", 1.5),
                 ("ph", "house-bold", 2.25), ("iconoir", "home", 1.5)]
        for p, n, expected in cases:
            with self.subTest(icon=f"{p}:{n}"):
                self.assertAlmostEqual(icon(p, n)["weight"], expected, delta=0.15 * expected)

    def test_style(self):
        for p, n, style in [("lucide", "house", "outline"), ("heroicons", "home-solid", "filled"),
                            ("ph", "house-fill", "filled"), ("ph", "house-duotone", "duotone"),
                            ("mdi", "home", "filled"), ("mdi", "home-outline", "outline")]:
            with self.subTest(icon=f"{p}:{n}"):
                self.assertEqual(icon(p, n)["style"], style)

    def test_stroke_classes(self):
        for p, n, stroke in [("ph", "house-thin", "thin"), ("heroicons", "home", "light"), ("ph", "house", "light"),
                             ("lucide", "house", "regular"), ("tabler", "home", "regular"), ("ph", "house-bold", "bold")]:
            with self.subTest(icon=f"{p}:{n}"):
                self.assertEqual(icon(p, n)["stroke"], stroke)

    def test_shape_and_color(self):
        # what the eye sees: a duotone Phosphor icon is an outline icon in two tones,
        # and a "filled"-named icon drawn with lines is an outline icon
        for p, n, shape, color in [("ph", "house-duotone", "outline", "duotone"), ("ph", "house-fill", "filled", "mono"),
                                   ("lucide", "house", "outline", "mono"), ("fluent", "link-20-filled", "outline", "mono")]:
            with self.subTest(icon=f"{p}:{n}"):
                lab = icon(p, n)
                self.assertEqual((lab["shape"], lab["color"]), (shape, color))

    def test_corners(self):
        for p, n, corners in [("lucide", "house", "rounded"), ("tabler", "home", "rounded"),
                              ("material-symbols", "home-outline-rounded", "rounded"),
                              ("material-symbols", "home-outline", "sharp"), ("mdi", "check", "sharp"),
                              # wheels are circles, not corners: Carbon's cart is sharp
                              ("carbon", "shopping-cart", "sharp"), ("heroicons", "shopping-cart", "rounded")]:
            with self.subTest(icon=f"{p}:{n}"):
                self.assertEqual(icon(p, n)["corners"], corners)


class Arabic(unittest.TestCase):
    def test_normalisation(self):
        self.assertEqual(norm_ar("السلة"), norm_ar("سلة"))
        self.assertEqual(norm_ar("إعدادات"), norm_ar("اعدادات"))
        self.assertEqual(norm_ar("الفاتورة"), "فاتوره")


@unittest.skipUnless(DB.exists(), "index not built")
class Index(unittest.TestCase):
    def setUp(self):
        from atlas.query import Filters, search
        self.db = sqlite3.connect(DB)
        self.db.row_factory = sqlite3.Row
        self.search, self.Filters = search, Filters

    def test_size(self):
        n = self.db.execute("SELECT COUNT(*) FROM icons").fetchone()[0]
        self.assertGreater(n, 300_000)

    def test_english_search(self):
        rows = self.search(self.db, "shopping cart", self.Filters(sets=["lucide"]), limit=3, per_set=3)
        self.assertTrue(any("cart" in r["name"] for r in rows))

    def test_arabic_search(self):
        rows = self.search(self.db, "سلة التسوق", self.Filters(), limit=10)
        self.assertTrue(rows and all("cart" in r["name"] or "basket" in r["name"] or "bag" in r["name"] or "shop" in r["name"] for r in rows[:5]))

    def test_filters(self):
        rows = self.search(self.db, "bell", self.Filters(shape="outline", corners="rounded", weight=1.5), limit=10)
        for r in rows:
            self.assertEqual(r["shape"], "outline")
            self.assertLessEqual(abs(r["weight"] - 1.5), 0.31)

    def test_no_noncommercial_by_default(self):
        rows = self.search(self.db, "home", self.Filters(), limit=50)
        self.assertTrue(all(r["license_tier"] in ("permissive", "attribution") for r in rows))


if __name__ == "__main__":
    unittest.main()
