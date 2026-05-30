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
    'nizhny-novgorod-bor-cable-car',
    'Нижегородская канатная дорога',
    'cable_urban',
    'not_visited',
    'Россия',
    'Нижегородская область',
    'Нижний Новгород / Бор',
    56.3309,
    44.0168,
    'Городская канатная дорога через Волгу между Нижним Новгородом и Бором.',
    'Высокий приоритет для российского каталога; перед основным seed сверить станции и источники.',
    2012,
    'АО "Нижегородские канатные дороги"',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'moscow-vorobyovy-gory-cable-car',
    'Московская канатная дорога',
    'cable_urban',
    'not_visited',
    'Россия',
    'Москва',
    'Москва',
    55.7106,
    37.5429,
    'Канатная дорога между Воробьевыми горами, Новой Лигой и Лужниками.',
    'Используется staging id; legacy-id Воробьевых гор не добавляется, чтобы не было дублей.',
    2018,
    'ООО "Московские канатные дороги"',
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
    'Приморский край',
    'Владивосток',
    43.1168,
    131.8998,
    'Классический городской фуникулер на склоне сопки Орлиной между улицами Пушкинской и Суханова.',
    'Один из самых важных российских фуникулеров для начальной подборки.',
    1962,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'nizhny-novgorod-kremlin-funicular',
    'Кремлевский фуникулер в Нижнем Новгороде',
    'funicular_modern',
    'not_visited',
    'Россия',
    'Нижегородская область',
    'Нижний Новгород',
    56.3282,
    44.0057,
    'Восстановленный фуникулер у Нижегородского кремля, открытый заново в 2024 году.',
    'Новый российский фуникулер с сильной исторической ценностью.',
    2024,
    'ГБУК НО "Нижегородский государственный историко-архитектурный музей-заповедник"',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'pyatigorsk-mashuk-cable-car',
    'Пятигорская канатная дорога на Машук',
    'cable_aerial_tram',
    'not_visited',
    'Россия',
    'Ставропольский край',
    'Пятигорск',
    44.0479,
    43.0838,
    'Маятниковая канатная дорога от бульвара Гагарина к вершине горы Машук.',
    'Высокий приоритет для Кавказских Минеральных Вод.',
    1971,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'svetlogorsk-panorama-elevator',
    'Панорамный лифт "Панорама" в Светлогорске',
    'elevator_panoramic',
    'not_visited',
    'Россия',
    'Калининградская область',
    'Светлогорск',
    54.9447,
    20.1538,
    'Панорамный лифт у морского побережья Светлогорска, работающий как видовой инженерный объект и вертикальная связь.',
    'Хороший российский пример для типа elevator_panoramic.',
    NULL,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'moscow-monorail',
    'Московский монорельс',
    'monorail',
    'not_visited',
    'Россия',
    'Москва',
    'Москва',
    55.8214,
    37.6404,
    'Историческая городская монорельсовая линия на северо-востоке Москвы, закрытая для пассажирской работы в 2025 году.',
    'Исторический объект: показываем закрытые системы отдельно от действующих.',
    2004,
    'Московский транспорт',
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
),
(
    'braga-bom-jesus-funicular',
    'Фуникулер Bom Jesus do Monte',
    'funicular_water',
    'not_visited',
    'Португалия',
    'Брага',
    'Брага',
    41.5547,
    -8.3778,
    'Водобалластный фуникулер у святилища Bom Jesus do Monte в Браге; редкая технология для семейного исследования.',
    'Проверить координату нижней станции и текущий график работы перед поездкой.',
    1882,
    'Irmandade do Bom Jesus do Monte',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'grenoble-bastille-cable-car',
    'Канатная дорога Grenoble-Bastille',
    'cable_tourist',
    'not_visited',
    'Франция',
    'Овернь — Рона — Альпы',
    'Гренобль',
    45.1939,
    5.7265,
    'Городская туристическая канатная дорога из центра Гренобля к крепости Бастилия.',
    'Хороший объект для карточки с видом на город и сравнением старых и современных кабинок.',
    1934,
    'Régie du Téléphérique Grenoble Bastille',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'como-brunate-funicular',
    'Фуникулер Комо — Брунате',
    'funicular_classic',
    'not_visited',
    'Италия',
    'Ломбардия',
    'Комо',
    45.8148,
    9.0835,
    'Классический фуникулер, соединяющий Комо с Брунате над озером Комо.',
    'Уточнить оператора и расписание; объект подходит для маршрута от озера к смотровой точке.',
    1894,
    NULL,
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'prague-petrin-funicular',
    'Пражский фуникулер на Петршин',
    'funicular_classic',
    'not_visited',
    'Чехия',
    'Прага',
    'Прага',
    50.0838,
    14.4039,
    'Фуникулер Уезд — Петршин в Праге; на дату среза находится в плановой реконструкции.',
    'Не показывать как работающий объект, пока реконструкция не завершена и статус не обновлен.',
    1891,
    'Dopravní podnik hl. m. Prahy',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'stary-smokovec-hrebienok-funicular',
    'Фуникулер Старый Смоковец — Гребиенок',
    'funicular_classic',
    'not_visited',
    'Словакия',
    'Прешовский край',
    'Высокие Татры',
    49.1419,
    20.2224,
    'Горный фуникулер в Высоких Татрах между Старым Смоковцем и туристическим узлом Гребиенок.',
    'Уточнить координату нижней станции и сезонный статус перед семейной поездкой.',
    1908,
    'Tatry mountain resorts',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
),
(
    'zakopane-kasprowy-wierch-cable-car',
    'Канатная дорога на Каспровы Верх',
    'cable_aerial_tram',
    'not_visited',
    'Польша',
    'Малопольское воеводство',
    'Закопане',
    49.2320,
    19.9810,
    'Высокогорная канатная дорога PKL из Кузнице на Каспровы Верх в Татрах.',
    'Проверить погоду, ограничения национального парка и фактическое расписание на день поездки.',
    1936,
    'Polskie Koleje Linowe',
    NULL,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
)
ON CONFLICT(id) DO NOTHING;

