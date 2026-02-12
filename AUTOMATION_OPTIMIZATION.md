# Instagram and TikTok Automation Optimization

This document explains the optimization applied to Instagram and TikTok browser automation to ensure efficient, reliable uploads.

## Overview

Browser automation recordings (e.g., from Playwright Codegen) often contain redundant steps that should be optimized for production use. This document describes the issues found in naive recordings and how our implementation avoids them.

## Instagram Automation Optimization

### ✅ Implemented Features

#### 1. Share Button Handling
**Status**: ✅ Fully Implemented

The Instagram upload flow properly handles the Share button with:
- **Selector**: `div[role="button"]:has-text("Share")` (line 308)
- **State Checking**: Uses `_wait_for_button_enabled()` to ensure button is ready
- **Enabled State Wait**: Critical for React-heavy UI that disables buttons during processing

**Implementation**:
```python
# Click "Share" button with state checking
logger.info("Clicking Share button")
if not _wait_for_button_enabled(page, "Share", timeout=10000):
    raise Exception("Share button failed - cannot complete upload")
```

#### 2. Complete Upload Flow
The optimized flow includes:
1. Navigate to Instagram
2. Click "Create" button (`svg[aria-label="New post"]`)
3. Select "Post" option from menu (handles A/B test variants)
4. Upload file via file input
5. Click "Next" through editing steps (with enabled state checking)
6. Fill caption
7. Click "Share" button (with enabled state checking)

### 🚫 Avoided Anti-Patterns

The implementation avoids these common recording issues:
- ❌ Using hashed CSS class names (e.g., `.x1i10hfl`) - uses semantic selectors instead
- ❌ Multiple redundant clicks on same elements - single click per action
- ❌ Character-by-character typing without delays - uses human-like typing with 50-150ms delays
- ❌ Waiting for `networkidle` - uses semantic UI selector waits instead
- ❌ Missing state checks on buttons - waits for "enabled" state before clicking

## TikTok Automation Optimization

### ✅ Optimized Implementation

The TikTok uploader has been optimized to ~200 lines with clean, efficient operations:

#### 1. Efficient Text Input
**Issue in Naive Recordings**: 
- Individual `keyDown`/`keyUp` events for each character
- Example: Typing "donbang" as 12 separate keystroke events
- Example: Typing "donboon" as 15 separate keystroke events

**Our Solution**:
```python
# Efficient batch typing with human-like delays
element.type(char, delay=random.uniform(50, 150))
```

#### 2. No Redundant Clicks
**Issues Avoided**:
- ❌ Duplicate clicks on "Show more" button
- ❌ Multiple individual clicks on caption editor
- ❌ Duplicate double-click on caption editor
- ❌ Unnecessary double-click selections

**Our Solution**:
- Single click per UI element
- Direct interaction with caption input using prioritized selectors

#### 3. Stable Selectors
**Issues Avoided**:
- ❌ Hashed CSS class names
- ❌ Fragile XPath selectors
- ❌ Generic selectors without context

**Our Solution**:
```python
caption_selectors = [
    '[data-e2e="caption-input"]',  # TikTok's official test attribute
    '[data-testid="video-caption"] div[contenteditable="true"]',
    'div.caption-editor[contenteditable="true"]',
    'div[contenteditable="true"][aria-label*="caption" i]',
    'div[contenteditable="true"][placeholder*="caption" i]'
]
```

### 📊 Optimization Results

**Naive Recording** (from Playwright Codegen):
- ~70+ steps
- Individual keystrokes for text input
- Redundant UI interactions
- Multiple selector attempts

**Optimized Implementation**:
- ~20-25 core steps
- Batch text input operations
- Single interaction per UI element
- Prioritized selector fallbacks

### 🎯 Core Optimization Principles

1. **Navigate to page** - Single goto with proper wait
2. **Select video/image file** - Direct file input interaction
3. **Handle UI dialogs** - Single click per modal/button
4. **Fill caption/description** - Single type operation with delays
5. **Submit post** - Single click with proper state checking

## Testing

Both implementations have comprehensive test coverage:

### Instagram Tests (`test_stable_selectors.py`)
- ✅ Create button uses ARIA label
- ✅ No hashed class selectors
- ✅ Next button uses role selector
- ✅ Caption uses role textbox
- ✅ Share button uses role selector
- ✅ File upload uses input type

### TikTok Tests (`test_stable_selectors.py`)
- ✅ Uses data-e2e attributes
- ✅ Caption uses contenteditable
- ✅ Post button has role fallback
- ✅ File upload uses input type
- ✅ No hashed class selectors

## Maintenance Guidelines

When updating automation code:

1. **Use Semantic Selectors**: ARIA labels, roles, data-e2e attributes
2. **Wait for State**: Check for "enabled" state before clicking buttons
3. **Batch Operations**: Combine text input, avoid character-by-character typing
4. **Human-Like Delays**: Add random delays (50-150ms) for bot detection avoidance
5. **Error Handling**: Proper error messages when selectors fail
6. **Logging**: Debug-level logs for each major step

## References

- Instagram uploader: `uploaders/brave_instagram.py`
- TikTok uploader: `uploaders/brave_tiktok.py`
- Selector tests: `test_stable_selectors.py`
- Post button fix tests: `test_instagram_post_button_fix.py`
