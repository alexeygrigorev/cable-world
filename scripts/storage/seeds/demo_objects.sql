INSERT INTO transport_objects (
    id,
    title,
    transport_type_id,
    visit_status_id,
    country,
    region,
    city,
    latitude,
    longitude,
    description,
    notes,
    opened_year,
    operator,
    manufacturer,
    created_at,
    updated_at
) VALUES
(
    'vorobyovy-gory',
    'Канатная дорога на Воробьевых горах',
    'cable_urban',
    'not_visited',
    'Россия',
    'Москва',
    'Москва',
    55.7103,
    37.5517,
    'Городская канатная дорога через Москву-реку с видом на университет и стадион.',
    'Проверить расписание и семейный тариф перед поездкой.',
    NULL,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'nizhny-novgorod',
    'Нижегородская канатная дорога',
    'cable_aerial_tram',
    'not_visited',
    'Россия',
    'Нижний Новгород',
    'Нижний Новгород',
    56.3299,
    44.0186,
    'Маршрут над Волгой между Нижним Новгородом и Бором.',
    'Хороший кандидат для первой большой карточки с фото и билетами.',
    NULL,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'vladivostok-funicular',
    'Владивостокский фуникулер',
    'funicular_classic',
    'not_visited',
    'Россия',
    'Владивосток',
    'Владивосток',
    43.1187,
    131.8939,
    'Короткий городской фуникулер на сопке Орлиное Гнездо.',
    'Добавить историю сооружения и видовые точки.',
    NULL,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'berlin-gaerten-der-welt',
    'Канатная дорога в садах мира Берлина',
    'cable_gondola',
    'not_visited',
    'Германия',
    'Берлин',
    'Берлин',
    52.5283,
    13.5900,
    'Гондольная канатная дорога над парком Gärten der Welt и Кинбергом, построенная к международной садовой выставке 2017 года.',
    'Проверить входной билет в парк и режим работы канатной дороги.',
    2017,
    'Leitner Seilbahn Berlin GmbH',
    'Leitner',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'thale-hexentanzplatz',
    'Канатная дорога Тале на Хексентанцплац',
    'cable_gondola',
    'not_visited',
    'Германия',
    'Саксония-Анхальт',
    'Тале',
    51.7414,
    11.0264,
    'Кабинная дорога из долины Боде к скальному плато Хексентанцплац, одной из главных видовых точек Гарца.',
    'Совместить с прогулкой по Бодеталю и соседним подъемником на Росстраппе.',
    2012,
    'Seilbahnen Thale Erlebniswelt',
    'Doppelmayr',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'thale-rosstrappe',
    'Кресельная дорога Тале на Росстраппе',
    'cable_tourist',
    'not_visited',
    'Германия',
    'Саксония-Анхальт',
    'Тале',
    51.7427,
    11.0259,
    'Кресельный подъемник из Бодеталя к скалам Росстраппе с видами на ущелье и Хексентанцплац.',
    'Проверить сезонность и погоду: открытая кресельная дорога зависит от условий.',
    2005,
    'Seilbahnen Thale Erlebniswelt',
    'Leitner',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'stuttgart-standseilbahn',
    'Штутгартский фуникулер',
    'funicular_classic',
    'not_visited',
    'Германия',
    'Баден-Вюртемберг',
    'Штутгарт',
    48.7609,
    9.1556,
    'Исторический фуникулер от Зюдхаймер-плац к лесному кладбищу, известный деревянными вагонами из тикового дерева.',
    'Удобно совместить с маршрутом по южным районам Штутгарта.',
    1929,
    'Stuttgarter Straßenbahnen AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'stuttgart-zahnradbahn',
    'Штутгартская зубчатая железная дорога',
    'rail_cog',
    'not_visited',
    'Германия',
    'Баден-Вюртемберг',
    'Штутгарт',
    48.7646,
    9.1687,
    'Городская зубчатая линия Zacke поднимается от Мариенплац к Дегерлоху и работает как часть общественного транспорта.',
    'Проверить возможность провоза велосипеда на специальной платформе.',
    1884,
    'Stuttgarter Straßenbahnen AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'bayerische-zugspitzbahn',
    'Баварская зубчатая дорога на Цугшпитце',
    'rail_cog',
    'not_visited',
    'Германия',
    'Бавария',
    'Гармиш-Партенкирхен',
    47.4917,
    11.0979,
    'Зубчатая железная дорога от Гармиш-Партенкирхена и Грайнау к плато Цугшпитцплатт под высочайшей вершиной Германии.',
    'Подходит для кругового маршрута с канатными дорогами Цугшпитце.',
    1930,
    'Bayerische Zugspitzbahn Bergbahn AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'seilbahn-zugspitze',
    'Канатная дорога Цугшпитце',
    'cable_aerial_tram',
    'not_visited',
    'Германия',
    'Бавария',
    'Грайнау',
    47.4567,
    10.9928,
    'Маятниковая канатная дорога от Айбзее к вершине Цугшпитце с большим перепадом высот и панорамой Альп.',
    'Лучше проверять погоду на вершине и бронирование билетов заранее.',
    2017,
    'Bayerische Zugspitzbahn Bergbahn AG',
    'Doppelmayr/Garaventa',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'zugspitze-gletscherbahn',
    'Глетчербан на Цугшпитце',
    'cable_aerial_tram',
    'not_visited',
    'Германия',
    'Бавария',
    'Гармиш-Партенкирхен',
    47.4214,
    10.9847,
    'Короткая высокогорная канатная дорога между плато Цугшпитцплатт и вершиной Цугшпитце.',
    'Полезна как связка между зубчатой дорогой и вершиной.',
    1992,
    'Bayerische Zugspitzbahn Bergbahn AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'wuppertaler-schwebebahn',
    'Вуппертальская подвесная железная дорога',
    'rail_suspended',
    'not_visited',
    'Германия',
    'Северный Рейн-Вестфалия',
    'Вупперталь',
    51.2692,
    7.1984,
    'Знаменитая подвесная городская железная дорога над рекой Вуппер, работающая как регулярный общественный транспорт с 1901 года.',
    'Проехать весь маршрут и выбрать станции с лучшими видами на реку.',
    1901,
    'WSW mobil GmbH',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'dresden-schwebebahn',
    'Дрезденская подвесная железная дорога',
    'rail_suspended',
    'not_visited',
    'Германия',
    'Саксония',
    'Дрезден',
    51.0539,
    13.8193,
    'Канатно-тяговая подвесная дорога из Лошвица в Оберлошвиц с верхней обзорной площадкой над долиной Эльбы.',
    'Проверить работу смотровой площадки на верхней станции.',
    1901,
    'Dresdner Verkehrsbetriebe AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'dresden-standseilbahn',
    'Дрезденский фуникулер',
    'funicular_classic',
    'not_visited',
    'Германия',
    'Саксония',
    'Дрезден',
    51.0530,
    13.8141,
    'Исторический фуникулер от Кёрнерплац к району Вайсер-Хирш, одна из двух дрезденских горных дорог.',
    'Можно сравнить в один день с Дрезденской подвесной дорогой.',
    1895,
    'Dresdner Verkehrsbetriebe AG',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'nerobergbahn',
    'Неробергбан в Висбадене',
    'funicular_water',
    'not_visited',
    'Германия',
    'Гессен',
    'Висбаден',
    50.0935,
    8.2326,
    'Водобалластный фуникулер на Нероберг, сохранивший редкую историческую систему движения с водой.',
    'Проверить сезон работы: линия обычно не круглогодичная.',
    1888,
    'ESWE Verkehrsgesellschaft mbH',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'bad-schandau-lift',
    'Исторический лифт Бад-Шандау',
    'elevator_vertical',
    'not_visited',
    'Германия',
    'Саксония',
    'Бад-Шандау',
    50.9196,
    14.1508,
    'Свободно стоящий исторический пассажирский лифт из долины Эльбы к району Острау и смотровой площадке.',
    'Хороший короткий объект для маршрута по Саксонской Швейцарии.',
    1904,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'heidelberg-bergbahn',
    'Гейдельбергская горная железная дорога',
    'funicular_classic',
    'not_visited',
    'Германия',
    'Баден-Вюртемберг',
    'Гейдельберг',
    49.4105,
    8.7155,
    'Две связанные фуникулерные линии от старого города к замку, Молькенкуру и вершине Кёнигштуль.',
    'Для семьи удобно начать у старого города и выйти у замка.',
    1890,
    'Heidelberger Straßen- und Bergbahn GmbH',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'bad-harzburg-burgbergseilbahn',
    'Бургбергская канатная дорога в Бад-Харцбурге',
    'cable_aerial_tram',
    'not_visited',
    'Германия',
    'Нижняя Саксония',
    'Бад-Харцбург',
    51.8710,
    10.5606,
    'Историческая маятниковая канатная дорога на Большой Бургберг с видом на город и предгорья Гарца.',
    'Подходит как начало прогулки по плато и маршрутов в национальный парк Гарца.',
    1929,
    'Stadt Bad Harzburg',
    'Adolf Bleichert & Co.',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'wurmbergseilbahn',
    'Вурмбергская канатная дорога',
    'cable_gondola',
    'not_visited',
    'Германия',
    'Нижняя Саксония',
    'Браунлаге',
    51.7319,
    10.6129,
    'Гондольная дорога из Браунлаге на Вурмберг, один из главных подъемов Гарца для прогулок, лыж и велосипедов.',
    'Проверить работу средней станции и правила перевозки велосипедов.',
    1963,
    'Wurmbergseilbahn GmbH & Co. KG',
    'Doppelmayr',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'dortmund-h-bahn',
    'Дортмундская H-Bahn',
    'suspended_train',
    'not_visited',
    'Германия',
    'Северный Рейн-Вестфалия',
    'Дортмунд',
    51.4924,
    7.4147,
    'Автоматическая подвесная система H-Bahn соединяет кампусы Технического университета Дортмунда и соседние станции.',
    'Интересный пример действующего автоматического подвесного шаттла в университетской среде.',
    1984,
    'DSW21',
    'Siemens',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'duesseldorf-skytrain',
    'SkyTrain аэропорта Дюссельдорфа',
    'suspended_train',
    'not_visited',
    'Германия',
    'Северный Рейн-Вестфалия',
    'Дюссельдорф',
    51.2805,
    6.7653,
    'Автоматический подвесной поезд связывает терминалы аэропорта Дюссельдорфа, парковки и железнодорожную станцию Flughafen.',
    'Проверить доступ по авиационному или городскому билету перед поездкой.',
    2002,
    'Flughafen Düsseldorf GmbH',
    'Siemens',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'baden-baden-merkurbergbahn',
    'Меркурбергбан в Баден-Бадене',
    'funicular_classic',
    'not_visited',
    'Германия',
    'Баден-Вюртемберг',
    'Баден-Баден',
    48.7630,
    8.2647,
    'Классический фуникулер на гору Меркур, один из самых длинных и крутых фуникулеров Германии.',
    'Подходит для короткой поездки к смотровой башне и маршрутам по северному Шварцвальду.',
    1913,
    'Stadtwerke Baden-Baden',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'koblenz-seilbahn',
    'Канатная дорога Кобленца',
    'cable_urban',
    'not_visited',
    'Германия',
    'Рейнланд-Пфальц',
    'Кобленц',
    50.3617,
    7.6052,
    'Городская 3S-канатная дорога через Рейн между районом Немецкого угла и крепостью Эренбрайтштайн.',
    'Хорошо совмещается с прогулкой по старому городу, набережной Рейна и крепостью.',
    2010,
    'Skyglide Event Deutschland GmbH',
    'Doppelmayr',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'koeln-seilbahn',
    'Кёльнская канатная дорога',
    'cable_tourist',
    'not_visited',
    'Германия',
    'Северный Рейн-Вестфалия',
    'Кёльн',
    50.9536,
    6.9770,
    'Рейнская канатная дорога между Кёльнским зоопарком и Рейнпарком, открытая к федеральной садовой выставке 1957 года.',
    'Удобно объединить с зоопарком, Флорой и прогулкой по Рейнпарку.',
    1957,
    'Kölner Seilbahn-Gesellschaft mbH',
    'Julius Pohlig',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
)
ON CONFLICT(id) DO NOTHING;

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.gaertenderwelt.de/erlebnisse/seilbahn/',
    status_note = 'Сезонный график на 2026 год: апрель-сентябрь ежедневно 10:00-19:00; при сильном ветре или грозе возможна остановка.'
