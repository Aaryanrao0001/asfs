#!/usr/bin/env python3
"""
Test suite for TikTok cookie banner and upload confirmation fixes.

This test validates:
1. Cookie banner acceptance function exists
2. Cookie banner function is called after navigation
3. Force click is removed from post button logic
4. Real upload confirmation function exists
5. Upload success detection uses actual signals
6. QThread cleanup is properly implemented
"""

import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cookie_banner_function():
    """Test that cookie banner acceptance function exists."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Cookie Banner Acceptance Function")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check for _accept_tiktok_cookies function
    if 'def _accept_tiktok_cookies(page: Page):' not in content:
        logger.error("❌ FAIL: _accept_tiktok_cookies() function not found")
        return False
    logger.info("✅ Found _accept_tiktok_cookies() function")
    
    # Check that it uses evaluate to access shadow DOM
    func_match = re.search(r'def _accept_tiktok_cookies.*?(?=\ndef |\Z)', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _accept_tiktok_cookies function")
        return False
    
    func_content = func_match.group(0)
    
    required_components = [
        'tiktok-cookie-banner',
        'shadowRoot',
        'page.evaluate',
        'accept'
    ]
    
    for component in required_components:
        if component not in func_content:
            logger.error(f"❌ FAIL: Missing required component: {component}")
            return False
    
    logger.info("✅ Cookie banner function correctly uses Shadow DOM access")
    return True


def test_cookie_banner_called():
    """Test that cookie banner acceptance is called after navigation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Cookie Banner Called After Navigation")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check both upload functions call _accept_tiktok_cookies
    functions_to_check = [
        'upload_to_tiktok_browser',
        '_upload_to_tiktok_with_manager'
    ]
    
    for func_name in functions_to_check:
        # Find function
        func_match = re.search(rf'def {func_name}.*?(?=\ndef [a-z_]|\Z)', content, re.DOTALL)
        if not func_match:
            logger.error(f"❌ FAIL: Could not find function {func_name}")
            return False
        
        func_content = func_match.group(0)
        
        # Check that _accept_tiktok_cookies is called after navigation
        if '_accept_tiktok_cookies(page)' not in func_content:
            logger.error(f"❌ FAIL: {func_name} does not call _accept_tiktok_cookies")
            return False
        
        logger.info(f"✅ {func_name} calls _accept_tiktok_cookies")
    
    return True


def test_force_click_removed():
    """Test that force=True is removed from post button clicks."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Force Click Removed")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check for force=True in click calls (actual usage, not comments)
    if 'click(force=True' in content or '.click(force=' in content:
        logger.error("❌ FAIL: force=True still found in code")
        return False
    
    logger.info("✅ force=True removed from all click calls")
    
    # Check that _click_post_button_with_validation doesn't use force click
    func_match = re.search(r'def _click_post_button_with_validation.*?(?=\ndef |\Z)', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _click_post_button_with_validation function")
        return False
    
    func_content = func_match.group(0)
    # Look for actual force click usage, not documentation
    if 'click(force=True' in func_content or 'force_click' in func_content:
        logger.error("❌ FAIL: Force click usage still present in validation function")
        return False
    
    logger.info("✅ Force click removed from validation function (documentation comments are OK)")
    return True


def test_real_upload_confirmation():
    """Test that real upload confirmation function exists."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Real Upload Confirmation Function")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check for _wait_for_real_upload function
    if 'def _wait_for_real_upload(page: Page)' not in content:
        logger.error("❌ FAIL: _wait_for_real_upload() function not found")
        return False
    logger.info("✅ Found _wait_for_real_upload() function")
    
    # Check that it looks for upload indicators
    func_match = re.search(r'def _wait_for_real_upload.*?(?=\ndef |\Z)', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _wait_for_real_upload function")
        return False
    
    func_content = func_match.group(0)
    
    required_components = [
        'uploading|processing|your video',
        'wait_for_selector',
        'Upload actually started',
        'Post mutation never triggered'
    ]
    
    for component in required_components:
        if component not in func_content:
            logger.error(f"❌ FAIL: Missing required component: {component}")
            return False
    
    logger.info("✅ Real upload confirmation correctly detects upload signals")
    return True


def test_upload_confirmation_used():
    """Test that upload success detection uses _wait_for_real_upload."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Upload Confirmation Used in Upload Functions")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check both upload functions use _wait_for_real_upload
    functions_to_check = [
        'upload_to_tiktok_browser',
        '_upload_to_tiktok_with_manager'
    ]
    
    for func_name in functions_to_check:
        # Find function
        func_match = re.search(rf'def {func_name}.*?(?=\ndef [a-z_]|\Z)', content, re.DOTALL)
        if not func_match:
            logger.error(f"❌ FAIL: Could not find function {func_name}")
            return False
        
        func_content = func_match.group(0)
        
        # Check that _wait_for_real_upload is called
        if '_wait_for_real_upload(page)' not in func_content:
            logger.error(f"❌ FAIL: {func_name} does not call _wait_for_real_upload")
            return False
        
        # Check that old fake detection is removed
        if 'Still on upload page - success cannot be determined' in func_content:
            logger.error(f"❌ FAIL: {func_name} still has old fake detection logic")
            return False
        
        logger.info(f"✅ {func_name} uses _wait_for_real_upload")
    
    return True


def test_qthread_cleanup():
    """Test that QThread cleanup is properly implemented."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: QThread Cleanup Implementation")
    logger.info("=" * 80)
    
    with open('ui/tabs/videos_tab.py', 'r') as f:
        content = f.read()
    
    # Check for proper thread cleanup in on_upload_finished
    if 'sender.quit()' not in content or 'sender.wait()' not in content:
        logger.error("❌ FAIL: Thread cleanup (quit/wait) not found")
        return False
    
    logger.info("✅ Thread cleanup (quit/wait) implemented")
    
    # Check for closeEvent handler
    if 'def closeEvent(self, event):' not in content:
        logger.error("❌ FAIL: closeEvent handler not found")
        return False
    
    logger.info("✅ closeEvent handler implemented")
    
    # Check that closeEvent properly cleans up threads
    close_match = re.search(r'def closeEvent.*?event\.accept\(\)', content, re.DOTALL)
    if not close_match:
        logger.error("❌ FAIL: Could not extract closeEvent handler")
        return False
    
    close_content = close_match.group(0)
    required_components = [
        'upload_workers',
        'quit()',
        'wait(',
        'clear()'
    ]
    
    for component in required_components:
        if component not in close_content:
            logger.error(f"❌ FAIL: closeEvent missing component: {component}")
            return False
    
    logger.info("✅ closeEvent properly cleans up worker threads")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("TikTok Cookie Banner and Upload Confirmation Fixes Test Suite")
    logger.info("=" * 80)
    
    tests = [
        ("Cookie Banner Function", test_cookie_banner_function),
        ("Cookie Banner Called", test_cookie_banner_called),
        ("Force Click Removed", test_force_click_removed),
        ("Real Upload Confirmation", test_real_upload_confirmation),
        ("Upload Confirmation Used", test_upload_confirmation_used),
        ("QThread Cleanup", test_qthread_cleanup)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 80)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
