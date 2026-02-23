#!/usr/bin/env python3
"""Unit tests for the analytics schema and weight advisor."""

import sys
import os
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.analytics.weight_advisor import generate_report, MIN_CLIPS_FOR_REPORT, _pearson


def _create_test_db(path: str, n_clips: int = 0):
    """Create a test database with the analytics schema and optional data."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE clips (
            id TEXT PRIMARY KEY,
            variant_type TEXT,
            hook_timestamp REAL,
            recut_applied BOOLEAN,
            first_2s_interrupt BOOLEAN,
            controversy_score REAL,
            novelty_score REAL,
            hashtag_mode_used TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE clip_performance (
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
        )
    """)

    for i in range(n_clips):
        clip_id = f"clip_{i}"
        conn.execute(
            "INSERT INTO clips VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (clip_id, "Curiosity", 1.5, False, True, 5.0 + (i % 5), 4.0, "append"),
        )
        conn.execute(
            "INSERT INTO clip_performance (clip_id, platform, views, impressions, "
            "avg_watch_pct, comments, shares, saves) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (clip_id, "tiktok", 1000 + i * 100, 5000, 35.0 + i, 10 + i, 5, 3),
        )

    conn.commit()
    conn.close()


class TestAnalyticsSchema(unittest.TestCase):
    """Verify schema creation and data write."""

    def test_schema_creates_tables(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            _create_test_db(db_path)
            conn = sqlite3.connect(db_path)
            tables = [
                r[0] for r in
                conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            ]
            self.assertIn("clips", tables)
            self.assertIn("clip_performance", tables)
            conn.close()
        finally:
            os.unlink(db_path)

    def test_clip_performance_write(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            _create_test_db(db_path, n_clips=5)
            conn = sqlite3.connect(db_path)
            count = conn.execute("SELECT COUNT(*) FROM clip_performance").fetchone()[0]
            self.assertEqual(count, 5)
            conn.close()
        finally:
            os.unlink(db_path)


class TestWeightAdvisor(unittest.TestCase):
    """Test report generation."""

    def test_not_enough_data(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            _create_test_db(db_path, n_clips=10)
            report = generate_report(db_path)
            self.assertIn("Not enough data", report)
        finally:
            os.unlink(db_path)

    def test_report_with_sufficient_data(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            _create_test_db(db_path, n_clips=120)
            report = generate_report(db_path)
            self.assertIn("Weight Advisor Report", report)
            self.assertIn("tiktok", report)
            self.assertIn("advisory only", report)
            self.assertNotIn("Not enough data", report)
        finally:
            os.unlink(db_path)


class TestPearson(unittest.TestCase):
    """Test correlation helper."""

    def test_perfect_positive(self):
        r = _pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        self.assertAlmostEqual(r, 1.0, places=3)

    def test_perfect_negative(self):
        r = _pearson([1, 2, 3, 4, 5], [10, 8, 6, 4, 2])
        self.assertAlmostEqual(r, -1.0, places=3)

    def test_no_data(self):
        r = _pearson([], [])
        self.assertEqual(r, 0.0)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
