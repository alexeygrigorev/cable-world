from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA_MODEL = ROOT / "docs" / "data-model.md"


class EngineeringSceneContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DATA_MODEL.read_text(encoding="utf-8")

    def test_engineering_scene_contract_is_documented_in_russian(self) -> None:
        self.assertIn("### Будущая инженерная и игровая сцена", self.text)
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_transport_object_is_root_for_future_scene(self) -> None:
        for term in [
            "`TransportObject` остается корневой записью реального объекта",
            "Будущая 3D/инженерная сцена является представлением выбранного `TransportObject`",
            "не отдельным объектом каталога",
            "transport_object_id",
            "одну и ту же линию, станции, маршрут, медиа и семейную историю",
        ]:
            self.assertIn(term, self.text)

    def test_mvp_stays_2d_without_full_3d_requirement(self) -> None:
        for term in [
            "MVP не требует полноценного 3D",
            "Текущая общая карта остается 2D-картой объектов",
            "детальная схема выбранного объекта остается 2D-схемой",
            "photogrammetry",
            "Three.js",
            "Godot 3D scenes",
            "не входят в MVP",
        ]:
            self.assertIn(term, self.text)

    def test_engineering_details_dictionary_is_fixed(self) -> None:
        for term in [
            "двигатель",
            "редуктор",
            "приводное колесо",
            "натяжное колесо",
            "канат",
            "кабина",
            "опора",
            "станция",
            "ObjectStation",
            "RouteDirection",
            "RouteSegment",
            "EngineeringPoint",
        ]:
            self.assertIn(term, self.text)

    def test_v3_scene_modes_are_named(self) -> None:
        for mode in [
            "прогулка",
            "поездка",
            "наблюдатель",
            "инженерный режим",
            "продуктовые цели V3",
        ]:
            self.assertIn(mode, self.text)


if __name__ == "__main__":
    unittest.main()