WHERE id = 'berlin-gaerten-der-welt';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.seilbahnen-thale.de/en/rosstrappe',
    status_note = 'Оператор показывает дневную доступность аттракционов; перед поездкой нужно проверить часы и погоду.'
WHERE id IN ('thale-hexentanzplatz', 'thale-rosstrappe');

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://embedded.ssb-ag.de/unternehmen/informationen-fakten/fahrzeuge/seilbahn/',
    status_note = 'Городская линия 20 SSB, действующий маршрут общественного транспорта.'
WHERE id = 'stuttgart-standseilbahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.ssb-ag.de/unternehmen/informationen-fakten/fahrzeuge/zahnradbahn/',
    status_note = 'Городская линия 10 SSB; действующая зубчатая дорога с регулярным расписанием.'
WHERE id = 'stuttgart-zahnradbahn';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://zugspitze.de/de/Service-Informationen/Betriebszeiten-Fahrplaene',
    status_note = 'Опубликованы рабочие часы и плановые ревизии на 2026 год; перед поездкой проверить погоду и текущий статус.'
WHERE id IN ('bayerische-zugspitzbahn', 'seilbahn-zugspitze', 'zugspitze-gletscherbahn');

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://schwebebahn.de/',
    status_note = 'Регулярный городской транспорт; перед поездкой проверить текущие Verkehrsinformationen.'
