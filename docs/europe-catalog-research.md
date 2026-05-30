# Каталог Европы: исследование кандидатов

Дата среза: 2026-05-30. Документ не является seed-файлом и не меняет production-каталог. Цель - дать редакторский shortlist для будущего расширения seed по Европе и показать staging-примеры, совместимые со схемой `schemas/staging_catalog_candidate.schema.json`.

## Область

Страны подробного среза:

- Португалия
- Франция
- Италия
- Чехия
- Словакия
- Польша

Интересующие типы транспорта:

- канатные дороги: `cable_gondola`, `cable_aerial_tram`, `cable_urban`, `cable_tourist`;
- фуникулеры: `funicular_classic`, `funicular_water`, `funicular_modern`;
- зубчатые железные дороги: `rail_cog`, `rail_mountain`;
- подвесные, монорельсовые и уникальные системы: `suspended_train`, `monorail`, `special_transport_system`, `unique_engineering_object`, при необходимости `elevator_inclined` и `elevator_panoramic`.

## Методика и уровень уверенности

Уровни уверенности:

- высокая - объект подтвержден официальной страницей оператора, города или профильной транспортной организации;
- средняя - объект хорошо известен и присутствует в нескольких справочниках, но перед seed нужна проверка текущего расписания/статуса;
- низкая - объект спорной классификации, сезонный, исторический или требует проверки на месте.

Для seed в первую очередь стоит брать объекты с официальной страницей, понятной геометрией и стабильным типом. OSM/Wikidata можно использовать как индекс и источник внешних id, но эксплуатационный статус нужно подтверждать операторским сайтом.

## Португалия

Общий вывод: Португалия хорошо подходит для первого seed-пакета: есть компактная группа городских фуникулеров Лиссабона и Порту, уникальный водобалластный фуникулер Bom Jesus, а также туристические канатные дороги Мадейры и Гайи.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Elevador do Bom Jesus do Monte | Брага | `funicular_water` | высокая | первым |
| Ascensor da Bica | Лиссабон | `funicular_classic` | высокая | первым после проверки статуса |
| Ascensor da Glória | Лиссабон | `funicular_classic` | средняя | после проверки статуса и безопасности |
| Ascensor do Lavra | Лиссабон | `funicular_classic` | высокая | первым после проверки статуса |
| Elevador de Santa Justa | Лиссабон | `elevator_vertical` или `elevator_panoramic` | высокая | вторым |
| Funicular dos Guindais | Порту | `funicular_modern` | высокая | первым |
| Teleférico do Funchal / Madeira Cable Car | Фуншал | `cable_gondola` | высокая | первым |
| Teleférico de Gaia | Вила-Нова-ди-Гая | `cable_tourist` | средняя | вторым |
| Ascensor da Nazaré | Назаре | `funicular_classic` | средняя | вторым |

Что включать первым: Bom Jesus как уникальный водобалластный объект; Funicular dos Guindais; Funchal Cable Car; один или два лиссабонских ascensores после актуальной проверки статуса.

Источники:

- Carris, страница лифтов и фуникулеров Лиссабона: https://www.carris.pt/descubra/frota/ascensores-e-elevador/
- STCP Serviços, Funicular dos Guindais: https://www.stcpservicos.pt/transporte-publico/funicular-dos-guindais
- Bom Jesus do Monte, Elevator/Funicular: https://bomjesus.pt/bom-jesus/elevator-or-funicular/
- ERIH, Bom Jesus Funicular: https://www.erih.net/i-want-to-go-there/site/bom-jesus-funicular
- Madeira Botanical Garden Cable Car: https://www.telefericojardimbotanico.com/

Риски: у лиссабонских фуникулеров нужна отдельная проверка фактического состояния на дату импорта; не смешивать вертикальный Elevador de Santa Justa с классическим фуникулером.

## Франция

Общий вывод: Франция дает хороший набор городских канатных дорог, классических/современных фуникулеров и зубчатых горных железных дорог. Для seed лучше разделить городские линии и высокогорные туристические объекты.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Téléphérique Grenoble-Bastille | Гренобль | `cable_tourist` | высокая | первым |
| Téléo | Тулуза | `cable_urban` | высокая | первым |
| Téléphérique de Brest | Брест | `cable_urban` | высокая | первым |
| Funiculaire de Montmartre | Париж | `funicular_modern` или `elevator_inclined` | высокая | первым |
| Funiculaires de Lyon F1/F2 | Лион | `funicular_classic` | средняя | вторым |
| Funiculaire d'Évian-les-Bains | Эвиан-ле-Бен | `funicular_classic` | средняя | вторым |
| Chemin de fer du Montenvers | Шамони | `rail_cog` | высокая | первым |
| Tramway du Mont-Blanc | Сен-Жерве / Нид-д'Эгль | `rail_cog` | высокая | первым |
| Train de la Rhune | Страна Басков | `rail_cog` | высокая | первым |
| Panoramique des Dômes | Пюи-де-Дом | `rail_cog` | средняя | вторым |
| Poma 2000 | Лан | `special_transport_system` | средняя, исторический | не первым |

