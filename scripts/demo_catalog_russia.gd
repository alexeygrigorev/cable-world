extends RefCounted
class_name DemoCatalogRussia

const OPERATIONAL_STATUS_BY_ID := {
	"nizhny-novgorod-bor-cable-car": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.borcity.ru/activity/transport/kanatka.php?special_version=Y",
		"status_note": "Статус и координаты нужно сверить с оператором/OSM перед production seed."
	},
	"moscow-vorobyovy-gory-cable-car": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://srkvg.ru/kanatnaya-doroga/",
		"status_note": "Официальный сайт описывает маршрут и функции дороги; перед seed уточнить координаты станций."
	},
	"vladivostok-funicular": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.vladivostok.travel/todo/funicular/",
		"status_note": "Туристический портал и новости подтверждают действующую работу после ремонтов; требуется сверка расписания."
	},
	"nizhny-novgorod-kremlin-funicular": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://kremlnn.ru/funicular",
		"status_note": "Официальный сайт указывает режим и зимние температурные ограничения; координаты ориентировочные."
	},
	"pyatigorsk-mashuk-cable-car": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://kanatkakmw.ru/",
		"status_note": "Регламентные закрытия возможны; перед seed проверить текущий режим работы."
	},
	"svetlogorsk-panorama-elevator": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://liftsvetlogorsk.ru/",
		"status_note": "Перед seed уточнить год открытия и точку привязки нижней/верхней станции."
	},
	"moscow-monorail": {
		"operational_status": "historical",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://transport.mos.ru/mostrans/all_news/125075",
		"status_note": "Единый транспортный портал Москвы сообщил, что монорельс завершит работу 28 июня 2025 года."
	}
}

static func get_operational_status_by_id() -> Dictionary:
	return OPERATIONAL_STATUS_BY_ID.duplicate(true)

static func get_objects() -> Array[Dictionary]:
	var objects: Array[Dictionary] = [
		{
			"id": "nizhny-novgorod-bor-cable-car",
			"name": "Нижегородская канатная дорога",
			"kind": "городская канатная дорога",
			"region": "Нижегородская область",
			"coordinates": Vector2(44.0168, 56.3309),
			"description": "Городская канатная дорога через Волгу между Нижним Новгородом и Бором.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Высокий приоритет для российского каталога; перед основным seed сверить станции и источники.",
			"transport_type_id": "cable_urban",
			"country": "Россия",
			"city": "Нижний Новгород / Бор",
			"latitude": 56.3309,
			"longitude": 44.0168,
			"opened_year": 2012,
			"operator": "АО \"Нижегородские канатные дороги\"",
			"manufacturer": null
		},
		{
			"id": "moscow-vorobyovy-gory-cable-car",
			"name": "Московская канатная дорога",
			"kind": "городская канатная дорога",
			"region": "Москва",
			"coordinates": Vector2(37.5429, 55.7106),
			"description": "Канатная дорога между Воробьевыми горами, Новой Лигой и Лужниками.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Используется staging id; интегратор отдельно решит дедупликацию с legacy seed.",
			"transport_type_id": "cable_urban",
			"country": "Россия",
			"city": "Москва",
			"latitude": 55.7106,
			"longitude": 37.5429,
			"opened_year": 2018,
			"operator": "ООО \"Московские канатные дороги\"",
			"manufacturer": null
		},
		{
			"id": "vladivostok-funicular",
			"name": "Владивостокский фуникулер",
			"kind": "классический фуникулер",
			"region": "Приморский край",
			"coordinates": Vector2(131.8998, 43.1168),
			"description": "Классический городской фуникулер на склоне сопки Орлиной между улицами Пушкинской и Суханова.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Один из самых важных российских фуникулеров для начальной подборки.",
			"transport_type_id": "funicular_classic",
			"country": "Россия",
			"city": "Владивосток",
			"latitude": 43.1168,
			"longitude": 131.8998,
			"opened_year": 1962,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "nizhny-novgorod-kremlin-funicular",
			"name": "Кремлевский фуникулер в Нижнем Новгороде",
			"kind": "современный фуникулер",
			"region": "Нижегородская область",
			"coordinates": Vector2(44.0057, 56.3282),
			"description": "Восстановленный фуникулер у Нижегородского кремля, открытый заново в 2024 году.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Новый российский фуникулер с сильной исторической ценностью.",
			"transport_type_id": "funicular_modern",
			"country": "Россия",
			"city": "Нижний Новгород",
			"latitude": 56.3282,
			"longitude": 44.0057,
			"opened_year": 2024,
			"operator": "ГБУК НО \"Нижегородский государственный историко-архитектурный музей-заповедник\"",
			"manufacturer": null
		},
		{
			"id": "pyatigorsk-mashuk-cable-car",
			"name": "Пятигорская канатная дорога на Машук",
			"kind": "маятниковая канатная дорога",
			"region": "Ставропольский край",
			"coordinates": Vector2(43.0838, 44.0479),
			"description": "Маятниковая канатная дорога от бульвара Гагарина к вершине горы Машук.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Высокий приоритет для Кавказских Минеральных Вод.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Россия",
			"city": "Пятигорск",
			"latitude": 44.0479,
			"longitude": 43.0838,
			"opened_year": 1971,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "svetlogorsk-panorama-elevator",
			"name": "Панорамный лифт \"Панорама\" в Светлогорске",
			"kind": "панорамный лифт",
			"region": "Калининградская область",
			"coordinates": Vector2(20.1538, 54.9447),
			"description": "Панорамный лифт у морского побережья Светлогорска, работающий как видовой инженерный объект и вертикальная связь.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хороший российский пример для типа elevator_panoramic.",
			"transport_type_id": "elevator_panoramic",
			"country": "Россия",
			"city": "Светлогорск",
			"latitude": 54.9447,
			"longitude": 20.1538,
			"opened_year": null,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "moscow-monorail",
			"name": "Московский монорельс",
			"kind": "монорельс",
			"region": "Москва",
			"coordinates": Vector2(37.6404, 55.8214),
			"description": "Историческая городская монорельсовая линия на северо-востоке Москвы, закрытая для пассажирской работы в 2025 году.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Исторический объект: интегратор решит, показывать ли закрытые системы в основном каталоге.",
			"transport_type_id": "monorail",
			"country": "Россия",
			"city": "Москва",
			"latitude": 55.8214,
			"longitude": 37.6404,
			"opened_year": 2004,
			"operator": "Московский транспорт",
			"manufacturer": null
		}
	]
	return objects