WHERE id = 'wuppertaler-schwebebahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.dvb.de/de-de/entdecken/bergbahnen/',
    status_note = 'DVB публикует рабочие графики и периоды ревизии для дрезденских горных дорог.'
WHERE id IN ('dresden-schwebebahn', 'dresden-standseilbahn');

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.wiesbaden.de/fr/leben-in-wiesbaden/freizeit/ausfluege/nerobergbahn-neroberg',
    status_note = 'Сезон 2026 начался 3 апреля; линия работает ежедневно до конца осени.'
WHERE id = 'nerobergbahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.saechsische-schweiz.de/ausflugsziele/historischer-personenaufzug-badschandau',
    status_note = 'Опубликованы круглогодичные часы работы с разным временем по месяцам.'
WHERE id = 'bad-schandau-lift';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.bergbahn-heidelberg.de/',
    status_note = 'Горная железная дорога работает по сезонным графикам; перед поездкой проверить текущий летний или зимний Fahrplan.'
WHERE id = 'heidelberg-bergbahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.bad-harzburg.de/wanderland/burgberg-seilbahn/',
    status_note = 'Опубликованы летние и зимние Fahrzeiten; плановая ревизия указана на ноябрь 2026 года.'
WHERE id = 'bad-harzburg-burgbergseilbahn';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://wurmberg-seilbahn.de/sommer.html',
    status_note = 'Оператор показывает текущий статус как открыто и публикует дневные часы работы.'
