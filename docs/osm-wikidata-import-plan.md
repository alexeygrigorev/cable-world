# План импорта и обогащения данных из OSM/Wikidata

Документ фиксирует исследование для GitHub issue #9. Цель - безопасно наполнять каталог канатных дорог, фуникулеров и необычного транспорта без production-импортера и без изменения текущей модели данных.

## Рекомендация

Для ближайших версий нужен полуавтоматический импорт через проверяемый staging-файл, а не прямой pipeline в SQLite.

Причина: OSM хорошо дает геометрию, координаты, теги инфраструктуры и внешние ссылки, Wikidata хорошо дает стабильный Q-id, названия на разных языках, страну, координаты, оператора и официальный сайт. Но оба источника не гарантируют точный `transport_type_id`, актуальный `operational_status`, русское описание и семейно-полезный отбор объектов. Эти поля должны проходить ручную редакторскую проверку перед попаданием в seed.

Практический поток:

1. собрать кандидатов из OSM Overpass и Wikidata SPARQL в staging JSON;
2. автоматически нормализовать только очевидные поля: координаты, исходные id, ссылки, черновой `transport_type_id`, черновой `opened_year`;
3. вручную проверить тип, название на русском, описание, статус эксплуатации и источник статуса;
4. только после проверки превращать записи в seed или будущий импортный каталог.

Прямой автоматический импорт в `transport_objects` не рекомендуется: он будет создавать дубликаты линий, станций и route relations, путать туристические канатные дороги с горнолыжными подъемниками, а также выставлять ложную актуальность статуса эксплуатации.

## Минимальный формат staging-записи

Формат совместим с текущим `TransportObject`: обязательные доменные поля совпадают с текущей моделью, а поля источников остаются рядом в staging-слое. Хранить `source_ids` в SQLite можно только после отдельного issue и миграции.

```json
{
  "id": "berlin-gaerten-der-welt",
  "transport_type_id": "cable_gondola",
  "visit_status_id": "not_visited",
  "country": "Германия",
  "region": "Берлин",
  "city": "Берлин",
  "latitude": 52.5396,
  "longitude": 13.5763,
  "localized": {
    "ru": {
      "title": "Канатная дорога в садах мира Берлина",
      "description": "Гондольная канатная дорога над парком Gärten der Welt."
    },
    "de": {
      "title": "Seilbahn in den Gärten der Welt",
      "description": ""
    },
    "en": {
      "title": "Gärten der Welt cable car",
      "description": ""
    }
  },
  "opened_year": 2017,
  "operator": "Leitner Ropeways",
  "manufacturer": "Leitner Ropeways",
  "operational_status": "unknown",
  "status_checked_at": "",
  "status_source_url": "",
  "status_note": "",
  "source_ids": {
    "osm": ["way/123456789"],
    "wikidata": "Q123456"
  },
  "source_urls": [
    "https://www.openstreetmap.org/way/123456789",
    "https://www.wikidata.org/wiki/Q123456"
  ],
  "review": {
    "state": "candidate",
    "reviewed_by": "",
    "reviewed_at": "",
    "notes": "Требуется ручная проверка типа, статуса и русского описания."
  }
}
```

Правила совместимости:

- `id`, `transport_type_id`, `visit_status_id` и `operational_status` остаются стабильными ASCII id, как описано в `docs/data-model.md` и `docs/i18n-strategy.md`;
- `localized.ru.title` и `localized.ru.description` обязательны, потому что текущий UX русский;
- для текущей SQLite-схемы `localized.ru.title` мапится в `TransportObject.title`, `localized.ru.description` - в `TransportObject.description`;
- `country`, `region`, `city`, `status_note` в текущем seed остаются русскими display/content-полями;
- `source_ids`, `source_urls` и `review` не являются production-полями текущей модели и не должны попадать в SQLite без отдельного issue;
- `operational_status` по умолчанию `unknown`, если нет свежего официального источника.

## OSM: проверенные теги

В OSM для канатных дорог используется ключ `aerialway=*`, а не `cableway=*`. Страница ключа описывает транспорт на тросах: cable cars, gondolas, chair lifts, drag lifts и zip lines: <https://wiki.openstreetmap.org/wiki/Key:aerialway>.

