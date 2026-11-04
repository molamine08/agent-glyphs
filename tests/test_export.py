import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import get  # noqa: E402
from atlas import concepts  # noqa: E402


class LicenceLinks(unittest.TestCase):
    def test_missing_url_links_to_spdx(self):
        self.assertEqual(get.license_cell("MIT", None), "[MIT](https://spdx.org/licenses/MIT.html)")

    def test_known_url_is_kept_and_unknown_is_plain(self):
        self.assertEqual(get.license_cell("MIT", "https://x/LICENSE"), "[MIT](https://x/LICENSE)")
        self.assertEqual(get.license_cell(None, None), "unknown")


class AssetCatalog(unittest.TestCase):
    def test_imageset_keeps_the_vector_and_tints(self):
        svg = '<svg viewBox="0 0 24 24" style="color:#f00"><path stroke="currentColor" d="M0 0h24"/></svg>'
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "App.xcassets"
            folder = get.write_imageset(out, "lucide-house", svg, None)
            meta = json.loads((folder / "Contents.json").read_text())
            self.assertEqual(meta["images"][0]["filename"], "lucide-house.svg")
            self.assertTrue(meta["properties"]["preserves-vector-representation"])
            self.assertEqual(meta["properties"]["template-rendering-intent"], "template")
            drawn = (folder / "lucide-house.svg").read_text()
            self.assertNotIn("currentColor", drawn)
            self.assertNotIn("style=", drawn)
            self.assertTrue((out / "Contents.json").exists())

    def test_multicolour_icon_keeps_its_colours(self):
        with tempfile.TemporaryDirectory() as d:
            folder = get.write_imageset(Path(d), "logos-x", '<svg><path fill="#1DA1F2"/></svg>', None)
            meta = json.loads((folder / "Contents.json").read_text())
            self.assertEqual(meta["properties"]["template-rendering-intent"], "original")


class EnglishPhrases(unittest.TestCase):
    def test_two_words_reach_the_one_token_name(self):
        parts = concepts.expand("image search")
        self.assertEqual(len(parts), 1)
        self.assertIn("search-visual", parts[0].strong)

    def test_similar_has_a_meaning(self):
        (p,) = concepts.expand("similar")
        self.assertIn("related", p.strong)


if __name__ == "__main__":
    unittest.main()
