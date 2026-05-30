extends RefCounted
class_name DemoCatalog

const DemoCatalogEuropeScript := preload("res://scripts/demo_catalog_europe.gd")
const DemoCatalogRussiaScript := preload("res://scripts/demo_catalog_russia.gd")

const DEFAULT_OPERATIONAL_STATUS := {
	"operational_status": "unknown",
	"status_checked_at": "",
	"status_source_url": "",
	"status_note": "Эксплуатационный статус еще не проверен."
}

const OPERATIONAL_STATUS_BY_ID := {
	"berlin-gaerten-der-welt": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.gaertenderwelt.de/erlebnisse/seilbahn/",
		"status_note": "Сезонный график на 2026 год: апрель-сентябрь ежедневно 10:00-19:00; при сильном ветре или грозе возможна остановка."
	},
	"thale-hexentanzplatz": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.seilbahnen-thale.de/en/rosstrappe",
		"status_note": "Оператор показывает дневную доступность аттракционов; перед поездкой нужно проверить часы и погоду."
	},
	"thale-rosstrappe": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.seilbahnen-thale.de/en/rosstrappe",
		"status_note": "Оператор показывает дневную доступность аттракционов; перед поездкой нужно проверить часы и погоду."
	},
	"stuttgart-standseilbahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://embedded.ssb-ag.de/unternehmen/informationen-fakten/fahrzeuge/seilbahn/",
		"status_note": "Городская линия 20 SSB, действующий маршрут общественного транспорта."
	},
	"stuttgart-zahnradbahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.ssb-ag.de/unternehmen/informationen-fakten/fahrzeuge/zahnradbahn/",
		"status_note": "Городская линия 10 SSB; действующая зубчатая дорога с регулярным расписанием."
	},
	"bayerische-zugspitzbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://zugspitze.de/de/Service-Informationen/Betriebszeiten-Fahrplaene",
		"status_note": "Опубликованы рабочие часы и плановые ревизии на 2026 год; перед поездкой проверить погоду и текущий статус."
	},
	"seilbahn-zugspitze": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://zugspitze.de/de/Service-Informationen/Betriebszeiten-Fahrplaene",
		"status_note": "Опубликованы рабочие часы и плановые ревизии на 2026 год; перед поездкой проверить погоду и текущий статус."
	},
	"zugspitze-gletscherbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://zugspitze.de/de/Service-Informationen/Betriebszeiten-Fahrplaene",
		"status_note": "Опубликованы рабочие часы и плановые ревизии на 2026 год; перед поездкой проверить погоду и текущий статус."
	},
	"wuppertaler-schwebebahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://schwebebahn.de/",
		"status_note": "Регулярный городской транспорт; перед поездкой проверить текущие Verkehrsinformationen."
	},
	"dresden-schwebebahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.dvb.de/de-de/entdecken/bergbahnen/",
		"status_note": "DVB публикует рабочие графики и периоды ревизии для дрезденских горных дорог."
	},
	"dresden-standseilbahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.dvb.de/de-de/entdecken/bergbahnen/",
		"status_note": "DVB публикует рабочие графики и периоды ревизии для дрезденских горных дорог."
	},
	"nerobergbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.wiesbaden.de/fr/leben-in-wiesbaden/freizeit/ausfluege/nerobergbahn-neroberg",
		"status_note": "Сезон 2026 начался 3 апреля; линия работает ежедневно до конца осени."
	},
	"bad-schandau-lift": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.saechsische-schweiz.de/ausflugsziele/historischer-personenaufzug-badschandau",
		"status_note": "Опубликованы круглогодичные часы работы с разным временем по месяцам."
	},
	"heidelberg-bergbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.bergbahn-heidelberg.de/",
		"status_note": "Горная железная дорога работает по сезонным графикам; перед поездкой проверить текущий летний или зимний Fahrplan."
	},
	"bad-harzburg-burgbergseilbahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.bad-harzburg.de/wanderland/burgberg-seilbahn/",
		"status_note": "Опубликованы летние и зимние Fahrzeiten; плановая ревизия указана на ноябрь 2026 года."
	},
	"wurmbergseilbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://wurmberg-seilbahn.de/sommer.html",
		"status_note": "Оператор показывает текущий статус как открыто и публикует дневные часы работы."
	},
	"dortmund-h-bahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.bus-und-bahn.de/h-bahn",
		"status_note": "Действующий автоматический транспорт TU Dortmund; оператор публикует Fahrplan и Verkehrsmeldungen."
	},
	"duesseldorf-skytrain": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.dus.com/en/to-and-from/bus-and-train",
		"status_note": "SkyTrain аэропорта работает ежедневно 03:45-00:45; ночью есть автобусная подмена."
	},
	"baden-baden-merkurbergbahn": {
		"operational_status": "active",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.stadtwerke-baden-baden.de/de/mobilitaet-freizeit/merkurbahn/",
		"status_note": "Оператор публикует часы MerkurBergbahn; после ревизии 2026 объект готов к регулярной работе."
	},
	"koblenz-seilbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.seilbahn-koblenz.de/",
		"status_note": "Туристическая канатная дорога через Рейн; перед поездкой проверить сезонный календарь и спецсобытия."
	},
	"koeln-seilbahn": {
		"operational_status": "active_seasonal",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://www.stadtwerkekoeln.de/pressemitteilungen/saisonstart-kolner-seilbahn-ab-dem-12-marz-heben-die-gondeln-wieder-ab",
		"status_note": "Сезон 2026 стартовал 12 марта; регулярный сезон идет до начала ноября, далее запланированы адвентные рейсы."
	}
}

