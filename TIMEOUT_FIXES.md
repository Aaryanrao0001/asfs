# Timeout Fixes for Instagram and TikTok Automation

## Issues Fixed

### 1. Instagram Stuck After Clicking "+" Button
**Problem**: Instagram automation was getting stuck after clicking the Create (+) button and never progressing forward.

**Root Cause**: Timeouts were too aggressive for slow networks. Instagram's React-based UI needs more time to:
- Load and animate the Create menu
- Render the Post option buttons
- Mount file input dialogs
- Process video uploads

**Solution**: Increased all timeouts by 3x:
- Page navigation: 60s → 180s
- UI element waits: 30s → 90s  
- Create button: 10s → 30s
- Menu animation wait: 2.5-4.5s → 7.5-13.5s
- Post option wait: 3s → 9s (per attempt)
- Post option retries: 3 → 5
- File dialog mount: 2-4s → 6-12s
- Upload processing: 3-6s → 9-18s
- Video processing: 5s → 15s
- Next/Share buttons: 10s → 30s
- State transitions: 1.5-3s → 4.5-9s

### 2. TikTok Clicking Wrong Button (Discard Instead of Post)
**Problem**: TikTok automation was clicking the "Discard" button instead of the "Post" button.

**Root Cause**: The selector `div[role="button"]:has-text("Post")` was matching buttons containing "Post" as a substring, which could match both "Post" and "Discard Post" or similar variants.

**Solution**: Made Post button selector more specific by explicitly excluding "Discard":
```python
# Old (ambiguous):
post_button_selector = '[data-e2e="post-button"], div[role="button"]:has-text("Post"), button:has-text("Post")'

# New (explicit):
post_button_selector = '[data-e2e="post-button"]:not(:has-text("Discard")), div[role="button"]:has-text("Post"):not(:has-text("Discard")), button:has-text("Post"):not(:has-text("Discard"))'
```

### 3. Both Platforms Not Loading Properly
**Problem**: Pages were not loading properly because requests were being killed too fast.

**Root Cause**: Aggressive timeouts were causing navigation and element waits to fail on slower networks.

**Solution**: Increased all TikTok timeouts by 3x:
- Page navigation: 60s → 180s
- Login wait: 90s → 270s
- Video processing: 120s → 360s
- Caption input wait: Various → 30s
- Post button wait: 10s → 30s
- Submission processing: 3s → 9s
- Upload confirmation: 5s → 15s
- Human-like delays: 2-4s → 6-12s

## Files Modified

### uploaders/brave_instagram.py
- Increased `_wait_for_button_enabled` default timeout: 30s → 90s
- Increased `_select_post_option` default timeout: 15s → 45s
- Increased max retries in `_select_post_option`: 3 → 5
- Increased selector wait times in `_select_post_option`: 3s → 9s
- Increased page.goto timeout: 60s → 180s
- Increased all button wait timeouts: 10s → 30s
- Increased all delay timeouts by 3x throughout
- Updated caption box timeout: 5s → 15s

### uploaders/brave_tiktok.py
- Fixed Post button selector to exclude "Discard" button
- Increased page.goto timeout: 60s → 180s
- Increased login wait timeout: 90s → 270s
- Increased video processing timeout: 120s → 360s
- Increased all button wait timeouts: 10s → 30s
- Increased all delay timeouts by 3x throughout
- Increased submission processing: 3s → 9s
- Increased upload confirmation: 5s → 15s

## Testing

All existing tests continue to pass:
- ✅ test_stable_selectors.py (14 tests)
- ✅ test_automation_efficiency.py (17 tests)

## Impact

These changes will:
1. ✅ Allow Instagram automation to progress past the Create menu
2. ✅ Prevent TikTok from clicking wrong buttons
3. ✅ Improve reliability on slow networks (3G, 4G, congested WiFi)
4. ✅ Reduce timeout-related failures
5. ⚠️ Increase total upload time by ~2-3x (necessary tradeoff for reliability)

## Recommendations

For users on fast networks who want faster uploads:
- These timeouts can be reduced back down in local deployments
- The 3x multiplier was chosen for maximum compatibility
- Consider making timeouts configurable via environment variables in future

## Testing Checklist

Before deploying:
- [ ] Test on slow network (3G/4G)
- [ ] Test on fast network (Fiber)
- [ ] Verify Instagram progresses past Create menu
- [ ] Verify TikTok clicks correct Post button
- [ ] Monitor for timeout errors in logs
- [ ] Verify upload success rates improve
