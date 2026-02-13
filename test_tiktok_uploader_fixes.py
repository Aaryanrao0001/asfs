#!/usr/bin/env python3
"""
Test suite for TikTok uploader fixes.

This test validates:
1. page.evaluate() syntax fix - proper argument passing
2. Navigation retry logic with verification
3. Page load verification helpers
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_page_evaluate_syntax():
    """
    Test that the page.evaluate() fix uses correct syntax.
    
    The fix changes from:
        page.evaluate(js_code, arg1, arg2)  # WRONG - 4 positional args
    To:
        page.evaluate(js_code, {"key1": arg1, "key2": arg2})  # CORRECT - 3 args
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: page.evaluate() Syntax Fix")
    logger.info("=" * 80)
    
    # Read the brave_tiktok.py file
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check that the old syntax is NOT present
    old_syntax = 'page.evaluate("""', 'selector, text)'
    if all(s in content for s in old_syntax):
        logger.error("❌ FAIL: Old page.evaluate() syntax still present")
        return False
    
    # Check that the new syntax IS present
    new_syntax_parts = [
        'page.evaluate("""',
        '(args) =>',
        'args.selector',
        'args.text',
        '{"selector": selector, "text": text}'
    ]
    
    found_parts = [part in content for part in new_syntax_parts]
    if not all(found_parts):
        missing = [new_syntax_parts[i] for i, found in enumerate(found_parts) if not found]
        logger.error(f"❌ FAIL: New page.evaluate() syntax incomplete. Missing: {missing}")
        return False
    
    logger.info("✅ PASS: page.evaluate() syntax correctly fixed")
    logger.info("   - Changed from multiple arguments to single dict argument")
    logger.info("   - JavaScript uses args.selector and args.text")
    return True


def test_navigation_retry_helpers():
    """
    Test that navigation retry helpers are present and properly structured.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Navigation Retry Helpers")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check for _verify_page_loaded function
    if 'def _verify_page_loaded(page: Page, expected_elements: list' not in content:
        logger.error("❌ FAIL: _verify_page_loaded() function not found")
        return False
    logger.info("✅ Found _verify_page_loaded() helper function")
    
    # Check for _navigate_with_retry function
    if 'def _navigate_with_retry(page: Page, url: str, max_retries: int = 3' not in content:
        logger.error("❌ FAIL: _navigate_with_retry() function not found")
        return False
    logger.info("✅ Found _navigate_with_retry() helper function")
    
    # Check that retry logic is implemented
    retry_components = [
        'for attempt in range(max_retries):',
        'page.goto(url',
        'verify_selectors',
        '_verify_page_loaded',
        'if attempt < max_retries - 1:',
        'continue'
    ]
    
    if not all(comp in content for comp in retry_components):
        logger.error("❌ FAIL: Retry logic components missing")
        return False
    logger.info("✅ Retry logic properly implemented with loop and continue")
    
    logger.info("✅ PASS: Navigation retry helpers properly implemented")
    return True


def test_navigation_usage():
    """
    Test that the new navigation retry is actually used in upload function.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Navigation Retry Usage")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check that old direct page.goto is replaced
    # Look for the upload_to_tiktok_browser function
    if 'def upload_to_tiktok_browser(' not in content:
        logger.error("❌ FAIL: upload_to_tiktok_browser() function not found")
        return False
    
    # Extract the function content (simplified check)
    func_start = content.find('def upload_to_tiktok_browser(')
    func_content = content[func_start:func_start + 10000]  # Get reasonable chunk
    
    # Check that _navigate_with_retry is called
    if '_navigate_with_retry(' not in func_content:
        logger.error("❌ FAIL: _navigate_with_retry() not called in upload function")
        return False
    logger.info("✅ Found _navigate_with_retry() call in upload function")
    
    # Check that verify_selectors are defined
    if "verify_selectors = [" not in func_content:
        logger.error("❌ FAIL: verify_selectors not defined")
        return False
    logger.info("✅ Found verify_selectors definition")
    
    # Check for file input selector
    if "'input[type=\"file\"]'" not in func_content:
        logger.error("❌ FAIL: File input selector not in verify_selectors")
        return False
    logger.info("✅ File input selector included in verification")
    
    logger.info("✅ PASS: Navigation retry properly used in upload function")
    return True


def test_improved_wait_times():
    """
    Test that wait times have been improved.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Improved Wait Times")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    improvements = []
    
    # Check for increased networkidle timeout after file upload
    if 'page.wait_for_load_state("networkidle", timeout=30000)' in content:
        improvements.append("Network idle timeout increased to 30s")
        logger.info("✅ Network idle timeout increased from 20s to 30s")
    
    # Check for increased fallback delay
    if 'page.wait_for_timeout(8000)' in content:
        improvements.append("Fallback delay increased to 8s")
        logger.info("✅ Fallback delay increased from 5s to 8s")
    
    # Check for upload page verification
    if 'if "upload" not in page.url.lower():' in content:
        improvements.append("Added verification to stay on upload page")
        logger.info("✅ Added verification to ensure staying on upload page")
    
    if len(improvements) >= 2:
        logger.info("✅ PASS: Wait times and verification improved")
        return True
    else:
        logger.error(f"❌ FAIL: Insufficient wait time improvements ({len(improvements)}/3)")
        return False


def run_all_tests():
    """Run all test functions."""
    logger.info("\n" + "=" * 80)
    logger.info("TikTok Uploader Fixes - Test Suite")
    logger.info("=" * 80)
    
    tests = [
        test_page_evaluate_syntax,
        test_navigation_retry_helpers,
        test_navigation_usage,
        test_improved_wait_times,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    passed = sum(results)
    total = len(results)
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ ALL TESTS PASSED")
        return True
    else:
        logger.error(f"❌ {total - passed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
