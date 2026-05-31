extends RefCounted

const AchievementsScript: GDScript = preload("res://scripts/achievements.gd")
const CollectionStatsScript: GDScript = preload("res://scripts/collection_stats.gd")


func test_collection_stats_and_achievements_runtime() -> Array[String]:
	var failures: Array[String] = []
	var objects: Array[Dictionary] = [
		{
			"id": "wuppertal-schwebebahn",
			"name": "Вуппертальская подвесная дорога",
			"country": "Германия",
			"transport_type_id": "suspended_train",
			"transport_type_title": "Подвесной поезд",
			"visit_status_id": "favorite",
		},
		{
			"id": "lisbon-bica",
			"name": "Фуникулер Бика",
			"country": "Португалия",
			"transport_type_id": "funicular_classic",
			"transport_type_title": "Фуникулер",
			"visit_status_id": "planned",
		},
	]

	var stats: Dictionary = CollectionStatsScript.calculate(objects)
	_expect(stats.get("total_count", 0) == 2, "CollectionStats must count all runtime objects.", failures)
	_expect(stats.get("visited_count", 0) == 1, "Favorite object must count as visited.", failures)
	_expect(stats.get("progress_percent", 0) == 50, "Progress must be rounded from visited/total.", failures)

	var achievements: Array[Dictionary] = AchievementsScript.calculate(objects)
	var suspended_train_achievement := _achievement_by_id(achievements, "first_suspended_train")
	var funicular_achievement := _achievement_by_id(achievements, "first_funicular")
	_expect(suspended_train_achievement.get("unlocked", false), "Visited suspended train must unlock its achievement.", failures)
	_expect(
		suspended_train_achievement.get("matched_object_id", "") == "wuppertal-schwebebahn",
		"Achievement must expose the matched runtime object.",
		failures
	)
	_expect(not funicular_achievement.get("unlocked", true), "Planned funicular must not unlock a visited achievement.", failures)

	return failures


func _achievement_by_id(achievements: Array[Dictionary], achievement_id: String) -> Dictionary:
	for achievement in achievements:
		if achievement.get("id", "") == achievement_id:
			return achievement
	return {}


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)
