# Доменная модель данных MVP

Документ фиксирует минимальную модель данных для MVP «Мир Троссов». Модель нужна для локального SQLite-хранилища, будущего импорта каталога и проверки того, что демо-данные соответствуют тем же сущностям.

## Сущности

### TransportObject

Объект транспорта или инженерное сооружение, которое показывается на карте и в списке.

Поля MVP:

- `id` - стабильный текстовый идентификатор объекта;
- `title` - название объекта;
- `transport_type_id` - ссылка на справочник типов транспорта;
- `country` - страна;
- `region` - регион, земля, кантон или область;
- `city` - город или ближайший населенный пункт;
- `latitude` - широта;
- `longitude` - долгота;
- `description` - краткое описание для карточки;
- `notes` - семейные заметки;
- `opened_year` - год открытия, если известен;
- `operator` - оператор, если известен;
- `manufacturer` - производитель, если известен;
- `operational_status` - текущий эксплуатационный статус объекта;
- `status_checked_at` - дата проверки эксплуатационного статуса в формате ISO `YYYY-MM-DD`, если известна;
- `status_source_url` - ссылка на источник статуса, если он есть;
- `status_note` - короткое русское пояснение к эксплуатационному статусу;
- `created_at` - дата создания записи;
- `updated_at` - дата последнего изменения записи.

### VisitStatus

Статус отношения семьи к объекту. В MVP у объекта один текущий статус.

Допустимые значения:

- `not_visited` - не посещен;
- `planned` - запланирован;
- `visited` - посещен;
- `favorite` - любимый.

Статус `любимый` означает, что объект уже особенно отмечен семьей. Если понадобится разделить «посещен» и «любимый» как независимые признаки, это будет отдельная миграция после MVP.

### OperationalStatus

Эксплуатационный статус описывает, работает сам объект или нет. Он не связан с семейным посещением: объект может быть любимым и временно закрытым, либо не посещенным и действующим.

Допустимые значения:

- `active` - работает;
- `active_seasonal` - работает сезонно или по сезонному графику;
- `temporarily_closed_planned` - временно закрыт по плану;
- `temporarily_closed_unplanned` - временно закрыт внепланово;
- `closed` - закрыт;
- `historical` - исторический объект без регулярной эксплуатации;
- `unknown` - статус неизвестен.

Поля источника (`status_checked_at`, `status_source_url`, `status_note`) хранят дату и основание проверки, если они есть в seed или импортируемом каталоге.

### Visit

Факт посещения объекта. У одного объекта может быть несколько посещений.

Поля MVP:

- `id` - стабильный текстовый идентификатор посещения;
- `transport_object_id` - ссылка на `TransportObject`;
- `visited_on` - дата посещения;
- `title` - короткое название поездки или события;
- `notes` - заметки о поездке;
- `impression_rating` - семейная оценка впечатлений от 1 до 5, если указана;
- `created_at` - дата создания записи;
- `updated_at` - дата последнего изменения записи.

### MediaAsset

Фото, видео или другой файл, связанный с объектом или посещением.

Поля MVP:

- `id` - стабильный текстовый идентификатор материала;
- `transport_object_id` - ссылка на `TransportObject`, если материал относится к объекту в целом;
- `visit_id` - ссылка на `Visit`, если материал относится к конкретному посещению;
- `kind` - тип материала: `photo`, `video`, `document`;
- `local_path` - путь к локальному файлу внутри пользовательского хранилища;
- `caption` - подпись;
- `taken_on` - дата съемки или создания, если известна;
- `latitude` - широта точки съемки или опорной точки материала, если известна;
- `longitude` - долгота точки съемки или опорной точки материала, если известна;
- `coordinate_source` - источник координат: `exif`, `manual`, `unknown`;
- `geo_note` - человекочитаемая русская заметка о координатах, точности или логике привязки;
- `station_id` - ссылка на `ObjectStation`, если материал снят на станции;
- `route_direction_id` - ссылка на `RouteDirection`, если материал относится к поездке в конкретном направлении;
- `route_segment_id` - ссылка на `RouteSegment`, если материал относится к отрезку между двумя станциями;
- `created_at` - дата добавления записи.

Хотя MVP хранит данные локально, путь не должен зависеть от абсолютного пути на машине разработчика. Для синхронизации позже понадобится переносимый относительный путь или отдельный слой файлового хранилища.

