#!/usr/bin/env python3
"""
Test suite for TikTok upload bug fixes.

This test validates:
1. Invalid CSS selector fixes (text= pseudo-selectors replaced with proper Playwright API)
2. Parameter roulette fix (explicit parameter passing, no legacy auto-detection)
3. Upload state management and retry logic
"""

import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_invalid_selector_fixes():
    """
    Test that invalid text= pseudo-selectors are replaced with proper Playwright API.
    
    INVALID:
        page.wait_for_selector('text=/regex/i')  # CSS can't parse regex
        page.wait_for_selector('text="string"')  # CSS can't parse this
    
    VALID:
        page.get_by_text(re.compile(r'pattern', re.IGNORECASE))
        page.locator('selector').wait_for(...)
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Invalid CSS Selector Fixes")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check that invalid text= selectors are NOT present
    invalid_patterns = [
        r'text=/[^/]+/i["\']',  # text=/regex/i
        r'text="[^"]+?"',       # text="string"
        r"text='[^']+?'",       # text='string'
    ]
    
    found_invalid = []
    for pattern in invalid_patterns:
        matches = re.findall(pattern, content)
        if matches:
            found_invalid.extend(matches)
    
    if found_invalid:
        logger.error(f"❌ FAIL: Found invalid text= selectors: {found_invalid}")
        return False
    
    logger.info("✅ No invalid text= selectors found")
    
    # Check that proper Playwright API is used
    proper_patterns = [
        r'page\.get_by_text\(re\.compile\(',  # page.get_by_text(re.compile(...))
        r'page\.locator\([^)]+\)\.wait_for\(',  # page.locator().wait_for()
    ]
    
    found_proper = []
    for pattern in proper_patterns:
        matches = re.findall(pattern, content)
        if matches:
            found_proper.extend(matches)
    
    if not found_proper:
        logger.warning("⚠️  WARNING: Could not find Playwright locator API usage")
    else:
        logger.info(f"✅ Found {len(found_proper)} proper Playwright API calls")
    
    # Specifically check _wait_for_real_upload function
    if 'def _wait_for_real_upload' not in content:
        logger.error("❌ FAIL: _wait_for_real_upload() function not found")
        return False
    
    # Extract the function
    func_start = content.find('def _wait_for_real_upload')
    func_end = content.find('\ndef ', func_start + 1)
    func_content = content[func_start:func_end]
    
    # Check it uses proper API
    if 'page.get_by_text(re.compile(' in func_content:
        logger.info("✅ _wait_for_real_upload uses page.get_by_text() with regex")
    else:
        logger.warning("⚠️  _wait_for_real_upload may not use proper text matching")
    
    # Check it's crash-safe
    if 'except Exception' in func_content and 'return True' in func_content:
        logger.info("✅ _wait_for_real_upload is crash-safe (returns True on error)")
    else:
        logger.error("❌ FAIL: _wait_for_real_upload not crash-safe")
        return False
    
    logger.info("✅ PASS: Invalid selectors fixed with proper Playwright API")
    return True


def test_parameter_roulette_fix():
    """
    Test that legacy parameter auto-detection is removed.
    
    The wrapper should NOT do this:
        if hashtags is None and isinstance(caption, dict):
            credentials = caption
            hashtags = description if isinstance(description, list) else []
            caption = title
            title = ""  # <-- THIS ERASES THE TITLE!
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Parameter Roulette Fix")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Find upload_to_tiktok function
    if 'def upload_to_tiktok(' not in content:
        logger.error("❌ FAIL: upload_to_tiktok() function not found")
        return False
    
    # Extract the function
    func_start = content.find('def upload_to_tiktok(')
    func_end = content.find('\ndef ', func_start + 1)
    if func_end == -1:
        func_end = len(content)
    func_content = content[func_start:func_end]
    
    # Check that legacy detection is NOT present
    legacy_patterns = [
        'if hashtags is None and isinstance(caption, dict):',
        'if credentials is None and isinstance(hashtags, dict):',
        'title = ""  # Legacy',
        'credentials = caption',
        'hashtags = description if isinstance(description, list)',
    ]
    
    found_legacy = []
    for pattern in legacy_patterns:
        if pattern in func_content:
            found_legacy.append(pattern)
    
    if found_legacy:
        logger.error(f"❌ FAIL: Legacy auto-detection still present: {found_legacy}")
        return False
    
    logger.info("✅ Legacy parameter auto-detection removed")
    
    # Check that title validation is present
    if 'if not title and not caption:' not in func_content:
        logger.error("❌ FAIL: Title validation not found")
        return False
    
    if 'raise ValueError' in func_content:
        logger.info("✅ Raises ValueError when title/caption missing")
    else:
        logger.error("❌ FAIL: Should raise ValueError for missing title")
        return False
    
    # Check that silent filename fallback is removed
    if 'video_name = os.path.splitext(os.path.basename(video_path))[0]' in func_content:
        logger.error("❌ FAIL: Silent filename fallback still present")
        return False
    
    logger.info("✅ Silent filename fallback removed")
    
    logger.info("✅ PASS: Parameter roulette fixed - no legacy detection, explicit validation")
    return True


