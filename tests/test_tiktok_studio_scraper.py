#!/usr/bin/env python3
"""
Unit tests for uploaders.tiktok_studio_scraper and the adaptive scheduling
logic added to scheduler.auto_scheduler.UploadScheduler.
"""

import asyncio
import sys
import os
import importlib
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules under test directly (bypassing package __init__ files
# that pull in optional heavy dependencies like PySide6 / Playwright browsers).
_repo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _repo)

# Stub the playwright sync_api so brave_tiktok (imported via __init__) doesn't
# break the import of tiktok_studio_scraper which only uses async playwright.
import types
_pw_stub = types.ModuleType("playwright")
_pw_stub.sync_api = types.ModuleType("playwright.sync_api")
_pw_stub.sync_api.Page = object
sys.modules.setdefault("playwright", _pw_stub)
sys.modules.setdefault("playwright.sync_api", _pw_stub.sync_api)

# Stub PySide6 so bulk_scheduler doesn't break the scheduler import.
for _mod in [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtWidgets",
    "PySide6.QtGui",
]:
    sys.modules.setdefault(_mod, types.ModuleType(_mod))

# Stub database so VideoRegistry import doesn't fail.
_db_stub = types.ModuleType("database")
_db_stub.VideoRegistry = MagicMock
sys.modules.setdefault("database", _db_stub)

import importlib.util

def _load_module(rel_path, module_name):
    spec = importlib.util.spec_from_file_location(
        module_name,
        os.path.join(_repo, rel_path),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_scraper = _load_module("uploaders/tiktok_studio_scraper.py", "uploaders.tiktok_studio_scraper")
get_latest_video_views = _scraper.get_latest_video_views

_auto = _load_module("scheduler/auto_scheduler.py", "scheduler.auto_scheduler")
UploadScheduler = _auto.UploadScheduler
_HIGH_VIEWS_THRESHOLD = _auto._HIGH_VIEWS_THRESHOLD
_LOW_VIEWS_THRESHOLD = _auto._LOW_VIEWS_THRESHOLD
_HIGH_VIEWS_GAP_HOURS = _auto._HIGH_VIEWS_GAP_HOURS
_MID_VIEWS_GAP_HOURS = _auto._MID_VIEWS_GAP_HOURS
_LOW_VIEWS_GAP_HOURS = _auto._LOW_VIEWS_GAP_HOURS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.run(coro)


def _make_page(inner_text="679", has_view_element=True, has_rows=True):
    """
    Build a minimal mock Playwright Page that simulates the TikTok Studio
    content dashboard.
    """
    page = AsyncMock()

    view_element = AsyncMock()
    view_element.inner_text = AsyncMock(return_value=inner_text)

    row = AsyncMock()
    row.query_selector = AsyncMock(
        return_value=view_element if has_view_element else None
    )

    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[row] if has_rows else [])
    return page


# ---------------------------------------------------------------------------
# Tests for get_latest_video_views
# ---------------------------------------------------------------------------

class TestGetLatestVideoViews(unittest.TestCase):

    def test_returns_integer_view_count(self):
        page = _make_page(inner_text="679")
        result = _run(get_latest_video_views(page))
        self.assertEqual(result, 679)

    def test_handles_comma_separated_numbers(self):
        page = _make_page(inner_text="1,234")
        result = _run(get_latest_video_views(page))
        self.assertEqual(result, 1234)

    def test_handles_dash_placeholder_as_zero(self):
        page = _make_page(inner_text="--")
        result = _run(get_latest_video_views(page))
        self.assertEqual(result, 0)

    def test_returns_none_when_no_rows(self):
        page = _make_page(has_rows=False)
        result = _run(get_latest_video_views(page))
        self.assertIsNone(result)

    def test_returns_none_when_view_element_missing(self):
        page = _make_page(has_view_element=False)
        result = _run(get_latest_video_views(page))
        self.assertIsNone(result)

    def test_returns_none_on_navigation_error(self):
        page = AsyncMock()
        page.goto = AsyncMock(side_effect=Exception("network error"))
        page.wait_for_load_state = AsyncMock()
        page.wait_for_selector = AsyncMock()
        result = _run(get_latest_video_views(page))
        self.assertIsNone(result)

    def test_returns_none_on_unparseable_text(self):
        page = _make_page(inner_text="N/A")
        result = _run(get_latest_video_views(page))
        self.assertIsNone(result)

    def test_handles_whitespace_around_number(self):
        page = _make_page(inner_text="  500  ")
        result = _run(get_latest_video_views(page))
        self.assertEqual(result, 500)


