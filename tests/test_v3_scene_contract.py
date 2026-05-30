from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "v3-scene-contract.md"
DATA_MODEL = ROOT / "docs" / "data-model.md"


class V3SceneContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_text = CONTRACT.read_text(encoding="utf-8")
        cls.data_model_text = DATA_MODEL.read_text(encoding="utf-8")

    def test_contract_exists_and_is_russian(self) -> None:
        self.assertTrue(CONTRACT.exists(), "Контракт V3-сцены должен существовать")
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.contract_text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.contract_text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_contract_is_post_1_0_and_does_not_block_mvp(self) -> None:
        for term in [
            "post-1.0 roadmap",
            "не являются blocker",
            "пользовательской цели 1.0",
            "Для 1.0 обязательными остаются",
            "MVP-карта",
            "2D-детальная схема",
            "release workflow",
            "версия приложения",
        ]:
            self.assertIn(term, self.contract_text)

    def test_engineering_mode_links_to_existing_model(self) -> None:
        for term in [
            "#32 Инженерный Режим Объекта",
            "transport_object_id",
            "`EngineeringPoint`",
            "`ObjectStation`",
            "`RouteDirection`",
            "`RouteSegment`",
            "`MediaAsset.station_id`",
            "`MediaAsset.route_direction_id`",
            "`MediaAsset.route_segment_id`",
        ]:
            self.assertIn(term, self.contract_text)

    def test_walk_mode_links_to_existing_model(self) -> None:
        for term in [
            "#34 Режим Прогулки По Объекту",
            "свободный осмотр",
            "не требует поездки",
            "станции берутся из `ObjectStation`",
            "опоры и подписанные инженерные детали берутся из `EngineeringPoint`",
            "видимый маршрут и канат берутся из `RouteSegment`",
            "`RouteDirection.direction_label`",
            "`RouteSegment.direction_label`",
        ]:
            self.assertIn(term, self.contract_text)

    def test_required_russian_ui_terms_are_present(self) -> None:
        for term in [
            "все видимые строки на русском",
            "двигатель",
            "редуктор",
            "приводное колесо",
            "натяжное колесо",
            "канат",
            "кабина",
            "опора",
            "станция",
            "маршрут",
            "инженерные подписи",
        ]:
            self.assertIn(term, self.contract_text)

    def test_no_3d_or_photogrammetry_implementation_is_required(self) -> None:
        for term in [
            "не требуют 3D",
            "photogrammetry",
            "физики каната",
            "импорта CAD",
            "полноценные 3D-модели объектов",
            "Если V3 потребует отдельные сущности для кабины, каната",
            "отдельная миграция с отдельным contract test",
        ]:
            self.assertIn(term, self.contract_text)

    def test_data_model_links_to_v3_contract(self) -> None:
        self.assertIn("[v3-scene-contract.md](v3-scene-contract.md)", self.data_model_text)
        self.assertIn("post-1.0 roadmap", self.data_model_text)
        self.assertIn("не blocker для пользовательской цели 1.0", self.data_model_text)


if __name__ == "__main__":
    unittest.main()