Что включать первым: Grenoble-Bastille, Téléo, Brest cable car, Montmartre, Montenvers, Tramway du Mont-Blanc и Train de la Rhune.

Источники:

- Grenoble-Bastille: https://bastille-grenoble.fr/en/
- Brest Métropole, téléphérique: https://brest.fr/telepherique
- POMA, Téléo Toulouse: https://www.poma.net/en/work/teleo/
- RATP, traffic page for Montmartre funicular: https://www.ratp.fr/en/infos-trafic/metro/FUN
- Association des funiculaires de France, Montmartre: https://funiculaires-france.fr/montmartre/?lang=en

Риски: в Альпах много сезонных/горнолыжных канатных дорог; для MVP-catalog стоит брать только транспортно или инженерно значимые объекты, иначе seed быстро превратится в справочник подъемников.

## Италия

Общий вывод: Италия - самый насыщенный рынок из шести стран. Основной риск - слишком быстро набрать десятки городских и туристических фуникулеров. Для первого seed нужен curated-набор: Неаполь, Комо, Генуя, Бергамо, Турин, Перуджа.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Funicolare Como-Brunate | Комо / Брунате | `funicular_classic` | высокая | первым |
| Funicolare Centrale | Неаполь | `funicular_classic` | высокая | первым |
| Funicolare di Chiaia | Неаполь | `funicular_classic` | высокая | первым |
| Funicolare di Montesanto | Неаполь | `funicular_classic` | высокая | первым |
| Funicolare di Mergellina | Неаполь | `funicular_classic` | высокая | вторым |
| Funicolare Zecca-Righi | Генуя | `funicular_classic` | средняя | первым |
| Funicolare Sant'Anna | Генуя | `elevator_inclined` или `funicular_modern` | средняя | вторым |
| Funicolare di Bergamo Alta | Бергамо | `funicular_classic` | средняя | первым |
| Tranvia Sassi-Superga | Турин | `rail_cog` | высокая | первым |
| Minimetrò Perugia | Перуджа | `special_transport_system` | высокая | первым |
| People Mover Venezia | Венеция | `special_transport_system` | средняя | вторым |
| Funivia Renon | Больцано / Сопрабольцано | `cable_gondola` | средняя | вторым |

Что включать первым: Como-Brunate; 2-3 неаполитанских фуникулера; Sassi-Superga; Minimetrò Perugia; один объект Генуи или Бергамо.

Источники:

- Funicolare Como-Brunate: https://www.funicolarecomo.it/
- ANM Napoli, карта мобильности с фуникулерами: https://www.anm.it/resource/1768990802000/cartadellamobilita25
- GTT, Tranvia Sassi-Superga: https://www.gtt.to.it/cms/turismo/sassisup
- Minimetrò Perugia: https://www.minimetrospa.it/
- Comune di Perugia, Minimetrò: https://turismo.comune.perugia.it/pagine/minimetro

Риски: у Неаполя несколько близких линий одного типа; импорт должен защищаться от дублей станция/линия и от одинаковых названий на разных языках.

## Чехия

Общий вывод: Чехия компактна, но важна для каталога из-за Праги, Карловых Вар и Ветруше. Текущий статус Petřín требует явной пометки: на 2026-05-30 линия не должна идти в seed как active.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Lanová dráha na Petřín | Прага | `funicular_classic` | высокая | первым, но статус `temporarily_closed_planned` |
| Lanová dráha Diana | Карловы Вары | `funicular_classic` | средняя | первым |
| Lanová dráha Imperial | Карловы Вары | `funicular_classic` | средняя | вторым |
| Lanová dráha Větruše | Усти-над-Лабем | `cable_aerial_tram` или `cable_tourist` | высокая | первым |
| Lanová dráha na Letnou | Прага | `funicular_classic` | средняя, исторический | не первым |
| Ještěd cable car | Либерец | `cable_aerial_tram` | средняя, закрыт/аварийная история | не первым до проверки |

Что включать первым: Petřín с плановым закрытием, Větruše, Diana. Imperial и исторические объекты - после ручной проверки.

Источники:

- DPP, Funicular to Petřín: https://www.dpp.cz/en/entertainment-and-experience/funicular-to-petrin
- DPP, новые вагоны Petřín, апрель 2026: https://www.dpp.cz/en/company/news/detail/342_3304-in-pictures-new-petrin-funicular-cars-installed-on-the-line
- Ústí nad Labem, Větruše centre: https://www.usti.cz/en/tourists/entertainment-sport/vetruse-centre.html
- Туристический портал Среднечешского нагорья, Větruše cable car: https://www.ceskestredohori.info/en/detail/cable-car-in-vetrus-usti-nad-labem
- Karlovy Vary tourist portal: https://www.karlovyvary.cz/en