DROP TABLE IF EXISTS legacy_transport_object_id_merge;

CREATE TEMP TABLE legacy_transport_object_id_merge (
    source_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    source_visit_status_id TEXT NOT NULL
);

INSERT INTO legacy_transport_object_id_merge (
    source_id,
    target_id,
    source_visit_status_id
)
SELECT
    transport_objects.id,
    CASE transport_objects.id
        WHEN 'vorobyovy-gory' THEN 'moscow-vorobyovy-gory-cable-car'
        WHEN 'nizhny-novgorod' THEN 'nizhny-novgorod-bor-cable-car'
    END,
    transport_objects.visit_status_id
FROM transport_objects
WHERE transport_objects.id IN ('vorobyovy-gory', 'nizhny-novgorod');

UPDATE transport_objects
SET visit_status_id = (
        SELECT legacy_transport_object_id_merge.source_visit_status_id
        FROM legacy_transport_object_id_merge
        WHERE legacy_transport_object_id_merge.target_id = transport_objects.id
          AND legacy_transport_object_id_merge.source_visit_status_id != 'not_visited'
        LIMIT 1
    ),
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id IN (
    SELECT target_id
    FROM legacy_transport_object_id_merge
    WHERE source_visit_status_id != 'not_visited'
);

UPDATE visits
SET transport_object_id = (
    SELECT legacy_transport_object_id_merge.target_id
    FROM legacy_transport_object_id_merge
    WHERE legacy_transport_object_id_merge.source_id = visits.transport_object_id
)
WHERE transport_object_id IN (
    SELECT source_id
    FROM legacy_transport_object_id_merge
);

UPDATE media_assets
SET transport_object_id = (
    SELECT legacy_transport_object_id_merge.target_id
    FROM legacy_transport_object_id_merge
    WHERE legacy_transport_object_id_merge.source_id = media_assets.transport_object_id
)
WHERE transport_object_id IN (
    SELECT source_id
    FROM legacy_transport_object_id_merge
);

UPDATE tickets
SET transport_object_id = (
    SELECT legacy_transport_object_id_merge.target_id
    FROM legacy_transport_object_id_merge
    WHERE legacy_transport_object_id_merge.source_id = tickets.transport_object_id
)
WHERE transport_object_id IN (
    SELECT source_id
    FROM legacy_transport_object_id_merge
);

DELETE FROM transport_objects
WHERE id IN (
    SELECT source_id
    FROM legacy_transport_object_id_merge
);

DROP TABLE legacy_transport_object_id_merge;

UPDATE transport_objects
SET title = 'Владивостокский фуникулер',
    transport_type_id = 'funicular_classic',
    country = 'Россия',
    region = 'Приморский край',
    city = 'Владивосток',
    latitude = 43.1168,
    longitude = 131.8998,
    description = 'Классический городской фуникулер на склоне сопки Орлиной между улицами Пушкинской и Суханова.',
    notes = 'Один из самых важных российских фуникулеров для начальной подборки.',
    opened_year = 1962,
    operator = NULL,
    manufacturer = NULL,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = 'vladivostok-funicular';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.borcity.ru/activity/transport/kanatka.php?special_version=Y',
    status_note = 'Статус и координаты нужно сверить с оператором/OSM перед production seed.'
