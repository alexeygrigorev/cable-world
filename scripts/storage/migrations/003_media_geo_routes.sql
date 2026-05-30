PRAGMA foreign_keys = ON;

CREATE TABLE object_stations (
    id TEXT PRIMARY KEY,
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    station_role TEXT NOT NULL DEFAULT 'unknown' CHECK (station_role IN (
        'lower',
        'middle',
        'upper',
        'terminal',
        'unknown'
    )),
    latitude REAL,
    longitude REAL,
    sort_order INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
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
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
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
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (from_station_id <> to_station_id),
    UNIQUE (route_direction_id, segment_order)
);

ALTER TABLE media_assets
ADD COLUMN latitude REAL;

ALTER TABLE media_assets
ADD COLUMN longitude REAL;

ALTER TABLE media_assets
ADD COLUMN coordinate_source TEXT NOT NULL DEFAULT 'unknown'
CHECK (coordinate_source IN ('exif', 'manual', 'unknown'));

ALTER TABLE media_assets
ADD COLUMN geo_note TEXT NOT NULL DEFAULT '';

ALTER TABLE media_assets
ADD COLUMN station_id TEXT REFERENCES object_stations(id) ON DELETE SET NULL;

ALTER TABLE media_assets
ADD COLUMN route_direction_id TEXT REFERENCES route_directions(id) ON DELETE SET NULL;

ALTER TABLE media_assets
ADD COLUMN route_segment_id TEXT REFERENCES route_segments(id) ON DELETE SET NULL;

CREATE INDEX idx_object_stations_object ON object_stations(transport_object_id);
CREATE INDEX idx_route_directions_object ON route_directions(transport_object_id);
CREATE INDEX idx_route_segments_direction ON route_segments(route_direction_id);
CREATE INDEX idx_media_assets_station ON media_assets(station_id);
CREATE INDEX idx_media_assets_route_direction ON media_assets(route_direction_id);
CREATE INDEX idx_media_assets_route_segment ON media_assets(route_segment_id);

INSERT INTO schema_migrations (version) VALUES ('003_media_geo_routes');