const LEGACY_OBJECT_IDS_REPLACED_BY_STAGING := {
	"vorobyovy-gory": true,
	"nizhny-novgorod": true,
	"vladivostok-funicular": true
}

static func get_objects() -> Array[Dictionary]:
	var objects: Array[Dictionary] = [
		{
			"id": "vorobyovy-gory",
			"name": "Канатная дорога на Воробьевых горах",
			"kind": "городская канатная дорога",
			"region": "Москва",
			"coordinates": Vector2(37.5517, 55.7103),
			"description": "Городская канатная дорога через Москву-реку с видом на университет и стадион.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить расписание и семейный тариф перед поездкой.",
			"transport_type_id": "cable_urban",
			"country": "Россия",
			"city": "Москва",
			"latitude": 55.7103,
			"longitude": 37.5517,
			"opened_year": null,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "nizhny-novgorod",
			"name": "Нижегородская канатная дорога",
			"kind": "маятниковая канатная дорога",
			"region": "Нижний Новгород",
			"coordinates": Vector2(44.0186, 56.3299),
			"description": "Маршрут над Волгой между Нижним Новгородом и Бором.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хороший кандидат для первой большой карточки с фото и билетами.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Россия",
			"city": "Нижний Новгород",
			"latitude": 56.3299,
			"longitude": 44.0186,
			"opened_year": null,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "vladivostok-funicular",
			"name": "Владивостокский фуникулер",
			"kind": "классический фуникулер",
			"region": "Владивосток",
			"coordinates": Vector2(131.8939, 43.1187),
			"description": "Короткий городской фуникулер на сопке Орлиное Гнездо.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Добавить историю сооружения и видовые точки.",
			"transport_type_id": "funicular_classic",
			"country": "Россия",
			"city": "Владивосток",
			"latitude": 43.1187,
			"longitude": 131.8939,
			"opened_year": null,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "berlin-gaerten-der-welt",
			"name": "Канатная дорога в садах мира Берлина",
			"kind": "гондольная канатная дорога",
			"region": "Берлин",
			"coordinates": Vector2(13.5900, 52.5283),
			"description": "Гондольная канатная дорога над парком Gärten der Welt и Кинбергом, построенная к международной садовой выставке 2017 года.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить входной билет в парк и режим работы канатной дороги.",
			"transport_type_id": "cable_gondola",
			"country": "Германия",
			"city": "Берлин",
			"latitude": 52.5283,
			"longitude": 13.5900,
			"opened_year": 2017,
			"operator": "Leitner Seilbahn Berlin GmbH",
			"manufacturer": "Leitner",
			"stations": [
				{
					"id": "berlin-gaerten-der-welt-station-kienbergpark",
					"title": "Киенбергпарк",
					"latitude": 52.5281,
					"longitude": 13.5903,
					"sort_order": 10,
					"note": "Нижняя станция у U5; удобная начальная точка семейной поездки."
				},
				{
					"id": "berlin-gaerten-der-welt-station-wolkenhain",
					"title": "Волькенхайн",
					"latitude": 52.5268,
					"longitude": 13.5838,
					"sort_order": 20,
					"note": "Промежуточная станция на Кинберге рядом со смотровой площадкой."
				},
				{
					"id": "berlin-gaerten-der-welt-station-gaerten-der-welt",
					"title": "Сады мира",
					"latitude": 52.5254,
					"longitude": 13.5753,
					"sort_order": 30,
					"note": "Станция у входа в парк со стороны Блумбергер-Дамм."
				}
			],
			"route_directions": [
				{
					"id": "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten",
					"from_station_id": "berlin-gaerten-der-welt-station-kienbergpark",
					"to_station_id": "berlin-gaerten-der-welt-station-gaerten-der-welt",
					"title": "Киенбергпарк -> Сады мира",
					"direction_label": "от Киенбергпарка к Садам мира",
					"sort_order": 10,
					"note": "Направление через Волькенхайн от метро U5 к главному входу в парк."
				},
				{
					"id": "berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark",
					"from_station_id": "berlin-gaerten-der-welt-station-gaerten-der-welt",
					"to_station_id": "berlin-gaerten-der-welt-station-kienbergpark",
					"title": "Сады мира -> Киенбергпарк",
					"direction_label": "от Садов мира к Киенбергпарку",
					"sort_order": 20,
					"note": "Обратное направление к U5 с промежуточной остановкой на Кинберге."
				}
			],
			"route_segments_by_direction": {
				"berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten": [
					{
						"id": "berlin-gaerten-der-welt-segment-kienbergpark-wolkenhain",
						"from_station_id": "berlin-gaerten-der-welt-station-kienbergpark",
						"to_station_id": "berlin-gaerten-der-welt-station-wolkenhain",
						"segment_order": 10,
						"title": "Киенбергпарк -> Волькенхайн",
						"direction_label": "вверх к Волькенхайну",
						"note": "Первый подъем от U5 к Кинбергу."
					},
					{
						"id": "berlin-gaerten-der-welt-segment-wolkenhain-gaerten",
						"from_station_id": "berlin-gaerten-der-welt-station-wolkenhain",
						"to_station_id": "berlin-gaerten-der-welt-station-gaerten-der-welt",
						"segment_order": 20,
						"title": "Волькенхайн -> Сады мира",
						"direction_label": "вниз к Садам мира",
						"note": "Спуск к входу в парк."
					}
				],
				"berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark": [
					{
						"id": "berlin-gaerten-der-welt-segment-gaerten-wolkenhain",
						"from_station_id": "berlin-gaerten-der-welt-station-gaerten-der-welt",
						"to_station_id": "berlin-gaerten-der-welt-station-wolkenhain",
						"segment_order": 10,
						"title": "Сады мира -> Волькенхайн",
						"direction_label": "вверх к Волькенхайну",
						"note": "Обратный подъем от парка к Кинбергу."
					},
					{
						"id": "berlin-gaerten-der-welt-segment-wolkenhain-kienbergpark",
						"from_station_id": "berlin-gaerten-der-welt-station-wolkenhain",
						"to_station_id": "berlin-gaerten-der-welt-station-kienbergpark",
						"segment_order": 20,
						"title": "Волькенхайн -> Киенбергпарк",
						"direction_label": "вниз к Киенбергпарку",
						"note": "Спуск к U5."
					}
				]
			}
		},
		{
			"id": "thale-hexentanzplatz",
			"name": "Канатная дорога Тале на Хексентанцплац",
			"kind": "гондольная канатная дорога",
			"region": "Саксония-Анхальт",
			"coordinates": Vector2(11.0264, 51.7414),
			"description": "Кабинная дорога из долины Боде к скальному плато Хексентанцплац, одной из главных видовых точек Гарца.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Совместить с прогулкой по Бодеталю и соседним подъемником на Росстраппе.",
			"transport_type_id": "cable_gondola",
			"country": "Германия",
			"city": "Тале",
			"latitude": 51.7414,
			"longitude": 11.0264,
			"opened_year": 2012,
			"operator": "Seilbahnen Thale Erlebniswelt",
			"manufacturer": "Doppelmayr"
		},
		{
			"id": "thale-rosstrappe",
			"name": "Кресельная дорога Тале на Росстраппе",
			"kind": "туристическая канатная дорога",
			"region": "Саксония-Анхальт",
			"coordinates": Vector2(11.0259, 51.7427),
			"description": "Кресельный подъемник из Бодеталя к скалам Росстраппе с видами на ущелье и Хексентанцплац.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить сезонность и погоду: открытая кресельная дорога зависит от условий.",
			"transport_type_id": "cable_tourist",
			"country": "Германия",
			"city": "Тале",
			"latitude": 51.7427,
			"longitude": 11.0259,
			"opened_year": 2005,
			"operator": "Seilbahnen Thale Erlebniswelt",
			"manufacturer": "Leitner"
		},
		{
			"id": "stuttgart-standseilbahn",
			"name": "Штутгартский фуникулер",
			"kind": "классический фуникулер",
			"region": "Баден-Вюртемберг",
			"coordinates": Vector2(9.1556, 48.7609),
			"description": "Исторический фуникулер от Зюдхаймер-плац к лесному кладбищу, известный деревянными вагонами из тикового дерева.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Удобно совместить с маршрутом по южным районам Штутгарта.",
			"transport_type_id": "funicular_classic",
			"country": "Германия",
			"city": "Штутгарт",
			"latitude": 48.7609,
			"longitude": 9.1556,
			"opened_year": 1929,
			"operator": "Stuttgarter Straßenbahnen AG",
			"manufacturer": null
		},
		{
			"id": "stuttgart-zahnradbahn",
			"name": "Штутгартская зубчатая железная дорога",
			"kind": "зубчатая железная дорога",
			"region": "Баден-Вюртемберг",
			"coordinates": Vector2(9.1687, 48.7646),
			"description": "Городская зубчатая линия Zacke поднимается от Мариенплац к Дегерлоху и работает как часть общественного транспорта.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить возможность провоза велосипеда на специальной платформе.",
			"transport_type_id": "rail_cog",
			"country": "Германия",
			"city": "Штутгарт",
			"latitude": 48.7646,
			"longitude": 9.1687,
			"opened_year": 1884,
			"operator": "Stuttgarter Straßenbahnen AG",
			"manufacturer": null
		},
		{
			"id": "bayerische-zugspitzbahn",
			"name": "Баварская зубчатая дорога на Цугшпитце",
			"kind": "зубчатая железная дорога",
			"region": "Бавария",
			"coordinates": Vector2(11.0979, 47.4917),
			"description": "Зубчатая железная дорога от Гармиш-Партенкирхена и Грайнау к плато Цугшпитцплатт под высочайшей вершиной Германии.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Подходит для кругового маршрута с канатными дорогами Цугшпитце.",
			"transport_type_id": "rail_cog",
			"country": "Германия",
			"city": "Гармиш-Партенкирхен",
			"latitude": 47.4917,
			"longitude": 11.0979,
			"opened_year": 1930,
			"operator": "Bayerische Zugspitzbahn Bergbahn AG",
			"manufacturer": null
		},
		{
			"id": "seilbahn-zugspitze",
			"name": "Канатная дорога Цугшпитце",
			"kind": "маятниковая канатная дорога",
			"region": "Бавария",
			"coordinates": Vector2(10.9928, 47.4567),
			"description": "Маятниковая канатная дорога от Айбзее к вершине Цугшпитце с большим перепадом высот и панорамой Альп.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Лучше проверять погоду на вершине и бронирование билетов заранее.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Германия",
			"city": "Грайнау",
			"latitude": 47.4567,
			"longitude": 10.9928,
			"opened_year": 2017,
			"operator": "Bayerische Zugspitzbahn Bergbahn AG",
			"manufacturer": "Doppelmayr/Garaventa"
		},
		{
			"id": "zugspitze-gletscherbahn",
			"name": "Глетчербан на Цугшпитце",
			"kind": "маятниковая канатная дорога",
			"region": "Бавария",
			"coordinates": Vector2(10.9847, 47.4214),
			"description": "Короткая высокогорная канатная дорога между плато Цугшпитцплатт и вершиной Цугшпитце.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Полезна как связка между зубчатой дорогой и вершиной.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Германия",
			"city": "Гармиш-Партенкирхен",
			"latitude": 47.4214,
			"longitude": 10.9847,
			"opened_year": 1992,
			"operator": "Bayerische Zugspitzbahn Bergbahn AG",
			"manufacturer": null
		},
		{
			"id": "wuppertaler-schwebebahn",
			"name": "Вуппертальская подвесная железная дорога",
			"kind": "подвесная железная дорога",
			"region": "Северный Рейн-Вестфалия",
			"coordinates": Vector2(7.1984, 51.2692),
			"description": "Знаменитая подвесная городская железная дорога над рекой Вуппер, работающая как регулярный общественный транспорт с 1901 года.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проехать весь маршрут и выбрать станции с лучшими видами на реку.",
			"transport_type_id": "rail_suspended",
			"country": "Германия",
			"city": "Вупперталь",
			"latitude": 51.2692,
			"longitude": 7.1984,
			"opened_year": 1901,
			"operator": "WSW mobil GmbH",
			"manufacturer": null
		},
		{
			"id": "dresden-schwebebahn",
			"name": "Дрезденская подвесная железная дорога",
			"kind": "подвесная железная дорога",
			"region": "Саксония",
			"coordinates": Vector2(13.8193, 51.0539),
			"description": "Канатно-тяговая подвесная дорога из Лошвица в Оберлошвиц с верхней обзорной площадкой над долиной Эльбы.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить работу смотровой площадки на верхней станции.",
			"transport_type_id": "rail_suspended",
			"country": "Германия",
			"city": "Дрезден",
			"latitude": 51.0539,
			"longitude": 13.8193,
			"opened_year": 1901,
			"operator": "Dresdner Verkehrsbetriebe AG",
			"manufacturer": null
		},
		{
			"id": "dresden-standseilbahn",
			"name": "Дрезденский фуникулер",
			"kind": "классический фуникулер",
			"region": "Саксония",
			"coordinates": Vector2(13.8141, 51.0530),
			"description": "Исторический фуникулер от Кёрнерплац к району Вайсер-Хирш, одна из двух дрезденских горных дорог.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Можно сравнить в один день с Дрезденской подвесной дорогой.",
			"transport_type_id": "funicular_classic",
			"country": "Германия",
			"city": "Дрезден",
			"latitude": 51.0530,
			"longitude": 13.8141,
			"opened_year": 1895,
			"operator": "Dresdner Verkehrsbetriebe AG",
			"manufacturer": null
		},
		{
			"id": "nerobergbahn",
			"name": "Неробергбан в Висбадене",
			"kind": "водяной фуникулер",
			"region": "Гессен",
			"coordinates": Vector2(8.2326, 50.0935),
			"description": "Водобалластный фуникулер на Нероберг, сохранивший редкую историческую систему движения с водой.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить сезон работы: линия обычно не круглогодичная.",
			"transport_type_id": "funicular_water",
			"country": "Германия",
			"city": "Висбаден",
			"latitude": 50.0935,
			"longitude": 8.2326,
			"opened_year": 1888,
			"operator": "ESWE Verkehrsgesellschaft mbH",
			"manufacturer": null
		},
		{
			"id": "bad-schandau-lift",
			"name": "Исторический лифт Бад-Шандау",
			"kind": "вертикальный лифт",
			"region": "Саксония",
			"coordinates": Vector2(14.1508, 50.9196),
			"description": "Свободно стоящий исторический пассажирский лифт из долины Эльбы к району Острау и смотровой площадке.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хороший короткий объект для маршрута по Саксонской Швейцарии.",
			"transport_type_id": "elevator_vertical",
			"country": "Германия",
			"city": "Бад-Шандау",
			"latitude": 50.9196,
			"longitude": 14.1508,
			"opened_year": 1904,
			"operator": null,
			"manufacturer": null
		},
		{
			"id": "heidelberg-bergbahn",
			"name": "Гейдельбергская горная железная дорога",
			"kind": "классический фуникулер",
			"region": "Баден-Вюртемберг",
			"coordinates": Vector2(8.7155, 49.4105),
			"description": "Две связанные фуникулерные линии от старого города к замку, Молькенкуру и вершине Кёнигштуль.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Для семьи удобно начать у старого города и выйти у замка.",
			"transport_type_id": "funicular_classic",
			"country": "Германия",
			"city": "Гейдельберг",
			"latitude": 49.4105,
			"longitude": 8.7155,
			"opened_year": 1890,
			"operator": "Heidelberger Straßen- und Bergbahn GmbH",
			"manufacturer": null
		},
		{
			"id": "bad-harzburg-burgbergseilbahn",
			"name": "Бургбергская канатная дорога в Бад-Харцбурге",
			"kind": "маятниковая канатная дорога",
			"region": "Нижняя Саксония",
			"coordinates": Vector2(10.5606, 51.8710),
			"description": "Историческая маятниковая канатная дорога на Большой Бургберг с видом на город и предгорья Гарца.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Подходит как начало прогулки по плато и маршрутов в национальный парк Гарца.",
			"transport_type_id": "cable_aerial_tram",
			"country": "Германия",
			"city": "Бад-Харцбург",
			"latitude": 51.8710,
			"longitude": 10.5606,
			"opened_year": 1929,
			"operator": "Stadt Bad Harzburg",
			"manufacturer": "Adolf Bleichert & Co."
		},
		{
			"id": "wurmbergseilbahn",
			"name": "Вурмбергская канатная дорога",
			"kind": "гондольная канатная дорога",
			"region": "Нижняя Саксония",
			"coordinates": Vector2(10.6129, 51.7319),
			"description": "Гондольная дорога из Браунлаге на Вурмберг, один из главных подъемов Гарца для прогулок, лыж и велосипедов.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить работу средней станции и правила перевозки велосипедов.",
			"transport_type_id": "cable_gondola",
			"country": "Германия",
			"city": "Браунлаге",
			"latitude": 51.7319,
			"longitude": 10.6129,
			"opened_year": 1963,
			"operator": "Wurmbergseilbahn GmbH & Co. KG",
			"manufacturer": "Doppelmayr"
		},
		{
			"id": "dortmund-h-bahn",
			"name": "Дортмундская H-Bahn",
			"kind": "подвесной поезд",
			"region": "Северный Рейн-Вестфалия",
			"coordinates": Vector2(7.4147, 51.4924),
			"description": "Автоматическая подвесная система H-Bahn соединяет кампусы Технического университета Дортмунда и соседние станции.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Интересный пример действующего автоматического подвесного шаттла в университетской среде.",
			"transport_type_id": "suspended_train",
			"country": "Германия",
			"city": "Дортмунд",
			"latitude": 51.4924,
			"longitude": 7.4147,
			"opened_year": 1984,
			"operator": "DSW21",
			"manufacturer": "Siemens"
		},
		{
			"id": "duesseldorf-skytrain",
			"name": "SkyTrain аэропорта Дюссельдорфа",
			"kind": "подвесной поезд",
			"region": "Северный Рейн-Вестфалия",
			"coordinates": Vector2(6.7653, 51.2805),
			"description": "Автоматический подвесной поезд связывает терминалы аэропорта Дюссельдорфа, парковки и железнодорожную станцию Flughafen.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Проверить доступ по авиационному или городскому билету перед поездкой.",
			"transport_type_id": "suspended_train",
			"country": "Германия",
			"city": "Дюссельдорф",
			"latitude": 51.2805,
			"longitude": 6.7653,
			"opened_year": 2002,
			"operator": "Flughafen Düsseldorf GmbH",
			"manufacturer": "Siemens",
			"stations": [
				{
					"id": "duesseldorf-skytrain-station-terminal",
					"title": "Терминал",
					"latitude": 51.2893,
					"longitude": 6.7652,
					"sort_order": 10,
					"note": "Станция у терминала аэропорта Дюссельдорфа."
				},
				{
					"id": "duesseldorf-skytrain-station-bahnhof",
					"title": "Аэропорт-вокзал",
					"latitude": 51.2810,
					"longitude": 6.7460,
					"sort_order": 20,
					"note": "Станция у дальнего железнодорожного вокзала Flughafen."
				}
			],
			"route_directions": [
				{
					"id": "duesseldorf-skytrain-direction-terminal-to-bahnhof",
					"from_station_id": "duesseldorf-skytrain-station-terminal",
					"to_station_id": "duesseldorf-skytrain-station-bahnhof",
					"title": "Терминал -> Аэропорт-вокзал",
					"direction_label": "в сторону вокзала",
					"sort_order": 10,
					"note": "Направление от терминала аэропорта к железнодорожному вокзалу Flughafen."
				}
			],
			"route_segments_by_direction": {
				"duesseldorf-skytrain-direction-terminal-to-bahnhof": [
					{
						"id": "duesseldorf-skytrain-segment-terminal-bahnhof",
						"from_station_id": "duesseldorf-skytrain-station-terminal",
						"to_station_id": "duesseldorf-skytrain-station-bahnhof",
						"segment_order": 10,
						"title": "Терминал -> Аэропорт-вокзал",
						"direction_label": "вниз к вокзалу",
						"note": "Прямой участок от терминала к железнодорожному вокзалу."
					}
				]
			}
		},
		{
			"id": "baden-baden-merkurbergbahn",
			"name": "Меркурбергбан в Баден-Бадене",
			"kind": "классический фуникулер",
			"region": "Баден-Вюртемберг",
			"coordinates": Vector2(8.2647, 48.7630),
			"description": "Классический фуникулер на гору Меркур, один из самых длинных и крутых фуникулеров Германии.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Подходит для короткой поездки к смотровой башне и маршрутам по северному Шварцвальду.",
			"transport_type_id": "funicular_classic",
			"country": "Германия",
			"city": "Баден-Баден",
			"latitude": 48.7630,
			"longitude": 8.2647,
			"opened_year": 1913,
			"operator": "Stadtwerke Baden-Baden",
			"manufacturer": null
		},
		{
			"id": "koblenz-seilbahn",
			"name": "Канатная дорога Кобленца",
			"kind": "городская канатная дорога",
			"region": "Рейнланд-Пфальц",
			"coordinates": Vector2(7.6052, 50.3617),
			"description": "Городская 3S-канатная дорога через Рейн между районом Немецкого угла и крепостью Эренбрайтштайн.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Хорошо совмещается с прогулкой по старому городу, набережной Рейна и крепостью.",
			"transport_type_id": "cable_urban",
			"country": "Германия",
			"city": "Кобленц",
			"latitude": 50.3617,
			"longitude": 7.6052,
			"opened_year": 2010,
			"operator": "Skyglide Event Deutschland GmbH",
			"manufacturer": "Doppelmayr"
		},
		{
			"id": "koeln-seilbahn",
			"name": "Кёльнская канатная дорога",
			"kind": "туристическая канатная дорога",
			"region": "Северный Рейн-Вестфалия",
			"coordinates": Vector2(6.9770, 50.9536),
			"description": "Рейнская канатная дорога между Кёльнским зоопарком и Рейнпарком, открытая к федеральной садовой выставке 1957 года.",
			"visited": false,
			"visit_status_id": "not_visited",
			"notes": "Удобно объединить с зоопарком, Флорой и прогулкой по Рейнпарку.",
			"transport_type_id": "cable_tourist",
			"country": "Германия",
			"city": "Кёльн",
			"latitude": 50.9536,
			"longitude": 6.9770,
			"opened_year": 1957,
			"operator": "Kölner Seilbahn-Gesellschaft mbH",
			"manufacturer": "Julius Pohlig"
		}
	]

	objects = _without_replaced_legacy_objects(objects)
	_append_seed_objects(objects, DemoCatalogEuropeScript.get_objects())
	_append_seed_objects(objects, DemoCatalogRussiaScript.get_objects())
	_apply_operational_status(objects)
	return objects