Координаты материала не заменяют координаты `TransportObject`: объект остается одной точкой на общей карте, а `MediaAsset.latitude`/`MediaAsset.longitude` помогают детальному экрану показать место съемки фотографии, точку начала видео или примерное положение материала на маршруте. Если координаты взяты из EXIF, `coordinate_source = 'exif'`; если поставлены пользователем или seed-данными, `coordinate_source = 'manual'`; если координаты отсутствуют или их источник неизвестен, используется `unknown`. Поле `geo_note` хранит пояснение для семьи и будущего UI, например «координата вручную поставлена примерно в середине маршрута».

### Будущая детальная схема объекта

Общая карта и детальная схема объекта должны оставаться разными уровнями модели:

- объектная карта показывает каждый `TransportObject` одной точкой с координатами `latitude` и `longitude`; на этом уровне не нужны станции, платформы, приводные колеса, опоры и внутренний маршрут;
- детальная схема объекта открывается после выбора объекта и описывает устройство конкретной линии: начало и конец, станции или платформы, инженерные точки, маршрут и направление видео.

MVP не требует полноценного 3D, прогулки по сцене, поездки от первого лица или инженерного симулятора. Текущая общая карта остается 2D-картой объектов, а детальная схема выбранного объекта остается 2D-схемой с точками, подписями и маршрутными связями. Будущая 3D/инженерная сцена должна строиться поверх той же доменной модели, но не должна менять смысл `TransportObject` в MVP.

Сущности детальной схемы добавлены как foundation для #20/#21 и не требуют полноценного UI карты:

- `ObjectStation` - станция, платформа, нижняя или верхняя точка линии внутри выбранного `TransportObject`;
- `RouteDirection` - направление поездки по объекту: начальная станция, конечная станция, русская подпись направления и порядок показа;
- `RouteSegment` - отрезок маршрута между станциями, платформами или инженерными точками; хранит порядок линии внутри направления и русскую подпись вверх/вниз или откуда/куда;
- `EngineeringPoint` - техническая точка объекта: приводное колесо, натяжное колесо, опора, поворотный узел или другая инженерная деталь.

### Будущая инженерная и игровая сцена

`TransportObject` остается корневой записью реального объекта: у него есть название, тип транспорта, координата для общей карты, статус и семейные материалы. Будущая 3D/инженерная сцена является представлением выбранного `TransportObject`, а не отдельным объектом каталога. Все режимы сцены должны ссылаться на тот же `transport_object_id`, чтобы прогулка, поездка, наблюдатель и инженерный режим показывали одну и ту же линию, станции, маршрут, медиа и семейную историю.

Для будущей сцены достаточно договориться о словаре инженерных деталей. Полноценные 3D-модели, физика каната, photogrammetry, Three.js, Godot 3D scenes и импорт CAD не входят в MVP и должны появляться только в отдельных задачах V3. В документации и данных можно описывать детали как 2D-точки, отрезки и подписи.

Инженерная модель выбранного объекта состоит из следующих деталей:

- двигатель - источник движения линии; обычно находится на приводной станции и может быть связан с `ObjectStation`;
- редуктор - узел между двигателем и приводным колесом; нужен для объяснения передачи усилия без моделирования реальной кинематики;
- приводное колесо - колесо, которое тянет канат и задает движение системы;
- натяжное колесо - колесо или узел натяжения каната, который поддерживает рабочее натяжение линии;
- канат - несущий или тяговый элемент маршрута; в 2D-схеме представлен линией `RouteSegment`, а не физической 3D-симуляцией;
- кабина - пассажирская кабина, вагон, кресло или платформа, которая движется по маршруту;
- опора - промежуточная башня, пилон или стойка, через которую проходит канат или направляющий путь;
- станция - нижняя, верхняя, промежуточная или сервисная станция, уже представленная сущностью `ObjectStation`.

`EngineeringPoint` может описывать двигатель, редуктор, приводное колесо, натяжное колесо, опору, поворотный узел и другую техническую точку. Кабина и канат в MVP не требуют отдельных таблиц: кабину достаточно показывать как будущий визуальный слой на `RouteDirection`, а канат - как подпись и геометрию `RouteSegment`. Если V3 потребует отдельные сущности для кабины, каната или состава, это будет новая миграция и отдельный contract test.

Режимы будущей сцены фиксируются как продуктовые цели V3:

