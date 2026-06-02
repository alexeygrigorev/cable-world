from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "visual-style-directions.md"


class VisualStyleDirectionsContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_document_exists_and_is_russian(self) -> None:
        self.assertTrue(DOC.is_file(), "Документ с визуальными стилями должен существовать")
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_recommended_style_is_explicit(self) -> None:
        for expected in [
            "детская иллюстрированная карта",
            "настольной игры",
            "наклеек",
            "русским",
            "390x844",
            "Достижения",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_map_rules_are_documented(self) -> None:
        for expected in [
            "background",
            "regions",
            "water",
            "terrain",
            "cities",
            "objects",
            "labels",
            "selection",
            "coordinates",
            "clusters",
            "fallback",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_incremental_plan_order_is_fixed(self) -> None:
        ordered = [
            "Style tokens",
            "Map art layer",
            "Glyphs",
            "Markers",
            "Cards and achievements",
        ]
        positions = [self.text.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