Риски: Petřín сейчас в реконструкции; Ještěd нельзя добавлять без отдельного источника по восстановлению/закрытию.

## Словакия

Общий вывод: Словацкий shortlist в основном горный: Высокие Татры и несколько туристических гондол. Для seed лучше выбрать один фуникулер, один высокогорный канатный маршрут и одну современную туристическую гондолу.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Starý Smokovec-Hrebienok | Высокие Татры | `funicular_classic` | высокая | первым |
| Tatranská Lomnica-Skalnaté pleso-Lomnický štít | Высокие Татры | `cable_aerial_tram` / `cable_gondola` | высокая | первым |
| Gondola Bachledka | Бахледова долина | `cable_gondola` | высокая | вторым |
| Štrbské Pleso cable/chair systems | Высокие Татры | `cable_tourist` | средняя | не первым |
| Jasná / Chopok cable systems | Низкие Татры | `cable_tourist` | средняя | не первым |

Что включать первым: Hrebienok как фуникулер; Lomnický štít как высокогорная канатная дорога; Bachledka как современная гондола к туристическому объекту.

Источники:

- Visit Tatry, cable cars: https://visittatry.sk/en/post/cable-cars
- Visit Tatry, ascent to Lomnický štít: https://www.tatry.sk/en/vystup-na-lomnicky-stit/
- Bachledka, gondola information: https://bachledka.sk/kabinkova-lanovka-bachledka
- Bachledka, FAQ: https://bachledka.sk/en/info-faq
- TMR/Vysoké Tatry passenger information: https://www.vt.sk/fileadmin/resort_upload/vt/Basic_cableway_passenger_information__TATRANSKA_LOMNICA__STARY_SMOKOVEC__STRBSKE_PLESO_resort__1_.pdf

Риски: большинство объектов сезонные или зависят от погоды; статус `active_seasonal` лучше ставить только после проверки расписания на дату импорта.

## Польша

Общий вывод: Польша дает сильный curated-набор: PKL в Татрах и Бескидах, городская Polinka во Вроцлаве и исторические фуникулеры. Для first seed лучше выбрать Kasprowy Wierch, Gubałówka и Polinka.

Кандидаты:

| Объект | Место | Тип | Уверенность | Приоритет |
| --- | --- | --- | --- | --- |
| Kolej linowa Kasprowy Wierch | Закопане / Кузнице | `cable_aerial_tram` | высокая | первым |
| Kolej linowo-terenowa Gubałówka | Закопане | `funicular_classic` | высокая | первым |
| Kolej linowo-terenowa Góra Parkowa | Крыница-Здруй | `funicular_classic` | высокая | вторым |
| Polinka | Вроцлав | `cable_urban` | высокая | первым |
| Kolej linowo-terenowa Żar | Мендзыбродзе-Живецке | `funicular_classic` | средняя | вторым |
| Elka | Хожув / Silesian Park | `cable_tourist` | средняя | вторым |

Что включать первым: Kasprowy Wierch, Gubałówka, Polinka. Góra Parkowa и Żar - следующая партия после проверки точных координат и расписания.

Источники:

- PKL, Kasprowy Wierch cable car: https://www.pkl.pl/kasprowy-wierch/kolej-linowa-kasprowy-wierch.html?setlang=1
- Zakopane official, Gubałówka funicular: https://www.zakopane.pl/en/tourist-area/tourism/mountain-ropeways/gubalowka-funicular-railway
- Zakopane official, Kasprowy Wierch cable railway: https://www.zakopane.pl/en/tourist-area/tourism/mountain-ropeways/kasprowy-wierch-cable-railway
- Wrocław University of Science and Technology, Polinka: https://pwr.edu.pl/en/polinka/
- Visit Wrocław, Polinka: https://visitwroclaw.eu/en/place/polinka

Риски: у PKL часть линий сезонная и горная; для seed нужно хранить дату проверки статуса и источник расписания.

## Staging-примеры

См. `examples/staging/europe_catalog_candidates.json`. В файле намеренно только 6 кандидатов - по одному на страну - чтобы проверить совместимость со схемой и дать редакторский шаблон без массового импорта.

## Seed review 2026-05-30

Статус review: все 6 staging-кандидатов переведены в `review.state = "approved"` без изменения UI, release-файлов, `VERSION`, SQLite seed или runtime-сцен. Проверка выполнялась как редакторский seed-review для #35; перенос в текущий demo/SQLite seed уже был сделан отдельным инкрементом, а этот review фиксирует доказательства.

