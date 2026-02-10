# Selector Intelligence System

## Overview

The Selector Intelligence System is a self-healing browser automation framework that addresses the core problem of selector fragility in web automation. It automatically adapts to UI changes across Instagram, TikTok, and YouTube by maintaining multiple selector strategies and learning from success/failure history.

## Key Features

### 1. Multi-Strategy Selectors
Each UI element has multiple fallback selectors ranked by stability:
1. **data-testid** (Priority 1) - Most stable, official test attributes
2. **aria-label** (Priority 2) - Semantic, accessibility-focused
3. **role** (Priority 3) - Semantic HTML roles
4. **text** (Priority 4) - Visible text (brittle but functional)
5. **xpath** (Priority 5) - Last resort

### 2. Adaptive Ranking
- Selectors are automatically reranked based on success/failure history
- Confidence scores adjust with each use (success +0.1, failure -0.2)
- Recent successes are weighted higher (recency factor)
- System learns which selectors work best over time

### 3. Network Idle Detection
- `wait_for_load_state("networkidle")` added after critical actions
- Prevents premature navigation and context closure
- Graceful fallback to timeout if networkidle hangs

### 4. Platform-Specific Optimizations

**Instagram:**
- Handles "Reel first" flow variant
- 5 retry attempts with 9-second delays for React animations
- State detection for button enabled/disabled status

**TikTok:**
- Extended 360-second timeout for video processing
- Caption input availability detection
- `no_wait_after=True` on Post button to prevent context closure

**YouTube:**
- Fixed brittle description field with 5 fallback selectors
- Multiple strategies for title and description inputs

## Usage

### Basic Usage (Automatic)

The selector intelligence system is automatically used by all uploader functions:

```python
from uploaders.brave_instagram import upload_to_instagram_browser

result = upload_to_instagram_browser(
    video_path="/path/to/video.mp4",
    title="My Video",
    description="Description",
    tags="#viral #trending"
)
```

The system will automatically:
1. Try selectors in priority order
2. Record success/failure for each attempt
3. Adapt ranking for future uploads

### Advanced Usage (Custom Selectors)

To add custom selectors for a platform:

```python
from uploaders.selectors import get_instagram_selectors, SelectorGroup

# Get existing manager
manager = get_instagram_selectors()

# Add new selector to existing group
caption_group = manager.get_group("caption_input")
caption_group.add_selector(
    value='div[data-new-attribute="caption"]',
    priority=1,  # High priority for official attributes
    description="New caption selector"
)
```

### Monitoring Selector Performance

```python
from uploaders.selectors import get_instagram_selectors

manager = get_instagram_selectors()
caption_group = manager.get_group("caption_input")

# Check selector rankings
for selector in caption_group.get_ranked_selectors():
    print(f"Selector: {selector.value}")
    print(f"  Priority: {selector.priority}")
    print(f"  Confidence: {selector.confidence}")
    print(f"  Success: {selector.success_count}")
    print(f"  Failures: {selector.failure_count}")
    print(f"  Score: {selector.get_score()}")
```

## Updating Selectors

### When to Update

Update selectors when:
1. Platform UI changes (new design, A/B test)
2. Automation consistently fails on specific step
3. Platform adds new official test attributes

### How to Update

#### Method 1: Using Playwright Codegen (Recommended)

```bash
# Record new selectors by interacting with the platform
npx playwright codegen https://www.instagram.com

# Copy the generated selectors
# Add them to uploaders/selectors.py
```

#### Method 2: Manual Inspection

1. Open browser dev tools on the platform
2. Inspect the element you want to target
3. Look for stable attributes in this priority order:
   - `data-testid`, `data-e2e` (priority 1)
   - `aria-label` (priority 2)
   - `role` (priority 3)
   - Visible text (priority 4)
4. Add to `uploaders/selectors.py`

#### Method 3: Code Update

Edit `uploaders/selectors.py` and add to the appropriate selector group:

```python
def get_instagram_selectors() -> SelectorManager:
    manager = SelectorManager("instagram")
    
    # Example: Update caption input selectors
    caption_group = SelectorGroup(
        name="caption_input",
        description="Caption/description text input"
    )
    
    # Add new selector
    caption_group.add_selector(
        value='div[data-instagram-caption="true"]',
        priority=1,
        description="New official caption attribute"
    )
    
    # Keep existing selectors as fallbacks
    caption_group.add_selector(
        value='div[role="textbox"][aria-label*="caption"]',
        priority=2,
        description="ARIA label fallback"
    )
    
    manager.add_group(caption_group)
    return manager
```

## Testing

### Running Tests

```bash
# Test selector intelligence system
python test_selector_intelligence.py

# Test stable selectors (backwards compatibility)
python test_stable_selectors.py

# All tests should pass
```

### Adding New Tests

When adding new selectors, add corresponding tests:

```python
def test_new_selector(self):
    """Test new selector is present and prioritized correctly."""
    manager = get_instagram_selectors()
    caption_group = manager.get_group("caption_input")
    
    # Check selector exists
    selectors = [s.value for s in caption_group.selectors]
    self.assertIn('div[data-instagram-caption="true"]', selectors)
    
    # Check priority is correct
    for selector in caption_group.selectors:
        if 'data-instagram-caption' in selector.value:
            self.assertEqual(selector.priority, 1)
```

## Troubleshooting

### Selector Not Found Error

**Symptom:** "Caption input not found with any selector"

**Solution:**
1. Check if platform UI changed
2. Use Playwright codegen to record new selectors
3. Add new selectors to `uploaders/selectors.py`
4. Keep old selectors as fallbacks

### Automation Hanging

**Symptom:** Upload process hangs at specific step

**Solution:**
1. Check network idle timeout isn't too long
2. Verify state detection selectors are correct
3. Add debug logging to identify which selector is failing

### Wrong Element Selected

**Symptom:** Text entered into wrong field

**Solution:**
1. Make selectors more specific (add more attributes)
2. Increase priority of correct selector
3. Decrease confidence of wrong selector

## Best Practices

1. **Always keep multiple selectors** - Don't rely on a single selector
2. **Prioritize official attributes** - `data-testid` > `aria-label` > others
3. **Test after updates** - Run test suite after adding new selectors
4. **Monitor confidence scores** - Low confidence indicates problem selector
5. **Update regularly** - Check selectors monthly or after platform updates
6. **Document selector source** - Add description explaining where selector came from

## Architecture

```
uploaders/
  ├── selectors.py          # Selector intelligence system
  │   ├── Selector          # Individual selector with metadata
  │   ├── SelectorGroup     # Group of selectors for one UI element
  │   ├── SelectorManager   # Platform-level selector management
  │   └── try_selectors_with_page()  # Helper to try selectors
  │
  ├── brave_instagram.py    # Instagram uploader (uses selectors.py)
  ├── brave_tiktok.py       # TikTok uploader (uses selectors.py)
  └── brave_youtube.py      # YouTube uploader (uses selectors.py)
```

## Performance Impact

- **Minimal overhead**: Selector lookup is O(n) where n = number of selectors per group (typically 3-5)
- **Adaptive improvement**: System gets faster over time as confidence scores converge
- **Failure resilience**: Multiple fallbacks prevent single point of failure

## Future Enhancements

Potential improvements for the selector system:

1. **Persistent storage** - Save confidence scores between runs
2. **Platform version detection** - Adapt based on platform version
3. **Visual detection** - Use screenshots to verify correct element selected
4. **Auto-discovery** - Automatically find new selectors when old ones fail
5. **Selector health dashboard** - Web UI to monitor selector performance

## Support

For issues or questions:
1. Check existing test files for examples
2. Review selector configurations in `uploaders/selectors.py`
3. Enable debug logging: `logging.getLogger("uploaders.selectors").setLevel(logging.DEBUG)`
4. Open an issue with selector failure details