- прогулка - свободный осмотр станций, опор и подписанных инженерных деталей без обязательной поездки;
- поездка - движение по `RouteDirection` от одной станции к другой с привязкой к сегментам, медиа и подписи направления;
- наблюдатель - внешний обзор объекта, маршрута, опор и движения кабины без управления;
- инженерный режим - объяснение работы двигателя, редуктора, приводного колеса, натяжного колеса, каната, кабины, опор и станций.

Эти режимы не меняют MVP-обязательства: карта и детальная схема остаются 2D, а любые 3D-представления должны быть добавлены позже как отдельный слой поверх существующих данных.

`RouteDirection` хранит `from_station_id`, `to_station_id`, `title` и `direction_label`. `title` может быть короткой подписью вида «Киенбергпарк -> Сады мира», а `direction_label` - человекочитаемым направлением «от Киенбергпарка к Садам мира». `RouteSegment` задает `from_station_id`, `to_station_id`, `segment_order`, `title` и `direction_label`, например «вверх к Волькенхайну» или «вниз к Садам мира».

`MediaAsset` может относиться не только к объекту или посещению в целом, но и к станции, отрезку или направлению: например, видео подъема от нижней станции к верхней, фото приводного колеса или ролик вдоль конкретного `RouteSegment`. Связи `station_id`, `route_direction_id` и `route_segment_id` нужны будущему UI, чтобы показать станции и направление видео без EXIF-импорта.

### Ticket

Билет, проездной документ или связанный с поездкой чек. Билет выделен отдельно от `MediaAsset`, потому что у него есть собственные поля и он участвует в семейном журнале.

Поля MVP:

- `id` - стабильный текстовый идентификатор билета;
- `transport_object_id` - ссылка на `TransportObject`;
- `visit_id` - ссылка на `Visit`, если билет относится к конкретной поездке;
- `media_asset_id` - ссылка на изображение или документ билета, если файл уже добавлен;
- `title` - название билета;
- `issued_on` - дата билета, если известна;
- `price_amount` - сумма, если известна;
- `price_currency` - валюта в формате ISO 4217, если известна;
- `notes` - заметки;
- `created_at` - дата добавления записи.

## Справочник типов транспорта

Типы транспорта сведены из спецификации в явный справочник. В базе они хранятся в таблице `transport_types`.

| id | Название | Группа |
| --- | --- | --- |
| `cable_gondola` | гондольная канатная дорога | канатные дороги |
| `cable_aerial_tram` | маятниковая канатная дорога | канатные дороги |
| `cable_urban` | городская канатная дорога | канатные дороги |
| `cable_tourist` | туристическая канатная дорога | канатные дороги |
| `funicular_classic` | классический фуникулер | фуникулеры |
| `funicular_water` | водяной фуникулер | фуникулеры |
| `funicular_modern` | современный фуникулер | фуникулеры |
| `rail_cog` | зубчатая железная дорога | железные дороги |
| `rail_mountain` | горная железная дорога | железные дороги |
| `rail_suspended` | подвесная железная дорога | железные дороги |
| `elevator_vertical` | вертикальный лифт | лифты |
| `elevator_inclined` | наклонный лифт | лифты |
| `elevator_panoramic` | панорамный лифт | лифты |
| `suspended_train` | подвесной поезд | подвесной транспорт |
| `monorail` | монорельс | подвесной транспорт |
| `suspended_ferry` | подвесной паром | подвесной транспорт |
| `escalator_unusual` | необычный эскалатор | другие инженерные сооружения |
| `special_transport_system` | транспортная система особой конструкции | другие инженерные сооружения |
| `unique_engineering_object` | уникальный инженерный объект | другие инженерные сооружения |

## SQLite-схема MVP

Схема рассчитана на локальную базу SQLite. Все идентификаторы текстовые, чтобы импорт из JSON и будущая синхронизация могли сохранять стабильные ключи.

Каноническая SQL-версия базовой схемы хранится в `scripts/storage/migrations/001_initial_schema.sql`. Эксплуатационные поля добавлены обратимо-совместимой миграцией `scripts/storage/migrations/002_operational_status.sql`, чтобы уже созданные локальные базы получили новые колонки без пересоздания. Геометки медиа, станции и направления маршрута добавлены миграцией `scripts/storage/migrations/003_media_geo_routes.sql`. Демо-инициализация объектов хранится отдельно в `scripts/storage/seeds/demo_objects.sql`, чтобы повторный запуск мог добавлять отсутствующие демо-записи без перезаписи пользовательских статусов посещения.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE visit_statuses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL UNIQUE
);

