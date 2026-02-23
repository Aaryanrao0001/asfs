-- Migration 0005: Audio-First Segment Scoring schema extension
-- Non-destructive: additive tables only. Safe for production.

-- Micro-segment scoring results (one row per scored micro-segment per source).
CREATE TABLE IF NOT EXISTS audio_micro_segments (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    segment_id INTEGER NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    duration_sec REAL NOT NULL,
    text TEXT,
    hook_score REAL,
    retention_score REAL,
    emotion_score REAL,
    relatability_score REAL,
    completion_score REAL,
    platform_fit_score REAL,
    controversy_score REAL,
    novelty_score REAL,
    composite_score REAL,
    mean_rms REAL,
    silence_ratio REAL,
    speech_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Macro candidate clips produced by the cluster merger.
CREATE TABLE IF NOT EXISTS audio_macro_candidates (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    macro_id INTEGER NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    duration_sec REAL NOT NULL,
    text TEXT,
    best_micro_score REAL,
    avg_micro_score REAL,
    macro_text_score REAL,
    blended_score REAL,
    platform TEXT,
    output_path TEXT,
    exported INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