# ---------------------------------------------------------------------------
# Tests for UploadScheduler adaptive scheduling
# ---------------------------------------------------------------------------

class TestAdaptiveScheduling(unittest.TestCase):

    def _make_scheduler(self):
        """Return a scheduler with VideoRegistry mocked out."""
        scheduler = UploadScheduler()
        return scheduler

    def test_schedule_next_upload_sets_gap(self):
        scheduler = self._make_scheduler()
        scheduler.schedule_next_upload(delay_hours=6)
        self.assertEqual(scheduler.upload_gap_seconds, 6 * 3600)

    def test_apply_adaptive_schedule_high_views(self):
        scheduler = self._make_scheduler()
        page = _make_page(inner_text=str(_HIGH_VIEWS_THRESHOLD))
        scheduler.set_page(page)

        # Patch the function reference used inside _apply_adaptive_schedule
        original = _scraper.get_latest_video_views
        _scraper.get_latest_video_views = AsyncMock(return_value=_HIGH_VIEWS_THRESHOLD)
        try:
            scheduler._apply_adaptive_schedule()
        finally:
            _scraper.get_latest_video_views = original

        self.assertEqual(scheduler.upload_gap_seconds, _HIGH_VIEWS_GAP_HOURS * 3600)

    def test_apply_adaptive_schedule_low_views(self):
        scheduler = self._make_scheduler()
        scheduler.set_page(AsyncMock())

        original = _scraper.get_latest_video_views
        _scraper.get_latest_video_views = AsyncMock(return_value=_LOW_VIEWS_THRESHOLD)
        try:
            scheduler._apply_adaptive_schedule()
        finally:
            _scraper.get_latest_video_views = original

        self.assertEqual(scheduler.upload_gap_seconds, _LOW_VIEWS_GAP_HOURS * 3600)

    def test_apply_adaptive_schedule_mid_views(self):
        scheduler = self._make_scheduler()
        scheduler.set_page(AsyncMock())
        mid_views = (_HIGH_VIEWS_THRESHOLD + _LOW_VIEWS_THRESHOLD) // 2

        original = _scraper.get_latest_video_views
        _scraper.get_latest_video_views = AsyncMock(return_value=mid_views)
        try:
            scheduler._apply_adaptive_schedule()
        finally:
            _scraper.get_latest_video_views = original

        self.assertEqual(scheduler.upload_gap_seconds, _MID_VIEWS_GAP_HOURS * 3600)

    def test_apply_adaptive_schedule_none_views_keeps_gap(self):
        """If scraping returns None the current gap must be preserved."""
        scheduler = self._make_scheduler()
        scheduler.set_page(AsyncMock())
        original_gap = scheduler.upload_gap_seconds

        original = _scraper.get_latest_video_views
        _scraper.get_latest_video_views = AsyncMock(return_value=None)
        try:
            scheduler._apply_adaptive_schedule()
        finally:
            _scraper.get_latest_video_views = original

        self.assertEqual(scheduler.upload_gap_seconds, original_gap)

    def test_apply_adaptive_schedule_no_page_keeps_gap(self):
        """Without a page set, the gap must remain unchanged."""
        scheduler = self._make_scheduler()
        original_gap = scheduler.upload_gap_seconds
        scheduler._apply_adaptive_schedule()
        self.assertEqual(scheduler.upload_gap_seconds, original_gap)

    def test_apply_adaptive_schedule_exception_keeps_gap(self):
        """If the scraper raises, the scheduler must not crash and keeps its gap."""
        scheduler = self._make_scheduler()
        scheduler.set_page(AsyncMock())
        original_gap = scheduler.upload_gap_seconds

        original = _scraper.get_latest_video_views
        _scraper.get_latest_video_views = AsyncMock(side_effect=RuntimeError("boom"))
        try:
            scheduler._apply_adaptive_schedule()
        finally:
            _scraper.get_latest_video_views = original

        self.assertEqual(scheduler.upload_gap_seconds, original_gap)

    def test_set_page_stores_page(self):
        scheduler = self._make_scheduler()
        mock_page = AsyncMock()
        scheduler.set_page(mock_page)
        self.assertIs(scheduler._page, mock_page)


if __name__ == "__main__":
    success = unittest.main(verbosity=2, exit=False).result.wasSuccessful()
    sys.exit(0 if success else 1)
