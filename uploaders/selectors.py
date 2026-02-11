"""
Selector Intelligence System for Browser Automation.

Provides:
1. Multi-strategy selector storage with priority ranking
2. Selector confidence scoring based on success/failure history
3. Auto-switching to working selectors (self-healing)
4. Centralized selector configuration for all platforms

Priority Order:
1. data-testid (most stable)
2. aria-label (semantic)
3. role (semantic)
4. visible text (brittle but functional)
5. XPath (last resort)
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Selector:
    """
    Represents a single selector with metadata.
    """
    value: str
    priority: int  # 1=highest (data-testid), 5=lowest (xpath)
    confidence: float = 1.0  # 0.0 to 1.0, decreases on failure, increases on success
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    description: str = ""
    
    def record_success(self):
        """Record successful use of this selector."""
        self.success_count += 1
        self.last_used = datetime.now()
        # Increase confidence, but cap at 1.0
        self.confidence = min(1.0, self.confidence + 0.1)
        
    def record_failure(self):
        """Record failed use of this selector."""
        self.failure_count += 1
        # Decrease confidence, but keep above 0.0
        self.confidence = max(0.0, self.confidence - 0.2)
    
    def get_score(self) -> float:
        """
        Calculate overall score for selector ranking.
        
        Score = confidence * (1 / priority) * recency_factor
        Higher score = better selector to try first
        """
        # Priority weight (lower priority number = higher weight)
        priority_weight = 1.0 / self.priority
        
        # Recency factor (more recently successful = higher weight)
        recency_weight = 1.0
        if self.last_used and self.success_count > 0:
            hours_since_success = (datetime.now() - self.last_used).total_seconds() / 3600
            # Decay over 24 hours
            recency_weight = max(0.5, 1.0 - (hours_since_success / 24))
        
        return self.confidence * priority_weight * recency_weight


@dataclass
class SelectorGroup:
    """
    Represents a group of selectors for a single UI element.
    """
    name: str
    description: str
    selectors: List[Selector] = field(default_factory=list)
    
    def add_selector(
        self, 
        value: str, 
        priority: int, 
        description: str = ""
    ):
        """Add a selector to the group."""
        selector = Selector(
            value=value,
            priority=priority,
            description=description
        )
        self.selectors.append(selector)
        
    def get_ranked_selectors(self) -> List[Selector]:
        """
        Get selectors ranked by score (best first).
        
        Returns:
            List of selectors sorted by score (highest to lowest)
        """
        return sorted(self.selectors, key=lambda s: s.get_score(), reverse=True)
    
    def get_best_selector(self) -> Optional[Selector]:
        """Get the highest-ranked selector."""
        ranked = self.get_ranked_selectors()
        return ranked[0] if ranked else None
    
    def record_success(self, selector_value: str):
        """Record success for a specific selector."""
        for selector in self.selectors:
            if selector.value == selector_value:
                selector.record_success()
                logger.info(
                    f"Selector success: {self.name} - {selector_value[:50]} "
                    f"(confidence: {selector.confidence:.2f})"
                )
                break
                
    def record_failure(self, selector_value: str):
        """Record failure for a specific selector."""
        for selector in self.selectors:
            if selector.value == selector_value:
                selector.record_failure()
                logger.warning(
                    f"Selector failure: {self.name} - {selector_value[:50]} "
                    f"(confidence: {selector.confidence:.2f})"
                )
                break


class SelectorManager:
    """
    Manages all selectors for a platform (Instagram, TikTok, YouTube).
    """
    
    def __init__(self, platform: str):
        self.platform = platform
        self.groups: Dict[str, SelectorGroup] = {}
        
    def add_group(self, group: SelectorGroup):
        """Add a selector group."""
        self.groups[group.name] = group
        
    def get_group(self, name: str) -> Optional[SelectorGroup]:
        """Get a selector group by name."""
        return self.groups.get(name)
    
    def get_selectors(self, group_name: str) -> List[str]:
        """
        Get ranked selector values for a group.
        
        Returns:
            List of selector values (strings) ranked by score
        """
        group = self.get_group(group_name)
        if not group:
            logger.error(f"Selector group not found: {group_name}")
            return []
        
        return [s.value for s in group.get_ranked_selectors()]


# ============================================================================
# INSTAGRAM SELECTORS
# ============================================================================

def get_instagram_selectors() -> SelectorManager:
    """
    Get Instagram selector configuration.
    
    Returns:
        SelectorManager with all Instagram selectors configured
    """
    manager = SelectorManager("instagram")
    
    # Create button
    create_group = SelectorGroup(
        name="create_button",
        description="Button to open Create menu"
    )
    create_group.add_selector(
        value='svg[aria-label="New post"]',
        priority=2,  # ARIA label
        description="Primary stable selector"
    )
    create_group.add_selector(
        value='svg[aria-label="Create"]',
        priority=2,
        description="Alternative ARIA label"
    )
    create_group.add_selector(
        value='a[href="#"]:has(svg)',
        priority=4,
        description="Structural fallback"
    )
    manager.add_group(create_group)
    
    # Post option in menu
    post_option_group = SelectorGroup(
        name="post_option",
        description="Post/Reel option in Create menu"
    )
    # Priority 1: SVG aria-label (most stable)
    post_option_group.add_selector(
        value='a:has(svg[aria-label="Post"])',
        priority=1,
        description="Link with Post SVG aria-label (most stable)"
    )
    post_option_group.add_selector(
        value='a[role="link"]:has(svg[aria-label="Post"])',
        priority=1,
        description="Link role with Post SVG aria-label"
    )
    # Priority 2: Text-based with link role
    post_option_group.add_selector(
        value='a:has-text("Post")',
        priority=2,
        description="Link with Post text"
    )
    post_option_group.add_selector(
        value='a[role="link"]:has-text("Post")',
        priority=2,
        description="Link role with Post text (hybrid)"
    )
    # Priority 3: Legacy button-based selectors (fallback)
    post_option_group.add_selector(
        value='div[role="button"]:has-text("Post")',
        priority=3,
        description="Classic Post option (legacy)"
    )
    post_option_group.add_selector(
        value='div[role="button"]:has-text("Create post")',
        priority=3,
        description="Newer variant (legacy)"
    )
    post_option_group.add_selector(
        value='div[role="button"]:has-text("Post to feed")',
        priority=3,
        description="Alternative variant (legacy)"
    )
    post_option_group.add_selector(
        value='div[role="button"]:has-text("Reel")',
        priority=3,
        description="Reel option (also allows file upload)"
    )
    manager.add_group(post_option_group)
    
    # Caption input
    caption_group = SelectorGroup(
        name="caption_input",
        description="Caption/description text input"
    )
    caption_group.add_selector(
        value='div[role="textbox"][aria-label*="caption"]',
        priority=2,
        description="Primary caption input"
    )
    caption_group.add_selector(
        value='textarea[aria-label*="caption"]',
        priority=3,
        description="Textarea variant"
    )
    caption_group.add_selector(
        value='div[role="textbox"][aria-label*="Write a caption"]',
        priority=2,
        description="English-specific variant"
    )
    caption_group.add_selector(
        value='div[contenteditable="true"][aria-label*="caption"]',
        priority=3,
        description="Contenteditable variant"
    )
    manager.add_group(caption_group)
    
    # File input
    file_input_group = SelectorGroup(
        name="file_input",
        description="File upload input"
    )
    file_input_group.add_selector(
        value='input[type="file"][accept*="video"]',
        priority=3,
        description="Video file input"
    )
    file_input_group.add_selector(
        value='input[type="file"][accept*="image"]',
        priority=3,
        description="Image file input (also accepts video)"
    )
    file_input_group.add_selector(
        value='input[type="file"]',
        priority=4,
        description="Generic file input"
    )
    manager.add_group(file_input_group)
    
    # Next button
    next_button_group = SelectorGroup(
        name="next_button",
        description="Next button in editing flow"
    )
    next_button_group.add_selector(
        value='div[role="button"]:has-text("Next")',
        priority=3,
        description="Primary Next button"
    )
    next_button_group.add_selector(
        value='button:has-text("Next")',
        priority=3,
        description="Button element variant"
    )
    manager.add_group(next_button_group)
    
    # Share button
    share_button_group = SelectorGroup(
        name="share_button",
        description="Share/Publish button"
    )
    share_button_group.add_selector(
        value='div[role="button"]:has-text("Share")',
        priority=3,
        description="Primary Share button"
    )
    share_button_group.add_selector(
        value='button:has-text("Share")',
        priority=3,
        description="Button element variant"
    )
    share_button_group.add_selector(
        value='div[role="button"]:has-text("Post")',
        priority=3,
        description="Alternative text"
    )
    manager.add_group(share_button_group)
    
    return manager


# ============================================================================
# TIKTOK SELECTORS
# ============================================================================

def get_tiktok_selectors() -> SelectorManager:
    """
    Get TikTok selector configuration.
    
    Returns:
        SelectorManager with all TikTok selectors configured
    """
    manager = SelectorManager("tiktok")
    
    # File input
    file_input_group = SelectorGroup(
        name="file_input",
        description="File upload input"
    )
    file_input_group.add_selector(
        value='[data-e2e="upload-input"]',
        priority=1,  # data-testid/e2e attribute is most stable
        description="Official test attribute"
    )
    file_input_group.add_selector(
        value='input[type="file"]',
        priority=3,
        description="Generic file input"
    )
    manager.add_group(file_input_group)
    
    # Caption input
    caption_group = SelectorGroup(
        name="caption_input",
        description="Caption/description input"
    )
    caption_group.add_selector(
        value='[data-e2e="caption-input"]',
        priority=1,
        description="Official test attribute"
    )
    caption_group.add_selector(
        value='[data-testid="video-caption"] div[contenteditable="true"]',
        priority=1,
        description="Test ID with contenteditable"
    )
    # Add new selectors for current TikTok UI
    caption_group.add_selector(
        value='div[contenteditable="plaintext-only"]',
        priority=2,
        description="Contenteditable plaintext-only mode (new TikTok UI pattern)"
    )
    caption_group.add_selector(
        value='div[contenteditable="true"][aria-label*="caption" i]',
        priority=2,
        description="ARIA label with contenteditable"
    )
    caption_group.add_selector(
        value='div[contenteditable="true"][data-text]',
        priority=2,
        description="Contenteditable with data-text (common React pattern for placeholder text)"
    )
    caption_group.add_selector(
        value='[role="textbox"][contenteditable]',
        priority=2,
        description="Role textbox with contenteditable"
    )
    caption_group.add_selector(
        value='div.caption-editor[contenteditable="true"]',
        priority=3,
        description="Class-based selector"
    )
    caption_group.add_selector(
        value='div[contenteditable="true"][placeholder*="caption" i]',
        priority=3,
        description="Placeholder-based"
    )
    caption_group.add_selector(
        value='div[contenteditable][spellcheck]',
        priority=3,
        description="Contenteditable with spellcheck (common in text editors)"
    )
    caption_group.add_selector(
        value='div[contenteditable="true"]',
        priority=4,
        description="Generic contenteditable (last resort - may match other inputs, relies on context)"
    )
    manager.add_group(caption_group)
    
    # Post button
    post_button_group = SelectorGroup(
        name="post_button",
        description="Post/Submit button"
    )
    post_button_group.add_selector(
        value='button[data-e2e="post_video_button"]',
        priority=1,
        description="Official post video button (most stable)"
    )
    post_button_group.add_selector(
        value='[data-e2e="post-button"]',
        priority=1,
        description="Official test attribute (alternative)"
    )
    post_button_group.add_selector(
        value='button[data-e2e="post-button"]',
        priority=1,
        description="Button with post test attribute"
    )
    post_button_group.add_selector(
        value='button:has-text("Post"):not(:has-text("Discard"))',
        priority=3,
        description="Button element with text (avoid class names)"
    )
    post_button_group.add_selector(
        value='div[role="button"]:has-text("Post"):not(:has-text("Discard"))',
        priority=4,
        description="Role-based with text (excluding Discard) - less stable"
    )
    manager.add_group(post_button_group)
    
    return manager


# ============================================================================
# YOUTUBE SELECTORS
# ============================================================================

def get_youtube_selectors() -> SelectorManager:
    """
    Get YouTube selector configuration.
    
    Returns:
        SelectorManager with all YouTube selectors configured
    """
    manager = SelectorManager("youtube")
    
    # Create button
    create_button_group = SelectorGroup(
        name="create_button",
        description="Create/Upload button"
    )
    create_button_group.add_selector(
        value='button[aria-label*="Create"]',
        priority=2,
        description="ARIA label"
    )
    create_button_group.add_selector(
        value='ytcp-button#create-icon',
        priority=3,
        description="ID-based selector"
    )
    manager.add_group(create_button_group)
    
    # Upload videos menu item
    upload_menu_group = SelectorGroup(
        name="upload_menu",
        description="Upload videos menu option"
    )
    upload_menu_group.add_selector(
        value='tp-yt-paper-item:has-text("Upload videos")',
        priority=3,
        description="Component with text"
    )
    upload_menu_group.add_selector(
        value='text="Upload videos"',
        priority=4,
        description="Text-only fallback"
    )
    manager.add_group(upload_menu_group)
    
    # File input
    file_input_group = SelectorGroup(
        name="file_input",
        description="File upload input"
    )
    file_input_group.add_selector(
        value='input[type="file"][name="Filedata"]',
        priority=3,
        description="Named file input"
    )
    file_input_group.add_selector(
        value='input[type="file"]',
        priority=4,
        description="Generic file input"
    )
    manager.add_group(file_input_group)
    
    # Title input
    title_input_group = SelectorGroup(
        name="title_input",
        description="Video title input"
    )
    title_input_group.add_selector(
        value='div[aria-label*="title" i][contenteditable="true"]',
        priority=2,
        description="ARIA label with contenteditable"
    )
    title_input_group.add_selector(
        value='ytcp-social-suggestions-textbox[label*="Title" i] input',
        priority=3,
        description="Component-based selector"
    )
    title_input_group.add_selector(
        value='#textbox[aria-label*="title" i]',
        priority=3,
        description="ID with ARIA label"
    )
    manager.add_group(title_input_group)
    
    # Description input (BRITTLE - needs improvement per problem statement)
    description_input_group = SelectorGroup(
        name="description_input",
        description="Video description input"
    )
    description_input_group.add_selector(
        value='div[aria-label*="description" i][contenteditable="true"]',
        priority=2,
        description="ARIA label with contenteditable"
    )
    description_input_group.add_selector(
        value='ytcp-social-suggestions-textbox[label*="Description" i] textarea',
        priority=3,
        description="Component-based textarea"
    )
    description_input_group.add_selector(
        value='#description-textarea',
        priority=3,
        description="ID-based selector"
    )
    description_input_group.add_selector(
        value='textarea[aria-label*="description" i]',
        priority=2,
        description="Textarea with ARIA label"
    )
    description_input_group.add_selector(
        value='div[id*="description"][contenteditable="true"]',
        priority=4,
        description="Structural fallback"
    )
    manager.add_group(description_input_group)
    
    # Next button
    next_button_group = SelectorGroup(
        name="next_button",
        description="Next button in upload flow"
    )
    next_button_group.add_selector(
        value='ytcp-button#next-button',
        priority=3,
        description="ID-based selector"
    )
    next_button_group.add_selector(
        value='button[aria-label*="Next"]',
        priority=2,
        description="ARIA label"
    )
    manager.add_group(next_button_group)
    
    # Public visibility radio
    public_radio_group = SelectorGroup(
        name="public_radio",
        description="Public visibility option"
    )
    public_radio_group.add_selector(
        value='tp-yt-paper-radio-button[name="PUBLIC"]',
        priority=3,
        description="Named radio button"
    )
    public_radio_group.add_selector(
        value='[aria-label*="Public" i][role="radio"]',
        priority=2,
        description="ARIA label with role"
    )
    manager.add_group(public_radio_group)
    
    # Publish/Done button
    publish_button_group = SelectorGroup(
        name="publish_button",
        description="Publish/Done button"
    )
    publish_button_group.add_selector(
        value='ytcp-button#done-button',
        priority=3,
        description="ID-based selector"
    )
    publish_button_group.add_selector(
        value='button[aria-label*="Publish"]',
        priority=2,
        description="ARIA label"
    )
    manager.add_group(publish_button_group)
    
    # Audience selection (Not for kids)
    audience_group = SelectorGroup(
        name="audience_not_for_kids",
        description="Not made for kids radio button"
    )
    audience_group.add_selector(
        value='tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]',
        priority=3,
        description="Named radio button"
    )
    audience_group.add_selector(
        value='[aria-label*="not made for kids" i][role="radio"]',
        priority=2,
        description="ARIA label with role"
    )
    manager.add_group(audience_group)
    
    return manager


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def try_selectors_with_page(
    page,
    selector_group: SelectorGroup,
    timeout: int = 10000,
    state: str = "visible"
) -> Tuple[Optional[str], Optional[object]]:
    """
    Try selectors from a group until one succeeds.
    
    Args:
        page: Playwright Page object
        selector_group: SelectorGroup to try
        timeout: Timeout in milliseconds for each selector
        state: State to wait for ("visible", "attached", "enabled")
        
    Returns:
        Tuple of (selector_value, element) or (None, None) if all fail
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    
    ranked_selectors = selector_group.get_ranked_selectors()
    
    for selector in ranked_selectors:
        try:
            logger.debug(
                f"Trying selector: {selector_group.name} - {selector.value[:60]}... "
                f"(score: {selector.get_score():.2f})"
            )
            
            element = page.wait_for_selector(
                selector.value,
                timeout=timeout,
                state=state
            )
            
            if element:
                logger.info(
                    f"Selector succeeded: {selector_group.name} - {selector.value[:60]}"
                )
                selector_group.record_success(selector.value)
                return selector.value, element
                
        except PlaywrightTimeoutError:
            logger.debug(f"Selector timeout: {selector.value[:60]}")
            selector_group.record_failure(selector.value)
            continue
        except Exception as e:
            logger.debug(f"Selector error: {selector.value[:60]} - {e}")
            selector_group.record_failure(selector.value)
            continue
    
    logger.error(f"All selectors failed for: {selector_group.name}")
    return None, None
