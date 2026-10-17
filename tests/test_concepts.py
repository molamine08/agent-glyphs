import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from atlas import concepts  # noqa: E402


class ArabicForms(unittest.TestCase):
    def test_plural_article_and_nisba_reach_the_same_stem(self):
        for w in ("مسلمين", "المسلمون", "مسلمه"):
            self.assertIn("مسلم", concepts.ar_forms(w), w)
        self.assertIn("اسلام", concepts.ar_forms("الإسلامي"))
        self.assertIn("سله", concepts.ar_forms("بالسلة"))

    def test_short_words_are_not_cut(self):
        self.assertEqual(concepts.ar_forms("بيت"), ["بيت"])

    def test_english_forms(self):
        self.assertIn("category", concepts.en_forms("categories"))
        self.assertIn("box", concepts.en_forms("boxes"))


class Expansion(unittest.TestCase):
    def setUp(self):
        concepts.groups.cache_clear()
        concepts.tables.cache_clear()
        self._orig = concepts.groups
        concepts.groups = lambda: [  # noqa: E731
            {"ar": ["مسلم", "إسلام"], "en": ["islam", "muslim"], "rel": ["mosque", "crescent"]},
            {"ar": ["لوحة التحكم", "داشبورد"], "en": ["dashboard"], "rel": ["chart"]},
        ]
        concepts.tables.cache_clear()

    def tearDown(self):
        concepts.groups = self._orig
        concepts.tables.cache_clear()

    def test_word_finds_synonyms_and_related(self):
        (p,) = concepts.expand("المسلمين")
        self.assertEqual(p.strong, {"islam", "muslim"})
        self.assertEqual(p.related, {"mosque", "crescent"})
        self.assertEqual(concepts.level({"mosque"}, "mosque", p), 1)
        self.assertEqual(concepts.level({"islam"}, "islam", p), 3)

    def test_phrase_is_matched_whole(self):
        parts = concepts.expand("لوحة التحكم")
        self.assertEqual(len(parts), 1)
        self.assertIn("dashboard", parts[0].strong)


if __name__ == "__main__":
    unittest.main()
