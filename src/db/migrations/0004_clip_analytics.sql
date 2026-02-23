-- Migration 0004: Clip analytics schema extension
-- Non-destructive: additive columns only. Safe for production.

-- New columns on clips table
ALTER TABLE clips ADD COLUMN variant_type TEXT;
ALTER TABLE clips ADD COLUMN hook_timestamp REAL;
-- NULL = not yet analysed; 1 = true; 0 = false (three-state flag)
ALTER TABLE clips ADD COLUMN recut_applied INTEGER DEFAULT NULL;
ALTER TABLE clips ADD COLUMN first_2s_interrupt INTEGER DEFAULT NULL;
ALTER TABLE clips ADD COLUMN controversy_score REAL;
ALTER TABLE clips ADD COLUMN novelty_score REAL;
ALTER TABLE clips ADD COLUMN hashtag_mode_used TEXT;

-- New performance tracking table
CREATE TABLE IF NOT EXISTS clip_performance (
    id INTEGER PRIMARY KEY,
    clip_id TEXT REFERENCES clips(id),
    platform TEXT,
    views INTEGER,
    impressions INTEGER,
    avg_watch_pct REAL,
    comments INTEGER,
    shares INTEGER,
    saves INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