WHERE id = 'nizhny-novgorod-bor-cable-car';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://srkvg.ru/kanatnaya-doroga/',
    status_note = 'Официальный сайт описывает маршрут и функции дороги; перед seed уточнить координаты станций.'
WHERE id = 'moscow-vorobyovy-gory-cable-car';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.vladivostok.travel/todo/funicular/',
    status_note = 'Туристический портал и новости подтверждают действующую работу после ремонтов; требуется сверка расписания.'
WHERE id = 'vladivostok-funicular';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://kremlnn.ru/funicular',
    status_note = 'Официальный сайт указывает режим и зимние температурные ограничения; координаты ориентировочные.'
WHERE id = 'nizhny-novgorod-kremlin-funicular';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://kanatkakmw.ru/',
    status_note = 'Регламентные закрытия возможны; перед seed проверить текущий режим работы.'
WHERE id = 'pyatigorsk-mashuk-cable-car';

UPDATE transport_objects
SET operational_status = 'active',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://liftsvetlogorsk.ru/',
    status_note = 'Перед seed уточнить год открытия и точку привязки нижней/верхней станции.'
WHERE id = 'svetlogorsk-panorama-elevator';

UPDATE transport_objects
SET operational_status = 'historical',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://transport.mos.ru/mostrans/all_news/125075',
    status_note = 'Единый транспортный портал Москвы сообщил, что монорельс завершит работу 28 июня 2025 года.'
WHERE id = 'moscow-monorail';

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

UPDATE transport_objects
SET operational_status = 'unknown',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://bomjesus.pt/bom-jesus/elevator-or-funicular/',
    status_note = 'Нужно подтвердить актуальное расписание перед переносом в основной каталог.'
WHERE id = 'braga-bom-jesus-funicular';

UPDATE transport_objects
SET operational_status = 'unknown',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://bastille-grenoble.fr/en/',
    status_note = 'Официальный сайт есть; перед поездкой нужно проверить часы работы и плановое обслуживание.'
WHERE id = 'grenoble-bastille-cable-car';

UPDATE transport_objects
SET operational_status = 'unknown',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.funicolarecomo.it/',
    status_note = 'Перед переносом в основной каталог нужно проверить оператора и актуальное расписание.'
WHERE id = 'como-brunate-funicular';

UPDATE transport_objects
SET operational_status = 'temporarily_closed_planned',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.dpp.cz/en/entertainment-and-experience/funicular-to-petrin',
    status_note = 'DPP сообщает о приостановке работы из-за полной реконструкции; пассажирские тесты ожидаются на рубеже лета и осени 2026.'
WHERE id = 'prague-petrin-funicular';

UPDATE transport_objects
SET operational_status = 'unknown',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://visittatry.sk/en/post/cable-cars',
    status_note = 'Перед переносом в основной каталог нужно проверить сезонное расписание и официальный статус у оператора.'
WHERE id = 'stary-smokovec-hrebienok-funicular';

UPDATE transport_objects
SET operational_status = 'unknown',
    status_checked_at = '2026-05-30',
    status_source_url = 'https://www.pkl.pl/kasprowy-wierch/kolej-linowa-kasprowy-wierch.html?setlang=1',
    status_note = 'Перед поездкой нужно проверить погодные ограничения, лимиты парка и фактическое расписание.'
WHERE id = 'zakopane-kasprowy-wierch-cable-car';

INSERT INTO object_stations (
    id,
    transport_object_id,
    title,
    station_role,
    latitude,
    longitude,
    sort_order,
    note
) VALUES
(
    'berlin-gaerten-der-welt-station-kienbergpark',
    'berlin-gaerten-der-welt',
    'Киенбергпарк',
    'lower',
    52.5281,
    13.5903,
    10,
    'Нижняя станция у U5; удобная начальная точка семейной поездки.'
),
(
    'berlin-gaerten-der-welt-station-wolkenhain',
    'berlin-gaerten-der-welt',
    'Волькенхайн',
    'upper',
    52.5268,
    13.5838,
    20,
    'Промежуточная станция на Кинберге рядом со смотровой площадкой.'
),
(
    'berlin-gaerten-der-welt-station-gaerten-der-welt',
    'berlin-gaerten-der-welt',
    'Сады мира',
    'lower',
    52.5254,
    13.5753,
    30,
    'Станция у входа в парк со стороны Блумбергер-Дамм.'
)
ON CONFLICT(id) DO UPDATE SET
    title = excluded.title,
    station_role = excluded.station_role,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    sort_order = excluded.sort_order,
    note = excluded.note,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now');

