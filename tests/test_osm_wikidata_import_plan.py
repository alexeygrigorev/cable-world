from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "osm-wikidata-import-plan.md"


class OsmWikidataImportPlanContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PLAN.read_text(encoding="utf-8")

    def test_document_exists_and_is_russian(self) -> None:
        self.assertTrue(PLAN.exists(), "План импорта OSM/Wikidata должен существовать")
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_minimal_staging_json_is_valid_and_matches_transport_object_contract(self) -> None:
        match = re.search(r"```json\n(.*?)\n```", self.text, flags=re.DOTALL)
        self.assertIsNotNone(match, "Документ должен содержать пример staging JSON")
        example = json.loads(match.group(1))

        for field in [
            "id",
            "transport_type_id",
            "visit_status_id",
            "country",
            "region",
            "city",
            "latitude",
            "longitude",
            "localized",
            "opened_year",
            "operator",
            "manufacturer",
            "operational_status",
            "status_checked_at",
            "status_source_url",
            "status_note",
            "source_ids",
            "source_urls",
            "review",
        ]:
            self.assertIn(field, example)

        self.assertRegex(example["id"], r"^[a-z][a-z0-9-]*$")
        self.assertRegex(example["transport_type_id"], r"^[a-z][a-z0-9_]*$")
        self.assertIn("ru", example["localized"])
        self.assertIn("title", example["localized"]["ru"])
        self.assertIn("description", example["localized"]["ru"])
        self.assertEqual(example["operational_status"], "unknown")

    def test_current_statuses_and_i18n_strategy_are_preserved(self) -> None:
        for status_id in [
            "active",
            "active_seasonal",
            "temporarily_closed_planned",
            "temporarily_closed_unplanned",
            "closed",
            "historical",
            "unknown",
        ]:
            self.assertIn(f"`{status_id}`", self.text)

        for expected in [
            "`ru` обязателен",
            "стабильные id и enum-поля не переводятся",
            "localized.ru",
            "TransportObject.title",
            "TransportObject.description",
        ]:
            self.assertIn(expected, self.text)

    def test_osm_tags_for_target_transport_types_are_documented(self) -> None:
        for tag in [
            "aerialway=*",
            "aerialway=gondola",
            "aerialway=cable_car",
            "aerialway=station",
            "railway=funicular",
            "route=funicular",
            "station=funicular",
            "railway=rail",
            "rack=yes",
            "railway=monorail",
            "route=monorail",
            "monorail=hanging",
            "operator=*",
            "operator:wikidata=*",
            "operator:website=*",
            "website=*",
            "contact:website=*",
            "start_date=*",
            "opening_date=*",
            "check_date=*",
            "wikidata=*",
        ]:
            self.assertIn(f"`{tag}`", self.text)

    def test_wikidata_fields_and_source_ids_are_documented(self) -> None:
        for prop in ["P31", "P279", "P625", "P17", "P137", "P856", "P571", "P1619", "P176", "P402", "P10689", "P11693"]:
            self.assertIn(f"`{prop}`", self.text)

        for expected in [
            "source_ids",
            "source_urls",
            "node/way/relation",
            "OpenStreetMap relation ID",
            "OpenStreetMap way ID",
            "OpenStreetMap node ID",
        ]:
            self.assertIn(expected, self.text)

    def test_recommendation_and_risks_are_explicit(self) -> None:
        for expected in [
            "полуавтоматический импорт",
            "staging JSON",
            "ручную редакторскую проверку",
            "Прямой автоматический импорт",
            "не рекомендуется",
            "Дубликаты",
            "Разная гранулярность",
            "Нестабильные id OSM",
            "Статусы устаревают",
            "Лицензии и атрибуция",
        ]:
            self.assertIn(expected, self.text)

    def test_follow_up_pipeline_issues_have_acceptance_scope(self) -> None:
        for expected in [
            "#28",
            "#29",
            "#30",
            "staging JSON schema",
            "валидатор кандидатов",
            "прототип сборщика кандидатов",
            "Overpass/SPARQL",
            "ручной review workflow",
            'review.state = "approved"',
            "без записи в production-хранилище",
        ]:
            self.assertIn(expected, self.text)


if __name__ == "__main__":
    unittest.main()
