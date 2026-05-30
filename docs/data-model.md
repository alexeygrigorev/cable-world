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
- `created_at` - дата добавления записи.

Хотя MVP хранит данные локально, путь не должен зависеть от абсолютного пути на машине разработчика. Для синхронизации позже понадобится переносимый относительный путь или отдельный слой файлового хранилища.

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
    created_at TEXT NOT NULL,
    CHECK (transport_object_id IS NOT NULL OR visit_id IS NOT NULL)
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
CREATE INDEX idx_visits_object ON visits(transport_object_id);
CREATE INDEX idx_media_assets_object ON media_assets(transport_object_id);
CREATE INDEX idx_media_assets_visit ON media_assets(visit_id);
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

Текущие демо-данные в GDScript считаются временным представлением модели и в этой задаче не меняются. При следующем переносе в JSON или SQLite каждая демо-запись должна мапиться на `TransportObject`, использовать один `transport_type_id` из справочника и один `visit_status_id` из `VisitStatus`.

Если у демо-объекта есть отметка посещения, она должна превращаться в статус `visited` или `not_visited`. Фото, видео и билеты в будущих демо-наборах должны добавляться как `MediaAsset` и `Ticket`, а не как произвольные поля внутри объекта.
