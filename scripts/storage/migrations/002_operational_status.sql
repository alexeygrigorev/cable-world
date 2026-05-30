PRAGMA foreign_keys = ON;

ALTER TABLE transport_objects
ADD COLUMN operational_status TEXT NOT NULL DEFAULT 'unknown'
CHECK (operational_status IN (
    'active',
    'active_seasonal',
    'temporarily_closed_planned',
    'temporarily_closed_unplanned',
    'closed',
    'historical',
    'unknown'
));

ALTER TABLE transport_objects
ADD COLUMN status_checked_at TEXT NOT NULL DEFAULT '';

ALTER TABLE transport_objects
ADD COLUMN status_source_url TEXT NOT NULL DEFAULT '';

ALTER TABLE transport_objects
ADD COLUMN status_note TEXT NOT NULL DEFAULT '';

CREATE INDEX idx_transport_objects_operational_status ON transport_objects(operational_status);

INSERT INTO schema_migrations (version) VALUES ('002_operational_status');
