PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

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

INSERT INTO visit_statuses (id, title, sort_order) VALUES
('not_visited', 'не посещен', 10),
('planned', 'запланирован', 20),
('visited', 'посещен', 30),
('favorite', 'любимый', 40);

INSERT INTO transport_types (id, title, group_title, sort_order) VALUES
('cable_gondola', 'гондольная канатная дорога', 'канатные дороги', 10),
('cable_aerial_tram', 'маятниковая канатная дорога', 'канатные дороги', 20),
('cable_urban', 'городская канатная дорога', 'канатные дороги', 30),
('cable_tourist', 'туристическая канатная дорога', 'канатные дороги', 40),
('funicular_classic', 'классический фуникулер', 'фуникулеры', 50),
('funicular_water', 'водяной фуникулер', 'фуникулеры', 60),
('funicular_modern', 'современный фуникулер', 'фуникулеры', 70),
('rail_cog', 'зубчатая железная дорога', 'железные дороги', 80),
('rail_mountain', 'горная железная дорога', 'железные дороги', 90),
('rail_suspended', 'подвесная железная дорога', 'железные дороги', 100),
('elevator_vertical', 'вертикальный лифт', 'лифты', 110),
('elevator_inclined', 'наклонный лифт', 'лифты', 120),
('elevator_panoramic', 'панорамный лифт', 'лифты', 130),
('suspended_train', 'подвесной поезд', 'подвесной транспорт', 140),
('monorail', 'монорельс', 'подвесной транспорт', 150),
('suspended_ferry', 'подвесной паром', 'подвесной транспорт', 160),
('escalator_unusual', 'необычный эскалатор', 'другие инженерные сооружения', 170),
('special_transport_system', 'транспортная система особой конструкции', 'другие инженерные сооружения', 180),
('unique_engineering_object', 'уникальный инженерный объект', 'другие инженерные сооружения', 190);

INSERT INTO schema_migrations (version) VALUES ('001_initial_schema');
