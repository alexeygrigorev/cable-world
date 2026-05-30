from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA_MODEL = ROOT / "docs" / "data-model.md"


class DataModelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DATA_MODEL.read_text(encoding="utf-8")

    def test_document_exists_and_is_russian(self) -> None:
        self.assertTrue(DATA_MODEL.exists(), "Документ доменной модели должен существовать")
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters, "Документ должен быть преимущественно на русском")

    def test_required_entities_are_named(self) -> None:
        for entity in ["TransportObject", "Visit", "MediaAsset", "Ticket", "VisitStatus", "OperationalStatus"]:
            self.assertIn(entity, self.text)

    def test_two_level_map_model_is_documented_without_schema_change(self) -> None:
        for term in [
            "объектная карта",
            "детальная схема объекта",
            "одной точкой",
            "начало и конец",
            "направление видео",
            "foundation для #20/#21",
            "003_media_geo_routes.sql",
        ]:
            self.assertIn(term, self.text)

        for entity in ["ObjectStation", "RouteDirection", "RouteSegment", "EngineeringPoint"]:
            self.assertIn(entity, self.text)

        for detail in [
            "станция",
            "платформа",
            "приводное колесо",
            "отрезок маршрута",
            "направление поездки",
        ]:
            self.assertIn(detail, self.text)

    def test_media_geotags_and_route_labels_are_documented(self) -> None:
        for term in [
            "coordinate_source",
            "`exif`, `manual`, `unknown`",
            "geo_note",
            "человекочитаемая русская заметка",
            "from_station_id",
            "to_station_id",
            "direction_label",
            "от Киенбергпарка к Садам мира",
            "вверх к Волькенхайну",
            "вниз к Садам мира",
        ]:
            self.assertIn(term, self.text)

        for stable_id in [
            "berlin-gaerten-der-welt-station-kienbergpark",
            "berlin-gaerten-der-welt-station-wolkenhain",
            "berlin-gaerten-der-welt-station-gaerten-der-welt",
            "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten",
            "berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark",
            "berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten",
        ]:
            self.assertIn(f"`{stable_id}`", self.text)

    def test_visit_statuses_are_fixed(self) -> None:
        expected_statuses = {
            "not_visited": "не посещен",
            "planned": "запланирован",
            "visited": "посещен",
            "favorite": "любимый",
        }
        for status_id, title in expected_statuses.items():
            self.assertIn(f"`{status_id}`", self.text)
            self.assertIn(title, self.text)

    def test_operational_statuses_are_separate_from_visit_statuses(self) -> None:
        expected_statuses = [
            "active",
            "active_seasonal",
            "temporarily_closed_planned",
            "temporarily_closed_unplanned",
            "closed",
            "historical",
            "unknown",
        ]
        for status_id in expected_statuses:
            self.assertIn(f"`{status_id}`", self.text)
        for field in [
            "operational_status",
            "status_checked_at",
            "status_source_url",
            "status_note",
            "не связан с семейным посещением",
        ]:
            self.assertIn(field, self.text)

    def test_sqlite_tables_are_documented(self) -> None:
        for table in [
            "visit_statuses",
            "transport_types",
            "transport_objects",
            "visits",
            "media_assets",
            "object_stations",
            "route_directions",
            "route_segments",
            "tickets",
        ]:
            self.assertRegex(self.text, rf"CREATE TABLE {table}\b")

    def test_transport_types_are_explicit(self) -> None:
        expected_types = [
            "cable_gondola",
            "cable_aerial_tram",
            "cable_urban",
            "cable_tourist",
            "funicular_classic",
            "funicular_water",
            "funicular_modern",
            "rail_cog",
            "rail_mountain",
            "rail_suspended",
            "elevator_vertical",
            "elevator_inclined",
            "elevator_panoramic",
            "suspended_train",
            "monorail",
            "suspended_ferry",
            "escalator_unusual",
            "special_transport_system",
            "unique_engineering_object",
        ]
        for transport_type in expected_types:
            self.assertIn(f"`{transport_type}`", self.text)

    def test_demo_data_mapping_is_documented_without_requiring_code_change(self) -> None:
        self.assertIn("Демо-данные", self.text)
        self.assertIn("TransportObject", self.text)
        self.assertIn("transport_type_id", self.text)
        self.assertIn("visit_status_id", self.text)
        self.assertIn("operational_status", self.text)


if __name__ == "__main__":
    unittest.main()
