-- Schema for the DevScape Lineage Archive (SQLite)

-- Table to record the lineage of contributions and actions
CREATE TABLE IF NOT EXISTS lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id TEXT NOT NULL,
    action_type TEXT NOT NULL, -- e.g., 'glyph_created', 'trait_evolved', 'quest_completed'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT -- JSON string for additional context
);

-- Table to log significant events within the DevScape world
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL, -- e.g., 'quest_trigger', 'planetary_feedback_log'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    related_entity_id TEXT, -- e.g., quest_id, planetary_id
    details TEXT -- JSON string for event-specific data
);

-- Table to track the evolution history of traits
CREATE TABLE IF NOT EXISTS traits_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trait_id TEXT NOT NULL,
    contributor_id TEXT, -- Optional: who evolved the trait
    old_level INTEGER,
    new_level INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT -- JSON string for evolution context
);