-- TODO(object-mode): добавить EngineeringPoint/hotspot seed для опор, приводных
-- и станционных инженерных узлов после появления таблицы EngineeringPoint.
-- Текущий vertical slice намеренно хранит только проверяемые станции,
-- направления, сегменты и демо-геометку видео; координаты ниже ручные,
-- не геодезические инженерные точки.
INSERT INTO route_directions (
    id,
    transport_object_id,
    from_station_id,
    to_station_id,
    title,
    direction_label,
    sort_order,
    note
) VALUES
(
    'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-station-kienbergpark',
    'berlin-gaerten-der-welt-station-gaerten-der-welt',
    'Киенбергпарк -> Сады мира',
    'от Киенбергпарка к Садам мира',
    10,
    'Направление через Волькенхайн от метро U5 к главному входу в парк.'
),
(
    'berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-station-gaerten-der-welt',
    'berlin-gaerten-der-welt-station-kienbergpark',
    'Сады мира -> Киенбергпарк',
    'от Садов мира к Киенбергпарку',
    20,
    'Обратное направление к U5 с промежуточной остановкой на Кинберге.'
)
ON CONFLICT(id) DO UPDATE SET
    from_station_id = excluded.from_station_id,
    to_station_id = excluded.to_station_id,
    title = excluded.title,
    direction_label = excluded.direction_label,
    sort_order = excluded.sort_order,
    note = excluded.note,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now');

INSERT INTO route_segments (
    id,
    transport_object_id,
    route_direction_id,
    from_station_id,
    to_station_id,
    segment_order,
    title,
    direction_label,
    note
) VALUES
(
    'berlin-gaerten-der-welt-segment-kienbergpark-wolkenhain',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten',
    'berlin-gaerten-der-welt-station-kienbergpark',
    'berlin-gaerten-der-welt-station-wolkenhain',
    10,
    'Киенбергпарк -> Волькенхайн',
    'вверх к Волькенхайну',
    'Первый подъем от U5 к Кинбергу.'
),
(
    'berlin-gaerten-der-welt-segment-wolkenhain-gaerten',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten',
    'berlin-gaerten-der-welt-station-wolkenhain',
    'berlin-gaerten-der-welt-station-gaerten-der-welt',
    20,
    'Волькенхайн -> Сады мира',
    'вниз к Садам мира',
    'Спуск к входу в парк.'
),
(
    'berlin-gaerten-der-welt-segment-gaerten-wolkenhain',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark',
    'berlin-gaerten-der-welt-station-gaerten-der-welt',
    'berlin-gaerten-der-welt-station-wolkenhain',
    10,
    'Сады мира -> Волькенхайн',
    'вверх к Волькенхайну',
    'Обратный подъем от парка к Кинбергу.'
),
(
    'berlin-gaerten-der-welt-segment-wolkenhain-kienbergpark',
    'berlin-gaerten-der-welt',
    'berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark',
    'berlin-gaerten-der-welt-station-wolkenhain',
    'berlin-gaerten-der-welt-station-kienbergpark',
    20,
    'Волькенхайн -> Киенбергпарк',
    'вниз к Киенбергпарку',
    'Спуск к U5.'
)
ON CONFLICT(id) DO UPDATE SET
    route_direction_id = excluded.route_direction_id,
    from_station_id = excluded.from_station_id,
    to_station_id = excluded.to_station_id,
    segment_order = excluded.segment_order,
    title = excluded.title,
    direction_label = excluded.direction_label,
    note = excluded.note,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now');

INSERT INTO media_assets (
    id,
    transport_object_id,
    kind,
    local_path,
    caption,
    taken_on,
    latitude,
    longitude,
    coordinate_source,
    geo_note,
    station_id,
    route_direction_id,
    route_segment_id,
    created_at
) VALUES
(
    'berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten',
    'berlin-gaerten-der-welt',
    'video',
    'media/berlin-gaerten-der-welt/demo-video-kienbergpark-to-gaerten.mp4',
    'Демо-видео поездки от Киенбергпарка к Садам мира через Волькенхайн.',
    '2026-05-30',
    52.5270,
    13.5838,
    'manual',
    'Координата вручную поставлена примерно в середине маршрута, чтобы будущий UI мог показать направление видео.',
    NULL,
    'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten',
    'berlin-gaerten-der-welt-segment-kienbergpark-wolkenhain',
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
)
ON CONFLICT(id) DO UPDATE SET
    transport_object_id = excluded.transport_object_id,
    kind = excluded.kind,
    local_path = excluded.local_path,
    caption = excluded.caption,
    taken_on = excluded.taken_on,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    coordinate_source = excluded.coordinate_source,
    geo_note = excluded.geo_note,
    station_id = excluded.station_id,
    route_direction_id = excluded.route_direction_id,
    route_segment_id = excluded.route_segment_id;