CREATE TABLE transport_types (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    group_title TEXT NOT NULL,
    sort_order INTEGER NOT NULL UNIQUE
);

CREATE TABLE transport_objects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    transport_type_id TEXT NOT NULL REFERENCES transport_types(id),
    visit_status_id TEXT NOT NULL REFERENCES visit_statuses(id),
    country TEXT NOT NULL,
    region TEXT,
    city TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    opened_year INTEGER,
    operator TEXT,
    manufacturer TEXT,
    operational_status TEXT NOT NULL DEFAULT 'unknown' CHECK (operational_status IN (
        'active',
        'active_seasonal',
        'temporarily_closed_planned',
        'temporarily_closed_unplanned',
        'closed',
        'historical',
        'unknown'
    )),
    status_checked_at TEXT NOT NULL DEFAULT '',
    status_source_url TEXT NOT NULL DEFAULT '',
    status_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE visits (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    visited_on TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    impression_rating INTEGER CHECK (impression_rating IS NULL OR impression_rating BETWEEN 1 AND 5),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE media_assets (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT REFERENCES transport_objects(id) ON DELETE CASCADE,
    visit_id TEXT REFERENCES visits(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('photo', 'video', 'document')),
    local_path TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '',
    taken_on TEXT,
    latitude REAL,
    longitude REAL,
    coordinate_source TEXT NOT NULL DEFAULT 'unknown' CHECK (coordinate_source IN ('exif', 'manual', 'unknown')),
    geo_note TEXT NOT NULL DEFAULT '',
    station_id TEXT REFERENCES object_stations(id) ON DELETE SET NULL,
    route_direction_id TEXT REFERENCES route_directions(id) ON DELETE SET NULL,
    route_segment_id TEXT REFERENCES route_segments(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    CHECK (transport_object_id IS NOT NULL OR visit_id IS NOT NULL)
);

CREATE TABLE object_stations (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    station_role TEXT NOT NULL DEFAULT 'unknown',
    latitude REAL,
    longitude REAL,
    sort_order INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (transport_object_id, sort_order)
);

CREATE TABLE route_directions (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    from_station_id TEXT NOT NULL REFERENCES object_stations(id) ON DELETE CASCADE,
    to_station_id TEXT NOT NULL REFERENCES object_stations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    direction_label TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (from_station_id <> to_station_id),
    UNIQUE (transport_object_id, sort_order)
);

CREATE TABLE route_segments (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    route_direction_id TEXT NOT NULL REFERENCES route_directions(id) ON DELETE CASCADE,
    from_station_id TEXT NOT NULL REFERENCES object_stations(id) ON DELETE CASCADE,
    to_station_id TEXT NOT NULL REFERENCES object_stations(id) ON DELETE CASCADE,
    segment_order INTEGER NOT NULL,
    title TEXT NOT NULL,
    direction_label TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (from_station_id <> to_station_id),
    UNIQUE (route_direction_id, segment_order)
);

CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    visit_id TEXT REFERENCES visits(id) ON DELETE SET NULL,
    media_asset_id TEXT REFERENCES media_assets(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    issued_on TEXT,
    price_amount REAL,
    price_currency TEXT CHECK (price_currency IS NULL OR length(price_currency) = 3),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX idx_transport_objects_type ON transport_objects(transport_type_id);
CREATE INDEX idx_transport_objects_status ON transport_objects(visit_status_id);
CREATE INDEX idx_transport_objects_operational_status ON transport_objects(operational_status);
CREATE INDEX idx_visits_object ON visits(transport_object_id);
CREATE INDEX idx_media_assets_object ON media_assets(transport_object_id);
CREATE INDEX idx_media_assets_visit ON media_assets(visit_id);
CREATE INDEX idx_media_assets_station ON media_assets(station_id);
CREATE INDEX idx_media_assets_route_direction ON media_assets(route_direction_id);
CREATE INDEX idx_media_assets_route_segment ON media_assets(route_segment_id);
CREATE INDEX idx_object_stations_object ON object_stations(transport_object_id);
CREATE INDEX idx_route_directions_object ON route_directions(transport_object_id);
CREATE INDEX idx_route_segments_direction ON route_segments(route_direction_id);
CREATE INDEX idx_tickets_object ON tickets(transport_object_id);
CREATE INDEX idx_tickets_visit ON tickets(visit_id);
```

Начальные значения `visit_statuses`:

```sql
INSERT INTO visit_statuses (id, title, sort_order) VALUES
('not_visited', 'не посещен', 10),
('planned', 'запланирован', 20),
('visited', 'посещен', 30),
('favorite', 'любимый', 40);
```

Начальные значения `transport_types` должны соответствовать справочнику типов транспорта выше.

## Демо-данные

Текущие демо-данные в GDScript считаются временным представлением модели. SQL seed в `scripts/storage/seeds/demo_objects.sql` мапит те же записи на `TransportObject`, использует один `transport_type_id` из справочника, один `visit_status_id` из `VisitStatus` и независимые поля `operational_status`, `status_checked_at`, `status_source_url`, `status_note` для эксплуатационного статуса.

Если у демо-объекта есть отметка посещения, она должна превращаться в статус `visited` или `not_visited`. Фото, видео и билеты в будущих демо-наборах должны добавляться как `MediaAsset` и `Ticket`, а не как произвольные поля внутри объекта.

Для `berlin-gaerten-der-welt` seed фиксирует один детальный маршрут:

- 3 станции `ObjectStation`: `berlin-gaerten-der-welt-station-kienbergpark`, `berlin-gaerten-der-welt-station-wolkenhain`, `berlin-gaerten-der-welt-station-gaerten-der-welt`;
- 2 направления `RouteDirection`: `berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten` с подписью «от Киенбергпарка к Садам мира» и `berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark` с подписью «от Садов мира к Киенбергпарку»;
- 4 отрезка `RouteSegment`, по два на каждое направление, с русскими подписями «вверх к Волькенхайну», «вниз к Садам мира», «вверх к Волькенхайну», «вниз к Киенбергпарку»;
- демо-видео `berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten` как `MediaAsset.kind = 'video'` с `coordinate_source = 'manual'`, русской `geo_note`, координатой и ссылкой на направление.

Идентификаторы станций, направлений, сегментов и демо-видео стабильные ASCII. Русские названия и подписи хранятся только в полях display text: `title`, `direction_label`, `note`, `caption`, `geo_note`.

Эти записи намеренно остаются небольшим демонстрационным набором, а не полной картой линии. Их задача - закрепить форму данных для будущего интерфейса: показать ребенку и родителю, где находятся станции, в какую сторону снято видео, какой участок маршрута виден на материале и почему координата считается точной или примерной. Импорт EXIF, редактирование маршрута и полноценная интерактивная схема будут отдельными продуктовыми задачами.

## Runtime SQLite в Godot

Godot 4.6 не содержит встроенного SQLite API, поэтому runtime-хранилище подключено через GDExtension [2shady4u/godot-sqlite](https://github.com/2shady4u/godot-sqlite) версии `v4.7`. В репозитории зафиксирован минимальный vendored набор для Linux x86_64:

- `addons/godot-sqlite/gdsqlite.gdextension`;
- `addons/godot-sqlite/bin/libgdsqlite.linux.template_debug.x86_64.so`;
- `addons/godot-sqlite/bin/libgdsqlite.linux.template_release.x86_64.so`;
- `addons/godot-sqlite/licenses/LICENSE.md`.

Полный релиз addon'а содержит сборки для других платформ, но они не добавлены в проект, чтобы не раздувать репозиторий неиспользуемыми бинарными файлами. Источник и версия зафиксированы здесь, а лицензия MIT лежит рядом с vendored-файлами.

`scripts/storage/sqlite_storage_adapter.gd` открывает `user://mir-trossov.sqlite3`, применяет SQL migrations из `scripts/storage/migrations`, выполняет seed из `scripts/storage/seeds/demo_objects.sql` и предоставляет CRUD для `transport_objects`, `visits` и `media_assets`. Главное окно использует этот адаптер для загрузки объектов, сохранения статуса посещения и регистрации MVP-записей фото как `MediaAsset` с переносимым относительным `local_path`; повторный запуск видит сохраненный `visit_status_id` и список фото.

На платформах без загруженного класса `SQLite`, включая текущий Web export, `is_runtime_available()` возвращает `false`. Приложение в этом случае использует встроенный `DemoCatalog` и не обещает сохранение пользовательских изменений между запусками.
