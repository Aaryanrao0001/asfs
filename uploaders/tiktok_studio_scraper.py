"""
TikTok Studio dashboard scraper for extracting per-post view metrics.

Navigates to https://www.tiktok.com/tiktokstudio/content and parses the
post table DOM to retrieve view counts. These counts drive adaptive upload
scheduling in UploadScheduler.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# CSS selectors for TikTok Studio content dashboard
_POST_TABLE_SELECTOR = '[data-tt="components_PostTable_Absolute"]'
_VIEW_COUNT_SELECTOR = (
    '[data-tt="components_RowLayout_FlexRow_6"] '
    '[data-tt="components_ItemRow_FlexCenter"]'
)

TIKTOK_STUDIO_URL = "https://www.tiktok.com/tiktokstudio/content"


async def get_latest_video_views(page) -> Optional[int]:
    """
    Scrape the view count of the most recent post from TikTok Studio.

    Navigates to the TikTok Studio content dashboard, waits for the post
    table to render, then extracts the view count displayed in the first
    (most recent) row.

    Args:
        page: An async Playwright ``Page`` instance that is already
              authenticated to TikTok.

    Returns:
        Integer view count for the latest post, or ``None`` if the count
        could not be determined.
    """
    try:
        await page.goto(TIKTOK_STUDIO_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector(_POST_TABLE_SELECTOR, timeout=15000)
    except Exception as exc:
        logger.warning("TikTok Studio dashboard did not load: %s", exc)
        return None

    rows = await page.query_selector_all(_POST_TABLE_SELECTOR)
    if not rows:
        logger.warning("No post rows found on TikTok Studio dashboard")
        return None

    latest_row = rows[0]

    # Attempt once; retry once with a short wait on failure as specified
    view_element = await latest_row.query_selector(_VIEW_COUNT_SELECTOR)
    if view_element is None:
        logger.debug("View element not found on first attempt – retrying after short wait")
        await page.wait_for_timeout(500)
        view_element = await latest_row.query_selector(_VIEW_COUNT_SELECTOR)

    if view_element is None:
        logger.warning("View element still missing after retry")
        return None

    try:
        views_text = await view_element.inner_text()
        views_text = views_text.strip()

        # "--" means TikTok has not yet computed the metric
        if views_text == "--":
            return 0

        return int(views_text.replace(",", ""))
    except (ValueError, TypeError) as exc:
        logger.warning("Could not parse view count '%s': %s", views_text, exc)
        return None
