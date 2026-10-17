"""Vision pipeline plumbing, with the model faked (no torch needed)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from atlas import vision  # noqa: E402
from atlas.semantics import categories_for  # noqa: E402

BODY = '<path fill="none" stroke="currentColor" stroke-width="2" d="M3 12h18M12 3v18"/>'


class FakeScorer:
    calls = 0

    def score(self, icons, top=3):
        FakeScorer.calls += len(icons)
        return [[("communication", 0.7), ("transport", 0.2), ("actions", 0.1)] for _ in icons]


class Vision(unittest.TestCase):
    def test_representatives_one_per_concept(self):
        data = {"icons": {n: {"body": BODY} for n in
                          ("send", "send-outline", "send-filled", "send-bold", "plane", "plane-outline")}}
        reps = vision.representatives(data)
        self.assertEqual(set(reps), {"send", "plane"})
        self.assertEqual(reps["send"], "send")  # the plain variant is preferred

    def test_build_incremental_and_votes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src, out = tmp / "src", tmp / "vision"
            src.mkdir()
            data = {"prefix": "demo", "info": {"name": "Demo"}, "lastModified": 1, "width": 24, "height": 24,
                    "icons": {"paper-plane": {"body": BODY}, "paper-plane-outline": {"body": BODY}}}
            (src / "demo.json").write_text(json.dumps(data))
            (src / "emo.json").write_text(json.dumps({**data, "prefix": "emo", "info": {"category": "Emoji"}}))
            FakeScorer.calls = 0
            with mock.patch.object(vision, "Scorer", FakeScorer):
                vision.build(src, out, hours=1)
                self.assertEqual(FakeScorer.calls, 1)      # one concept, emoji set skipped
                vision.build(src, out, hours=1)
                self.assertEqual(FakeScorer.calls, 1)      # unchanged set is not looked at again
            self.assertFalse((out / "emo.json.gz").exists())
            with mock.patch.object(vision, "VISION_DIR", out):
                vision._load.cache_clear()
                v = vision.votes("demo", "paper-plane", "paper-plane", weight=1.0)
                self.assertAlmostEqual(v["communication"], 0.7)
                self.assertEqual(vision.votes("demo", "paper-plane", "paper-plane", weight=0.0), {})
                # without vision a paper plane is filed under transport; strong vision votes move it
                self.assertEqual(categories_for("paper-plane", None, None, "demo")[0], "transport")
                self.assertEqual(categories_for("paper-plane", None, None, "demo", {"communication": 3.0})[0],
                                 "communication")
            vision._load.cache_clear()

    def test_default_weight_is_off(self):
        cfg = json.loads((ROOT / "config.json").read_text())
        self.assertIn("vision_weight", cfg)


if __name__ == "__main__":
    unittest.main()
