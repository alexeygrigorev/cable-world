extends RefCounted
class_name DemoCatalog

static func get_objects() -> Array[Dictionary]:
	return [
		{
			"id": "vorobyovy-gory",
			"name": "Канатная дорога на Воробьевых горах",
			"kind": "канатная дорога",
			"region": "Москва",
			"coordinates": Vector2(37.5517, 55.7103),
			"description": "Городская канатная дорога через Москву-реку с видом на университет и стадион.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить расписание и семейный тариф перед поездкой."
		},
		{
			"id": "nizhny-novgorod",
			"name": "Нижегородская канатная дорога",
			"kind": "междугородная канатная дорога",
			"region": "Нижний Новгород",
			"coordinates": Vector2(44.0186, 56.3299),
			"description": "Маршрут над Волгой между Нижним Новгородом и Бором.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хороший кандидат для первой большой карточки с фото и билетами."
		},
		{
			"id": "vladivostok-funicular",
			"name": "Владивостокский фуникулер",
			"kind": "фуникулер",
			"region": "Владивосток",
			"coordinates": Vector2(131.8939, 43.1187),
			"description": "Короткий городской фуникулер на сопке Орлиное Гнездо.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Добавить историю сооружения и видовые точки."
		}
	]
