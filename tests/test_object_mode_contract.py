from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "object-mode-contract.md"
DATA_MODEL = ROOT / "docs" / "data-model.md"


class ObjectModeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")
        cls.data_model_text = DATA_MODEL.read_text(encoding="utf-8")

    def test_contract_exists_and_is_russian(self) -> None:
        self.assertTrue(CONTRACT.exists(), "Object mode contract document must exist")
        self.assertIn("# Контракт Object Mode", self.text)
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_object_mode_starts_from_selected_transport_object(self) -> None:
        for term in [
            "Object mode всегда открывается из выбранного `TransportObject`",
            "не создает отдельный объект каталога",
            "transport_object_id",
            "выбранный `TransportObject` -> детальная схема -> станция -> поездка",
            "один `TransportObject` равен одной точке",
        ]:
            self.assertIn(term, self.text)

    def test_required_model_entities_and_fields_are_documented(self) -> None:
        for term in [
            "ObjectStation",
            "RouteDirection",
            "RouteSegment",
            "EngineeringPoint",
            "hotspot",
            "`from_station_id`",
            "`to_station_id`",
            "`direction_label`",
            "`segment_order`",
            "`point_type`",
            "`station_id`",
            "`route_segment_id`",
            "`MediaAsset.station_id`",
            "`MediaAsset.route_direction_id`",
            "`MediaAsset.route_segment_id`",
        ]:
            self.assertIn(term, self.text)

    def test_empty_states_are_russian_and_non_destructive(self) -> None:
        for term in [
            "Объект не выбран",
            "Для этого объекта пока нет станций схемы",
            "Для этого объекта пока нет направления поездки",
            "Для этого направления пока нет отрезков маршрута",
            "Инженерные точки для этого объекта пока не добавлены",
            "Для этого места пока нет материалов",
            "не должны менять `visit_status_id`, `operational_status`",
        ]:
            self.assertIn(term, self.text)

    def test_i18n_ready_ids_are_separate_from_display_text(self) -> None:
        for term in [
            "I18n-Ready Идентификаторы",
            "стабильными ASCII-идентификаторами",
            "не переводятся",
            "не строятся из текущего UI-языка",
            "`title`",
            "`direction_label`",
            "`note`",
            "`caption`",
            "`geo_note`",
        ]:
            self.assertIn(term, self.text)

    def test_berlin_gaerten_der_welt_is_named_as_vertical_slice(self) -> None:
        for term in [
            "Вертикальный Срез Berlin",
            "`berlin-gaerten-der-welt` является главным вертикальным срезом object mode",
            "TransportObject.id = berlin-gaerten-der-welt",
            "Киенбергпарк",
            "Волькенхайн",
            "Сады мира",
            "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten",
        ]:
            self.assertIn(term, self.text)

    def test_contract_requires_data_driven_object_mode_not_ui_hardcode(self) -> None:
        for term in [
            "строится из данных модели",
            "а не из случайной схемы, UI hardcode или генерации станций на клиенте",
            "не придумывает случайные станции",
            "не хранит названия станций или порядок движения в UI-коде",
            "отсутствие hardcode названий станций и маршрута в object mode UI",
        ]:
            self.assertIn(term, self.text)

    def test_data_model_links_to_object_mode_contract(self) -> None:
        for term in [
            "docs/object-mode-contract.md",
            "выбранный `TransportObject` -> детальная схема -> станция -> поездка",
            "i18n-ready id",
            "вертикальный срез `berlin-gaerten-der-welt`",
        ]:
            self.assertIn(term, self.data_model_text)


if __name__ == "__main__":
    unittest.main()