| Задача | OSM-теги | Маппинг в каталог | Риск |
| --- | --- | --- | --- |
| Гондольная канатная дорога | `aerialway=gondola`, `name=*`, `operator=*`, `wikidata=*`, `website=*` | `cable_gondola` или после ручной проверки `cable_urban`/`cable_tourist` | OSM не всегда различает городскую и туристическую роль |
| Маятниковая канатная дорога | `aerialway=cable_car` | `cable_aerial_tram` | термин `cable_car` в разных странах может означать разные системы |
| Другие подвесные канатные системы | `aerialway=chair_lift`, `aerialway=mixed_lift`, `aerialway=goods`, `aerialway=zip_line` | обычно не импортировать автоматически; возможен `special_transport_system` после ручного отбора | много горнолыжной инфраструктуры и служебных линий |
| Станции канатной дороги | `aerialway=station`, `name=*` | не `TransportObject`, можно использовать позже для `ObjectStation` | станция может дублировать линию как отдельный объект |
| Фуникулер | `railway=funicular`, `route=funicular`, `station=funicular`, `operator=*` | `funicular_classic`, `funicular_modern` или `funicular_water` после проверки | OSM допускает похожие наклонные лифты как funicular |
| Зубчатая железная дорога | `railway=rail` + `rack=yes`; полезны `gauge=*`, `usage=*`, `service=*` | `rail_cog` | часть линии может быть зубчатой, а не весь маршрут |
| Горная железная дорога | `railway=rail`, `railway=narrow_gauge`, `usage=tourism` или route relation | `rail_mountain` после ручной проверки | тегов недостаточно для уверенного определения |
| Монорельс | `railway=monorail`, `route=monorail` | `monorail` | аттракционы и park transport могут быть нерелевантны |
| Подвесная железная дорога | `railway=monorail` + `monorail=hanging` | `rail_suspended` или `suspended_train` после ручной проверки | отдельного универсального `railway=suspended` нет; это подтип monorail |
| Оператор | `operator=*`, `operator:wikidata=*`, `operator:website=*` | `operator`; Q-id только в staging | названия операторов не всегда нормализованы |
| Сайт | `website=*`, `contact:website=*` | кандидат для `status_source_url` только если страница подтверждает статус | homepage не равен источнику текущего статуса |
| Координаты | геометрия node/way/relation, центр линии или ручная точка | `latitude`, `longitude` | центр route relation может оказаться в стороне от полезной точки карты |
| Дата открытия | `start_date=*`; `opening_date=*` только для будущего открытия | `opened_year` после парсинга года | `opening_date` в прошлом надо перепроверять |
| Актуальность проверки | `check_date=*`, `survey:date=*`, `source:date=*` | может помочь `status_checked_at`, но не заменяет источник статуса | дата проверки OSM не означает, что объект работает |
| Внешние id | `wikidata=*`, OSM element id `node/way/relation` | `source_ids` в staging | OSM id может смениться при ремаппинге |

Для rail-объектов можно использовать OpenRailwayMap как дополнительный просмотрщик OSM-данных, но не как отдельный источник истины. Его документация прямо говорит, что проект построен на OSM-данных и покрывает rail-mounted systems including funiculars, но не aerialways, monorails and maglevs: <https://wiki.openstreetmap.org/wiki/OpenRailwayMap>.

## Wikidata: проверенные поля

| Задача | Wikidata property | Маппинг в каталог | Риск |
| --- | --- | --- | --- |
| Тип объекта | `P31` instance of, с учетом `P279` subclass of | черновой `transport_type_id` | классификация неполная и зависит от языка/страны |
| Координаты | `P625` coordinate location | `latitude`, `longitude` | координата может быть станцией, офисом или общей точкой |
| Страна | `P17` country | русское `country` через label/Q-id lookup | спорные территории и устаревшие страны требуют ручной политики |
| Оператор | `P137` operator | `operator`, label выбранной локали | оператор может быть историческим или несколько операторов |
| Официальный сайт | `P856` official website | кандидат `source_urls`; для `status_source_url` только если подтверждает статус | старые сайты сохраняются в Wikidata и не всегда актуальны |
| Дата создания/открытия | `P571` inception; иногда `P1619` date of official opening | `opened_year` | не всегда дата начала эксплуатации линии |
| Производитель | `P176` manufacturer | `manufacturer` | часто указан производитель подвижного состава, а не системы |
| OSM relation id | `P402` OpenStreetMap relation ID | `source_ids.wikidata_osm_relation` в staging | есть только для relation; node/way представлены отдельными property |
| OSM way id | `P10689` OpenStreetMap way ID | `source_ids.wikidata_osm_way` в staging | свежая property, покрытие неполное |
| OSM node id | `P11693` OpenStreetMap node ID | `source_ids.wikidata_osm_node` в staging | покрытие неполное |
| Внешние источники | references на statements, `stated in`, `reference URL`, retrieved date | `source_urls`, `review.notes` | references часто отсутствуют или ведут на агрегаторы |

Проверенные страницы свойств Wikidata:

- `P31` instance of: <https://www.wikidata.org/wiki/Property:P31>;
- `P625` coordinate location: <https://www.wikidata.org/wiki/Property:P625>;
- `P137` operator: <https://www.wikidata.org/wiki/Property:P137>;
- `P856` official website: <https://www.wikidata.org/wiki/Property:P856>;
- `P402` OpenStreetMap relation ID: <https://www.wikidata.org/wiki/Property:P402>;
- `P10689` OpenStreetMap way ID: <https://www.wikidata.org/wiki/Property:P10689>;
- `P11693` OpenStreetMap node ID: <https://www.wikidata.org/wiki/Property:P11693>.

## Нормализация типов

Автоматическое правило должно выдавать только черновой `transport_type_id`.

