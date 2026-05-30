extends RefCounted
class_name DemoCatalogEurope

const OPERATIONAL_STATUS_BY_ID := {
	"braga-bom-jesus-funicular": {
		"operational_status": "unknown",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://bomjesus.pt/bom-jesus/elevator-or-funicular/",
		"status_note": "Нужно подтвердить актуальное расписание перед переносом в основной каталог."
	},
	"grenoble-bastille-cable-car": {
		"operational_status": "unknown",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://bastille-grenoble.fr/en/",
		"status_note": "Официальный сайт есть; перед поездкой нужно проверить часы работы и плановое обслуживание."
	},
	"como-brunate-funicular": {
		"operational_status": "unknown",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.funicolarecomo.it/",
		"status_note": "Перед переносом в основной каталог нужно проверить оператора и актуальное расписание."
	},
	"prague-petrin-funicular": {
		"operational_status": "temporarily_closed_planned",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.dpp.cz/en/entertainment-and-experience/funicular-to-petrin",
		"status_note": "DPP сообщает о приостановке работы из-за полной реконструкции; пассажирские тесты ожидаются на рубеже лета и осени 2026."
	},
	"stary-smokovec-hrebienok-funicular": {
		"operational_status": "unknown",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://visittatry.sk/en/post/cable-cars",
		"status_note": "Перед переносом в основной каталог нужно проверить сезонное расписание и официальный статус у оператора."
	},
	"zakopane-kasprowy-wierch-cable-car": {
		"operational_status": "unknown",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.pkl.pl/kasprowy-wierch/kolej-linowa-kasprowy-wierch.html?setlang=1",
		"status_note": "Перед поездкой нужно проверить погодные ограничения, лимиты парка и фактическое расписание."
	}
}

static func get_operational_status_by_id() -> Dictionary:
	return OPERATIONAL_STATUS_BY_ID.duplicate(true)

static func get_objects() -> Array[Dictionary]:
	var objects: Array[Dictionary] = [
		{
			"id": "braga-bom-jesus-funicular",
			"name": "Фуникулер Bom Jesus do Monte",
			"kind": "водобалластный фуникулер",
			"region": "Брага",
			"coordinates": Vector2(-8.3778, 41.5547),
			"description": "Водобалластный фуникулер у святилища Bom Jesus do Monte в Браге; редкая технология для семейного исследования.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить координату нижней станции и текущий график работы перед поездкой.",
			"transport_type_id": "funicular_water",
			"country": "Португалия",
			"city": "Брага",
			"latitude": 41.5547,
			"longitude": -8.3778,
			"opened_year": 1882,
			"operator": "Irmandade do Bom Jesus do Monte",
			"manufacturer": null
		},
		{
			"id": "grenoble-bastille-cable-car",
			"name": "Канатная дорога Grenoble-Bastille",
			"kind": "городская туристическая канатная дорога",
			"region": "Овернь — Рона — Альпы",
			"coordinates": Vector2(5.7265, 45.1939),
			"description": "Городская туристическая канатная дорога из центра Гренобля к крепости Бастилия.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хороший объект для карточки с видом на город и сравнением старых и современных кабинок.",
			"transport_type_id": "cable_tourist",
			"country": "Франция",
			"city": "Гренобль",
			"latitude": 45.1939,
			"longitude": 5.7265,
			"opened_year": 1934,
			"operator": "Régie du Téléphérique Grenoble Bastille",
			"manufacturer": null
		},
		{
			"id": "como-brunate-funicular",
			"name": "Фуникулер Комо — Брунате",
			"kind": "классический фуникулер",
			"region": "Ломбардия",
			"coordinates": Vector2(9.0835, 45.8148),
			"description": "Классический фуникулер, соединяющий Комо с Брунате над озером Комо.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Уточнить оператора и расписание; объект подходит для маршрута от озера к смотровой точке.",
			"transport_type_id": "funicular_classic",
			"country": "Италия",
			"city": "Комо",
			"latitude": 45.8148,
			"longitude": 9.0835,
			"opened_year": 1894,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "prague-petrin-funicular",
			"name": "Пражский фуникулер на Петршин",
			"kind": "классический фуникулер",
			"region": "Прага",
			"coordinates": Vector2(14.4039, 50.0838),
			"description": "Фуникулер Уезд — Петршин в Праге; на дату среза находится в плановой реконструкции.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Не показывать как работающий объект, пока реконструкция не завершена и статус не обновлен.",
			"transport_type_id": "funicular_classic",
			"country": "Чехия",
			"city": "Прага",
			"latitude": 50.0838,
			"longitude": 14.4039,
			"opened_year": 1891,
			"operator": "Dopravní podnik hl. m. Prahy",
			"manufacturer": null
		},
		{
			"id": "stary-smokovec-hrebienok-funicular",
			"name": "Фуникулер Старый Смоковец — Гребиенок",
			"kind": "горный фуникулер",
			"region": "Прешовский край",
			"coordinates": Vector2(20.2224, 49.1419),
			"description": "Горный фуникулер в Высоких Татрах между Старым Смоковцем и туристическим узлом Гребиенок.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Уточнить координату нижней станции и сезонный статус перед семейной поездкой.",
			"transport_type_id": "funicular_classic",
			"country": "Словакия",
			"city": "Высокие Татры",
			"latitude": 49.1419,
			"longitude": 20.2224,
			"opened_year": 1908,
			"operator": "Tatry mountain resorts",
			"manufacturer": null
		},
		{
			"id": "zakopane-kasprowy-wierch-cable-car",
			"name": "Канатная дорога на Каспровы Верх",
			"kind": "маятниковая канатная дорога",
			"region": "Малопольское воеводство",
			"coordinates": Vector2(19.981, 49.232),
			"description": "Высокогорная канатная дорога PKL из Кузнице на Каспровы Верх в Татрах.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить погоду, ограничения национального парка и фактическое расписание на день поездки.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Польша",
			"city": "Закопане",
			"latitude": 49.232,
			"longitude": 19.981,
			"opened_year": 1936,
			"operator": "Polskie Koleje Linowe",
			"manufacturer": null
		}
	]

	return objects