WHERE id = 'wurmbergseilbahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.bus-und-bahn.de/h-bahn',
    status_note = 'Действующий автоматический транспорт TU Dortmund; оператор публикует Fahrplan и Verkehrsmeldungen.'
WHERE id = 'dortmund-h-bahn';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.dus.com/en/to-and-from/bus-and-train',
    status_note = 'SkyTrain аэропорта работает ежедневно 03:45-00:45; ночью есть автобусная подмена.'
WHERE id = 'duesseldorf-skytrain';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.stadtwerke-baden-baden.de/de/mobilitaet-freizeit/merkurbahn/',
    status_note = 'Оператор публикует часы MerkurBergbahn; после ревизии 2026 объект готов к регулярной работе.'
WHERE id = 'baden-baden-merkurbergbahn';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.seilbahn-koblenz.de/',
    status_note = 'Туристическая канатная дорога через Рейн; перед поездкой проверить сезонный календарь и спецсобытия.'
WHERE id = 'koblenz-seilbahn';

UPDATE transport_objects
SET operational_status = 'active_seasonal',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.stadtwerkekoeln.de/pressemitteilungen/saisonstart-kolner-seilbahn-ab-dem-12-marz-heben-die-gondeln-wieder-ab',
    status_note = 'Сезон 2026 стартовал 12 марта; регулярный сезон идет до начала ноября, далее запланированы адвентные рейсы.'
WHERE id = 'koeln-seilbahn';