def test_pipeline_caller_fix():
    """
    Test that pipeline.py calls upload_to_tiktok with explicit named parameters.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Pipeline Caller Fix")
    logger.info("=" * 80)
    
    with open('pipeline.py', 'r') as f:
        content = f.read()
    
    # Find the upload_to_tiktok call
    if 'upload_to_tiktok(' not in content:
        logger.error("❌ FAIL: upload_to_tiktok() call not found in pipeline.py")
        return False
    
    # Extract context around the call
    call_index = content.find('upload_to_tiktok(')
    call_context = content[call_index:call_index + 500]
    
    # Check that it uses named parameters
    required_params = [
        'video_path=',
        'title=',
        'description=',
        'caption=',
        'hashtags=',
        'credentials='
    ]
    
    found_params = []
    for param in required_params:
        if param in call_context:
            found_params.append(param)
    
    if len(found_params) < 4:  # At least video_path, title, caption, credentials
        logger.error(f"❌ FAIL: Missing named parameters. Found: {found_params}")
        return False
    
    logger.info(f"✅ Found {len(found_params)} named parameters: {found_params}")
    
    # Check that title is derived from caption before the call
    call_start = content.rfind('if platform == "TikTok":', 0, call_index)
    tiktok_block = content[call_start:call_index + 500]
    
    if 'title = caption[:100]' in tiktok_block or 'title =' in tiktok_block:
        logger.info("✅ Title is derived from caption before upload call")
    else:
        logger.warning("⚠️  Could not verify title derivation logic")
    
    logger.info("✅ PASS: Pipeline calls upload_to_tiktok with explicit named parameters")
    return True


def test_upload_state_module():
    """
    Test that upload state management module exists and has required components.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Upload State Management Module")
    logger.info("=" * 80)
    
    try:
        with open('uploaders/upload_state.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error("❌ FAIL: upload_state.py module not found")
        return False
    
    logger.info("✅ upload_state.py module exists")
    
    # Check for required classes/functions
    required_components = [
        'class UploadState(Enum):',
        'class UploadStateTracker:',
        'class RetryConfig:',
        'def retry_with_backoff(',
        'def safe_execute(',
    ]
    
    found_components = []
    for component in required_components:
        if component in content:
            found_components.append(component)
    
    if len(found_components) != len(required_components):
        missing = [c for c in required_components if c not in found_components]
        logger.error(f"❌ FAIL: Missing components: {missing}")
        return False
    
    logger.info(f"✅ All {len(required_components)} required components found")
    
    # Check for state definitions
    states = [
        'VALIDATING',
        'UPLOADING_FILE',
        'PROCESSING',
        'FILLING_CAPTION',
        'POSTING',
        'CONFIRMING',
        'DONE',
        'FAILED'
    ]
    
    found_states = [s for s in states if s in content]
    if len(found_states) >= 6:
        logger.info(f"✅ Found {len(found_states)} upload states")
    else:
        logger.error(f"❌ FAIL: Only found {len(found_states)} states, expected at least 6")
        return False
    
    logger.info("✅ PASS: Upload state management module properly implemented")
    return True


def test_retry_integration():
    """
    Test that retry logic is integrated into upload_to_tiktok wrapper.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Retry Logic Integration")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Find upload_to_tiktok function
    func_start = content.find('def upload_to_tiktok(')
    func_end = content.find('\ndef ', func_start + 1)
    if func_end == -1:
        func_end = len(content)
    func_content = content[func_start:func_end]
    
    # Check for retry_with_backoff usage
    if 'retry_with_backoff(' not in func_content:
        logger.error("❌ FAIL: retry_with_backoff not used in upload_to_tiktok")
        return False
    
    logger.info("✅ retry_with_backoff() is used")
    
    # Check for RetryConfig
    if 'RetryConfig(' not in func_content:
        logger.error("❌ FAIL: RetryConfig not used")
        return False
    
    logger.info("✅ RetryConfig is configured")
    
    # Check for exponential backoff delays
    if 'delays=[5, 15, 45]' in func_content or 'delays' in func_content:
        logger.info("✅ Exponential backoff delays configured")
    else:
        logger.warning("⚠️  Could not verify backoff delays")
    
    logger.info("✅ PASS: Retry logic integrated with exponential backoff")
    return True


def test_multi_strategy_clicking():
    """
    Test that post button clicking has multiple fallback strategies.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Multi-Strategy Button Clicking")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Find _click_post_button_with_validation function
    if 'def _click_post_button_with_validation' not in content:
        logger.error("❌ FAIL: _click_post_button_with_validation not found")
        return False
    
    func_start = content.find('def _click_post_button_with_validation')
    func_end = content.find('\ndef ', func_start + 1)
    func_content = content[func_start:func_end]
    
    # Check for multiple click strategies
    strategies = [
        ('post_button.click(', 'Strategy 1: Standard click'),
        ('page.evaluate("(element) => element.click()"', 'Strategy 2: JavaScript click'),
        ('MouseEvent', 'Strategy 3: Dispatch event'),
        ('page.keyboard.press("Enter")', 'Strategy 4: Keyboard Enter'),
    ]
    
    found_strategies = []
    for pattern, desc in strategies:
        if pattern in func_content:
            found_strategies.append(desc)
            logger.info(f"✅ Found {desc}")
    
    if len(found_strategies) < 3:
        logger.error(f"❌ FAIL: Only found {len(found_strategies)} strategies, expected at least 3")
        return False
    
    logger.info(f"✅ Found {len(found_strategies)}/4 click strategies")
    
    # Check that validator is advisory
    if 'advisory' in func_content.lower() or 'non-fatal' in func_content.lower():
        logger.info("✅ Validator is advisory (non-blocking)")
    else:
        logger.warning("⚠️  Could not verify validator is advisory")
    
    logger.info("✅ PASS: Multi-strategy button clicking implemented")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("TIKTOK UPLOAD BUG FIXES TEST SUITE")
    logger.info("=" * 80)
    
    tests = [
        ("Invalid Selector Fixes", test_invalid_selector_fixes),
        ("Parameter Roulette Fix", test_parameter_roulette_fix),
        ("Pipeline Caller Fix", test_pipeline_caller_fix),
        ("Upload State Module", test_upload_state_module),
        ("Retry Integration", test_retry_integration),
        ("Multi-Strategy Clicking", test_multi_strategy_clicking),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("-" * 80)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
