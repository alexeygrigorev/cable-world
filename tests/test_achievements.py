from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT))

from scripts.achievements import calculate_achievements  # noqa: E402


class AchievementsTest(unittest.TestCase):
    def test_first_achievements_unlock_from_visited_local_objects(self) -> None:
        achievements = calculate_achievements(
            [
                {
                    "id": "planned-funicular",
                    "name": "Запланированный фуникулер",
                    "visit_status_id": "planned",
                    "transport_type_id": "funicular_classic",
                },
                {
                    "id": "visited-funicular",
                    "name": "Посещенный фуникулер",
                    "visit_status_id": "visited",
                    "transport_type_id": "funicular_water",
                },
                {
                    "id": "favorite-cableway",
                    "name": "Любимая канатная дорога",
                    "visit_status_id": "favorite",
                    "transport_type_id": "cable_gondola",
                },
                {
                    "id": "visited-suspended-train",
                    "name": "Посещенный подвесной поезд",
                    "visit_status_id": "visited",
                    "transport_type_id": "suspended_train",
                },
            ]
        )

        by_id = {achievement["id"]: achievement for achievement in achievements}
        self.assertTrue(by_id["first_funicular"]["unlocked"])
        self.assertEqual(by_id["first_funicular"]["matched_object_id"], "visited-funicular")
        self.assertEqual(by_id["first_funicular"]["progress_text"], "Посещенный фуникулер")
        self.assertTrue(by_id["first_cableway"]["unlocked"])
        self.assertEqual(by_id["first_cableway"]["matched_object_id"], "favorite-cableway")
        self.assertTrue(by_id["first_suspended_train"]["unlocked"])
        self.assertEqual(by_id["first_suspended_train"]["matched_object_id"], "visited-suspended-train")

    def test_planned_and_not_visited_do_not_unlock_achievements(self) -> None:
        achievements = calculate_achievements(
            [
                {
                    "id": "planned-cableway",
                    "name": "План",
                    "visit_status_id": "planned",
                    "transport_type_id": "cable_urban",
                },
                {
                    "id": "new-suspended-train",
                    "name": "Новый объект",
                    "visit_status_id": "not_visited",
                    "transport_type_id": "suspended_train",
                },
            ]
        )

        self.assertEqual([achievement["unlocked"] for achievement in achievements], [False, False, False])
        for achievement in achievements:
            self.assertEqual(achievement["status_text"], "Еще не получено")
            self.assertEqual(achievement["progress_text"], "Отметьте объект как посещенный или любимый.")
            self.assertEqual(achievement["matched_object_id"], "")

    def test_achievement_ids_are_ascii_and_titles_are_russian(self) -> None:
        achievements = calculate_achievements([])

        for achievement in achievements:
            self.assertIsNone(re.search(r"[А-Яа-яЁё]", achievement["id"]))
            self.assertRegex(achievement["id"], r"^[a-z0-9_]+$")
            self.assertGreater(len(re.findall(r"[А-Яа-яЁё]", achievement["title"])), 0)
            self.assertGreater(len(re.findall(r"[А-Яа-яЁё]", achievement["description"])), 0)

    def test_godot_achievements_script_exposes_same_contract(self) -> None:
        script_text = (ROOT / "scripts" / "achievements.gd").read_text(encoding="utf-8")
        for expected in [
            "class_name Achievements",
            "static func calculate(objects: Array[Dictionary]) -> Array[Dictionary]:",
            '"first_funicular"',
            '"first_cableway"',
            '"first_suspended_train"',
            '"Первый фуникулер"',
            '"Первая канатная дорога"',
            '"Первый подвесной поезд"',
            "STATUS_FAVORITE",
            "status_is_visited",
        ]:
            self.assertIn(expected, script_text)


if __name__ == "__main__":
    unittest.main()
