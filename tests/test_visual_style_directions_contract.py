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

    def test_has_at_least_three_visual_style_variants(self) -> None:
        variants = re.findall(r"^## Вариант \d+:", self.text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(variants), 3)
        for expected in [
            "детская иллюстрированная карта",
            "пиксель-арт",
            "инженерный атлас",
            "настольная игра",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_each_variant_covers_required_design_dimensions(self) -> None:
        for expected in [
            "Настроение",
            "Палитра",
            "UI-компоненты",
            "Карта",
            "Маркеры",
            "Карточки объектов",
            "Достижения",
            "Режим поездки / наблюдатель",
            "Плюсы",
            "Минусы",
            "Трудозатраты",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_recommended_style_is_explicit(self) -> None:
        for expected in [
            "Рекомендованный стиль для MVP/1.0",
            "Рекомендуемый стиль",
            "детская иллюстрированная карта с элементами настольной игры и наклеек",
            "семейный проект",
            "без GIS",
            "MVP/1.0",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_map_art_plan_without_gis_is_documented(self) -> None:
        for expected in [
            "Как реализовать игровую карту без GIS",
            "Фон-картинка",
            "Слои",
            "Normalized positions",
            "map_x",
            "map_y",
            "0.0..1.0",
            "zoom/pan",
            "Clusters/labels",
            "fallback на список",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_incremental_plan_order_is_fixed(self) -> None:
        ordered = [
            "Style tokens/theme",
            "Map art layer",
            "Маркеры/иконки",
            "Карточки/достижения",
        ]
        positions = [self.text.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
