PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    species TEXT NOT NULL,
    author TEXT NOT NULL,
    region TEXT NOT NULL,
    board_type TEXT NOT NULL DEFAULT '자유 소통',
    location_visibility TEXT NOT NULL DEFAULT '비공개'
        CHECK (location_visibility IN ('비공개','대략 공개','정확 공개')),
    is_public INTEGER NOT NULL DEFAULT 1 CHECK (is_public IN (0,1)),
    photo_public_consent INTEGER NOT NULL DEFAULT 0 CHECK (photo_public_consent IN (0,1)),
    operator_photo_consent INTEGER NOT NULL DEFAULT 0 CHECK (operator_photo_consent IN (0,1)),
    created_at TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0 CHECK (likes >= 0),
    photo_blob BLOB
);

CREATE TABLE IF NOT EXISTS aquarium (
    user_id TEXT NOT NULL,
    species TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    observation_id INTEGER REFERENCES observations(id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, species)
);

CREATE TABLE IF NOT EXISTS aquarium_visibility (
    user_id TEXT NOT NULL,
    species TEXT NOT NULL,
    is_public INTEGER NOT NULL DEFAULT 0 CHECK (is_public IN (0,1)),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, species)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observation_likes (
    observation_id INTEGER NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    PRIMARY KEY (observation_id, user_id)
);

CREATE TABLE IF NOT EXISTS consent_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    observation_id INTEGER REFERENCES observations(id) ON DELETE SET NULL,
    consent_type TEXT NOT NULL CHECK (consent_type IN ('public_post','public_photo','operator_photo','ai_transfer')),
    enabled INTEGER NOT NULL CHECK (enabled IN (0,1)),
    notice_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('오류 제보','기능 건의')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '접수',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    elapsed_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS game_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    game TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS point_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    points INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (user_id, source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_observations_public_created ON observations(is_public, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_observations_species ON observations(species);
CREATE INDEX IF NOT EXISTS idx_comments_observation ON comments(observation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_logs_created ON ai_logs(created_at);