Approved-кандидаты:

| Страна | ID | Тип | Статус | Решение |
|---|---|---|---|---|
| Португалия | `braga-bom-jesus-funicular` | `funicular_water` | `unknown` | Редкая водобалластная технология подтверждена источниками; статус оставлен `unknown`, потому что официальный источник не доказывает текущее расписание на дату проверки. |
| Франция | `grenoble-bastille-cable-car` | `cable_tourist` | `unknown` | Туристическая горная канатка; статус оставлен `unknown`, потому что сезонность и техобслуживание требуют проверки live-расписания перед поездкой. |
| Италия | `como-brunate-funicular` | `funicular_classic` | `unknown` | Классический фуникулер с отдельным официальным сайтом; статус оставлен `unknown`, потому что расписание нужно подтверждать по официальному источнику перед поездкой. |
| Чехия | `prague-petrin-funicular` | `funicular_classic` | `temporarily_closed_planned` | Petřín нельзя показывать как `active`: DPP сообщает о полной реконструкции и плановой приостановке работы. |
| Словакия | `stary-smokovec-hrebienok-funicular` | `funicular_classic` | `unknown` | Горный объект в Высоких Татрах; статус оставлен `unknown`, потому что расписание зависит от сезона и текущих условий. |
| Польша | `zakopane-kasprowy-wierch-cable-car` | `cable_aerial_tram` | `unknown` | Высокогорная канатная дорога; статус оставлен `unknown`, потому что работа зависит от погоды, лимитов нацпарка и текущего расписания PKL. |

Обязательные поля перед seed:

- `transport_type_id` проверен для каждого объекта и не смешивает линию, станцию и оператора.
- Координаты сохранены как точка будущего `TransportObject`: нижняя станция или центр линии, достаточный для map seed.
- `operational_status`, `status_checked_at = "2026-05-30"` и официальный `status_source_url` заполнены у каждого кандидата.
- Для Petřín сохранен `temporarily_closed_planned`; `active` запрещен до новой проверки после открытия.
- Для Франции, Италии, Словакии и Польши сезонность/горный режим явно отражены в `review.notes` и статусных пояснениях.

Duplicate audit:

| ID | Slug | OSM | Wikidata | Название линии/станции |
|---|---|---|---|---|
| `braga-bom-jesus-funicular` | unique | `not_provided/not_required_for_seed` | `Q892885` unique | Bom Jesus do Monte Funicular unique |
| `grenoble-bastille-cable-car` | unique | `not_provided/not_required_for_seed` | `Q1520467` unique | Grenoble-Bastille cable car unique |
| `como-brunate-funicular` | unique | `not_provided/not_required_for_seed` | `Q1055831` unique | Como-Brunate funicular unique |
| `prague-petrin-funicular` | unique | `relation/5617683` unique | `Q1502676` unique | Petřín funicular unique |
| `stary-smokovec-hrebienok-funicular` | unique | `not_provided/not_required_for_seed` | `Q7607830` unique | Starý Smokovec-Hrebienok funicular unique |
| `zakopane-kasprowy-wierch-cable-car` | unique | `not_provided/not_required_for_seed` | `Q637591` unique | Kasprowy Wierch cable car unique |

Если OSM id отсутствует, это не пустое поле review: в `review.notes` зафиксировано `OSM id=not_provided/not_required_for_seed`, потому что для первого seed достаточно официального источника, Wikidata id и ручной проверки названия. Для более крупного импорта OSM id нужно добирать отдельным import-review этапом.

## Рекомендация для future seed

Пакет 1, высокий сигнал и низкий риск дублей:

- Португалия: Bom Jesus do Monte, Guindais, Teleférico do Funchal.
- Франция: Grenoble-Bastille, Téléo, Brest, Montmartre, Montenvers.
- Италия: Como-Brunate, Sassi-Superga, Minimetrò Perugia, 2 линии Неаполя.
- Чехия: Petřín с `temporarily_closed_planned`, Větruše, Diana.
- Словакия: Hrebienok, Lomnický štít.
- Польша: Kasprowy Wierch, Gubałówka, Polinka.

Пакет 2:

- дополнительные фуникулеры Лиссабона, Генуи, Бергамо, Лиона, Карловых Вар;
- Góra Parkowa, Żar, Bachledka;
- исторические и закрытые объекты только с `historical` или `closed`.

Перед seed-review для каждого кандидата нужны:

- точка координат будущего TransportObject, предпочтительно нижняя станция или центр линии;
- один официальный `status_source_url`;
- выбранный `transport_type_id` без смешения линии, станции и оператора;
- проверка дубликатов по OSM/Wikidata и локальному slug;
- краткое русское описание без рекламного текста.
