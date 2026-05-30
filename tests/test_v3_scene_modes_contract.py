from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "v3-scene-modes-contract.md"
DATA_MODEL = ROOT / "docs" / "data-model.md"


class V3SceneModesContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")
        cls.data_model_text = DATA_MODEL.read_text(encoding="utf-8")

    def test_contract_exists_and_is_russian(self) -> None:
        self.assertTrue(CONTRACT.exists(), "V3 contract document must exist")
        self.assertIn("# V3 контракт режимов поездки и наблюдателя", self.text)
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_post_1_0_boundary_is_explicit(self) -> None:
        for term in [
            "post-1.0 roadmap",
            "не являются blocker",
            "текущий MVP уже показывает выбранный маршрут в карточке объекта",
            "не реализует полноценный 3D",
            "не блокировать 1.0",
        ]:
            self.assertIn(term, self.text)

    def test_trip_mode_uses_existing_route_model(self) -> None:
        for term in [
            "Режим «поездка»",
            "transport_object_id",
            "route_direction_id",
            "RouteDirection.direction_label",
            "route_segments.segment_order",
            "from_station_id",
            "to_station_id",
            "media_assets",
            "Материалы поездки",
            "Для этой поездки пока нет направления маршрута",
            "Для этого направления пока нет отрезков маршрута",
        ]:
            self.assertIn(term, self.text)

    def test_observer_mode_uses_object_route_and_engineering_terms(self) -> None:
        for term in [
            "Режим «наблюдатель»",
            "внешний обзор объекта",
            "без управления поездкой",
            "кабина",
            "опора",
            "EngineeringPoint",
            "Для наблюдения пока нет схемы маршрута",
            "опоры являются V3-расширением",
        ]:
            self.assertIn(term, self.text)

    def test_contract_links_to_current_2d_card_and_storage_methods(self) -> None:
        for term in [
            "scripts/main_screen.gd",
            "list_object_stations",
            "list_route_directions",
            "list_route_segments",
            "scripts/object_card_panel.gd",
            "Схема маршрута",
            "scripts/storage/migrations/003_media_geo_routes.sql",
            "scripts/storage/seeds/demo_objects.sql",
            "berlin-gaerten-der-welt",
        ]:
            self.assertIn(term, self.text)

    def test_data_model_links_to_v3_contract(self) -> None:
        for term in [
            "docs/v3-scene-modes-contract.md",
            "V3-режимов «поездка» и «наблюдатель»",
            "post-1.0 roadmap",
            "не являются blocker для 1.0",
        ]:
            self.assertIn(term, self.data_model_text)


if __name__ == "__main__":
    unittest.main()
