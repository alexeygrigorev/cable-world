from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from scripts.collection_stats import (  # noqa: E402
    calculate_collection_stats,
    status_is_visited,
)


class CollectionStatsTest(unittest.TestCase):
    def test_counts_overall_country_and_transport_type_progress(self) -> None:
        stats = calculate_collection_stats(
            [
                {
                    "id": "ru-visited",
                    "visit_status_id": "visited",
                    "country": "Россия",
                    "transport_type_id": "cable_urban",
                    "transport_type_title": "городская канатная дорога",
                },
                {
                    "id": "ru-favorite",
                    "visit_status_id": "favorite",
                    "country": "Россия",
                    "transport_type_id": "cable_urban",
                    "transport_type_title": "городская канатная дорога",
                },
                {
                    "id": "de-planned",
                    "visit_status_id": "planned",
                    "country": "Германия",
                    "transport_type_id": "funicular_classic",
                    "transport_type_title": "классический фуникулер",
                },
                {
                    "id": "de-new",
                    "visit_status_id": "not_visited",
                    "country": "Германия",
                    "transport_type_id": "funicular_classic",
                    "transport_type_title": "классический фуникулер",
                },
            ]
        )

        self.assertEqual(stats["total_count"], 4)
        self.assertEqual(stats["visited_count"], 2)
        self.assertEqual(stats["progress_percent"], 50)
        self.assertEqual(stats["overall"]["title"], "Вся коллекция")

        countries = {country["id"]: country for country in stats["countries"]}
        self.assertEqual(countries["ru"]["title"], "Россия")
        self.assertEqual(countries["ru"]["visited_count"], 2)
        self.assertEqual(countries["ru"]["progress_percent"], 100)
        self.assertEqual(countries["de"]["title"], "Германия")
        self.assertEqual(countries["de"]["visited_count"], 0)
        self.assertEqual(countries["de"]["progress_percent"], 0)

        transport_types = {transport_type["id"]: transport_type for transport_type in stats["transport_types"]}
        self.assertEqual(transport_types["cable_urban"]["visited_count"], 2)
        self.assertEqual(transport_types["funicular_classic"]["visited_count"], 0)

    def test_recalculate_after_visit_status_change(self) -> None:
        objects = [
            {
                "id": "object-1",
                "visit_status_id": "planned",
                "country": "Россия",
                "transport_type_id": "cable_gondola",
                "transport_type_title": "гондольная канатная дорога",
            }
        ]

        before = calculate_collection_stats(objects)
        objects[0]["visit_status_id"] = "favorite"
        after = calculate_collection_stats(objects)

        self.assertEqual(before["visited_count"], 0)
        self.assertEqual(before["progress_percent"], 0)
        self.assertEqual(after["visited_count"], 1)
        self.assertEqual(after["progress_percent"], 100)

    def test_visit_status_ids_define_visited_semantics(self) -> None:
        self.assertFalse(status_is_visited("not_visited"))
        self.assertFalse(status_is_visited("planned"))
        self.assertTrue(status_is_visited("visited"))
        self.assertTrue(status_is_visited("favorite"))

    def test_group_identifiers_are_not_russian_strings(self) -> None:
        stats = calculate_collection_stats(
            [
                {
                    "id": "object-1",
                    "visit_status_id": "visited",
                    "country": "Россия",
                    "transport_type_id": "rail_cog",
                    "transport_type_title": "зубчатая железная дорога",
                }
            ]
        )

        for group in [stats["overall"], *stats["countries"], *stats["transport_types"]]:
            self.assertIsNone(re.search(r"[А-Яа-яЁё]", group["id"]))
            self.assertRegex(group["id"], r"^[a-z0-9_]+$")
            self.assertGreater(len(re.findall(r"[А-Яа-яЁё]", group["title"])), 0)

    def test_godot_collection_stats_script_exposes_same_contract(self) -> None:
        script_text = (ROOT / "scripts" / "collection_stats.gd").read_text(encoding="utf-8")
        for expected in [
            "class_name CollectionStats",
            "static func calculate(objects: Array[Dictionary]) -> Dictionary:",
            '"overall"',
            '"countries"',
            '"transport_types"',
            "STATUS_FAVORITE",
            "status_is_visited",
            '"Вся коллекция"',
        ]:
            self.assertIn(expected, script_text)


if __name__ == "__main__":
    unittest.main()