| Условие | Черновой тип | Требование перед seed |
| --- | --- | --- |
| `aerialway=gondola` | `cable_gondola` | проверить роль: городская, туристическая или горная |
| `aerialway=cable_car` | `cable_aerial_tram` | проверить, что это маятниковая канатная дорога |
| `railway=funicular` или `route=funicular` | `funicular_classic` | проверить, не наклонный лифт и не водяной фуникулер |
| `railway=rail` + `rack=yes` | `rail_cog` | проверить, что объект в каталоге - именно зубчатая линия |
| `railway=monorail` + `monorail=hanging` | `suspended_train` | вручную выбрать между `suspended_train` и `rail_suspended` |
| `railway=monorail` | `monorail` | исключить аттракционы и служебные системы |
| нет уверенного правила | `special_transport_system` | ручное решение обязательно |

## Нормализация эксплуатационного статуса

`operational_status` нельзя надежно выводить только из OSM/Wikidata.

Разрешенные значения остаются текущими: `active`, `active_seasonal`, `temporarily_closed_planned`, `temporarily_closed_unplanned`, `closed`, `historical`, `unknown`.

Правила:

- если есть свежая официальная страница оператора с расписанием или сообщением о работе, можно ставить `active`, `active_seasonal` или временное закрытие и заполнять `status_checked_at`, `status_source_url`, `status_note`;
- если есть только OSM lifecycle-тег (`disused:*`, `abandoned:*`, `construction:*`) или Wikidata без свежей ссылки, статус остается `unknown`, а сигнал уходит в `review.notes`;
- `closed` и `historical` ставятся только после ручной проверки по надежному источнику;
- `website=*` и `P856` сами по себе не являются источником статуса.

## i18n-стратегия

Импортный слой должен следовать текущей стратегии:

- `ru` обязателен для каждого объекта;
- `de` и `en` опциональны и могут подтягиваться из Wikidata labels, но не заменяют русскую редактуру;
- стабильные id и enum-поля не переводятся;
- для текущей схемы seed берет русские поля из `localized.ru`;
- если в Wikidata нет русского label, запись остается кандидатом до ручного названия, а не попадает в seed с английским title.

## Риски качества данных

- Дубликаты: OSM может иметь way линии, relation маршрута и отдельные станции; Wikidata может описывать линию, систему, станцию или оператора.
- Разная гранулярность: каталог хочет один `TransportObject`, а источники могут описывать отдельные пути, станции, секции и route relations.
- Нестабильные id OSM: node/way/relation id полезны для traceability, но не должны быть главным `TransportObject.id`.
- Неполные типы: `railway=monorail` покрывает разные технологии; `aerialway=*` покрывает и релевантные, и нерелевантные подъемники.
- Статусы устаревают: OSM/Wikidata не являются расписанием оператора.
- Лицензии и атрибуция: OSM - ODbL, Wikidata structured data - CC0; импортный pipeline должен хранить ссылки на источники и показывать/документировать атрибуцию там, где понадобится.
- Русский контент: автоматический перевод или label из Wikidata не достаточен для пользовательского описания.

## Follow-up implementation issues

Созданы отдельные implementation issues:

1. #28 «Добавить staging JSON schema и валидатор кандидатов импорта»: фиксирует обязательные поля, ASCII id, обязательный `localized.ru`, допустимые `transport_type_id` и `operational_status`, запрет записи `source_ids` в SQLite.
2. #29 «Сделать прототип сборщика кандидатов из OSM/Wikidata»: Overpass/SPARQL запросы, merge по `wikidata`/OSM id, экспорт только в staging JSON, без записи в production-хранилище.
3. #30 «Добавить ручной review workflow для кандидатов импорта»: список кандидатов, поля проверки, причины отклонения, генерация проверенного seed только из `review.state = "approved"`.

## Источники

- OSM `aerialway=*`: <https://wiki.openstreetmap.org/wiki/Key:aerialway>
- OSM `railway=funicular`: <https://wiki.openstreetmap.org/wiki/Tag:railway%3Dfunicular>
- OSM `route=funicular`: <https://wiki.openstreetmap.org/wiki/Tag:route%3Dfunicular>
- OSM `railway=rail` и `rack=yes`: <https://wiki.openstreetmap.org/wiki/Tag:railway%3Drail>
- OSM `railway=monorail` и `monorail=hanging`: <https://wiki.openstreetmap.org/wiki/Tag:railway%3Dmonorail>
- OSM `operator=*`: <https://wiki.openstreetmap.org/wiki/Key:operator>
- OSM `website=*`: <https://wiki.openstreetmap.org/wiki/Key:website>
- OSM `start_date=*`: <https://wiki.openstreetmap.org/wiki/Key:start_date>
- OSM `opening_date=*`: <https://wiki.openstreetmap.org/wiki/Key:opening_date>
- OSM `check_date=*`: <https://wiki.openstreetmap.org/wiki/Key:check_date>
- Wikidata properties: <https://www.wikidata.org/wiki/Property:P31>, <https://www.wikidata.org/wiki/Property:P625>, <https://www.wikidata.org/wiki/Property:P137>, <https://www.wikidata.org/wiki/Property:P856>, <https://www.wikidata.org/wiki/Property:P402>, <https://www.wikidata.org/wiki/Property:P10689>, <https://www.wikidata.org/wiki/Property:P11693>