static func _without_replaced_legacy_objects(source_objects: Array[Dictionary]) -> Array[Dictionary]:
	var filtered_objects: Array[Dictionary] = []
	for object_data in source_objects:
		var object_id := str(object_data.get("id", ""))
		if LEGACY_OBJECT_IDS_REPLACED_BY_STAGING.has(object_id):
			continue
		filtered_objects.append(object_data)
	return filtered_objects


static func _append_seed_objects(target_objects: Array[Dictionary], seed_objects: Array[Dictionary]) -> void:
	var known_ids := {}
	for object_data in target_objects:
		known_ids[str(object_data.get("id", ""))] = true

	for object_data in seed_objects:
		var object_id := str(object_data.get("id", ""))
		if object_id.is_empty() or known_ids.has(object_id):
			continue
		target_objects.append(object_data)
		known_ids[object_id] = true


static func _apply_operational_status(objects: Array[Dictionary]) -> void:
	var status_by_id := _combined_operational_status_by_id()
	for object_data in objects:
		var object_id := str(object_data.get("id", ""))
		var metadata: Dictionary = DEFAULT_OPERATIONAL_STATUS
		if status_by_id.has(object_id):
			metadata = status_by_id[object_id]
		for key in metadata.keys():
			object_data[key] = metadata[key]


static func _combined_operational_status_by_id() -> Dictionary:
	var status_by_id := OPERATIONAL_STATUS_BY_ID.duplicate(true)
	for object_id in DemoCatalogEuropeScript.get_operational_status_by_id().keys():
		status_by_id[object_id] = DemoCatalogEuropeScript.get_operational_status_by_id()[object_id]
	for object_id in DemoCatalogRussiaScript.get_operational_status_by_id().keys():
		status_by_id[object_id] = DemoCatalogRussiaScript.get_operational_status_by_id()[object_id]
	return status_by_id
