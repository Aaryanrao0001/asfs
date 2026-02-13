#!/usr/bin/env python3
"""
Test suite for TikTok uploader DraftJS and readiness detection fixes.

This test validates:
1. DraftJS stability detection before caption insertion
2. Removal of unreliable Loading icon detection
3. Worker thread always emits finish signal
"""

import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_draftjs_stability_detection():
    """
    Test that DraftJS stability detection is implemented.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: DraftJS Stability Detection")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Check for _wait_for_draftjs_stable function
    if 'def _wait_for_draftjs_stable(page: Page, selector: str' not in content:
        logger.error("❌ FAIL: _wait_for_draftjs_stable() function not found")
        return False
    logger.info("✅ Found _wait_for_draftjs_stable() function")
    
    # Check that it waits for editor visibility and DraftJS initialization
    required_components = [
        'wait_for_selector(selector, state="visible"',
        'wait_for_function',
        'contentEditable',
        'DraftEditor',
    ]
    
    func_match = re.search(r'def _wait_for_draftjs_stable.*?(?=\ndef )', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _wait_for_draftjs_stable function")
        return False
    
    func_content = func_match.group(0)
    
    if not all(comp in func_content for comp in required_components):
        missing = [comp for comp in required_components if comp not in func_content]
        logger.error(f"❌ FAIL: DraftJS stability detection incomplete. Missing: {missing}")
        return False
    
    logger.info("✅ DraftJS stability detection checks for:")
    logger.info("   - Editor visibility")
    logger.info("   - ContentEditable attribute")
    logger.info("   - DraftJS initialization")
    
    logger.info("✅ PASS: DraftJS stability detection properly implemented")
    return True


def test_loading_icon_removed():
    """
    Test that unreliable Loading icon detection is removed.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Loading Icon Detection Removed")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Extract _wait_for_post_button_ready function
    func_match = re.search(r'def _wait_for_post_button_ready.*?(?=\ndef )', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _wait_for_post_button_ready function")
        return False
    
    func_content = func_match.group(0)
    
    # Check that Loading icon detection is NOT present
    if 'data-icon="Loading"' in func_content:
        logger.error("❌ FAIL: Unreliable Loading icon detection still present")
        return False
    logger.info("✅ Loading icon detection removed")
    
    # Check that post button detection is present
    if 'post_video_button' not in func_content or 'wait_for_function' not in func_content:
        logger.error("❌ FAIL: Post button detection missing")
        return False
    logger.info("✅ Post button detection present")
    
    logger.info("✅ PASS: Unreliable Loading icon detection removed")
    return True


def test_draftjs_stability_called_before_insert():
    """
    Test that DraftJS stability is checked before text insertion.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: DraftJS Stability Called Before Insert")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Extract _insert_text_into_draftjs function
    func_match = re.search(r'def _insert_text_into_draftjs.*?(?=\ndef )', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _insert_text_into_draftjs function")
        return False
    
    func_content = func_match.group(0)
    
    # Check that _wait_for_draftjs_stable is called
    if '_wait_for_draftjs_stable(page, selector' not in func_content:
        logger.error("❌ FAIL: _wait_for_draftjs_stable not called in _insert_text_into_draftjs")
        return False
    logger.info("✅ _wait_for_draftjs_stable called before insertion")
    
    # Check that insertion fails if editor not stable
    if 'did not stabilize' not in func_content or 'return False' not in func_content:
        logger.error("❌ FAIL: Missing error handling for unstable editor")
        return False
    logger.info("✅ Error handling for unstable editor present")
    
    # Verify the call comes before the evaluate call
    stability_check_pos = func_content.find('_wait_for_draftjs_stable')
    evaluate_pos = func_content.find('page.evaluate')
    
    if stability_check_pos < 0 or evaluate_pos < 0:
        logger.error("❌ FAIL: Could not find stability check or evaluate call")
        return False
    
    if stability_check_pos > evaluate_pos:
        logger.error("❌ FAIL: Stability check comes after evaluate call")
        return False
    logger.info("✅ Stability check comes before evaluate call")
    
    logger.info("✅ PASS: DraftJS stability is properly checked before text insertion")
    return True


def test_worker_thread_finish_signal():
    """
    Test that worker thread always emits finish signal in exception handler.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Worker Thread Finish Signal")
    logger.info("=" * 80)
    
    with open('ui/workers/upload_worker.py', 'r') as f:
        content = f.read()
    
    # Extract UploadWorker.run method
    # Look for the run method in UploadWorker class
    class_match = re.search(r'class UploadWorker.*?(?=class |$)', content, re.DOTALL)
    if not class_match:
        logger.error("❌ FAIL: Could not extract UploadWorker class")
        return False
    
    class_content = class_match.group(0)
    
    # Find the run method
    run_match = re.search(r'def run\(self\):.*?(?=\n    def |\nclass |$)', class_content, re.DOTALL)
    if not run_match:
        logger.error("❌ FAIL: Could not extract run() method")
        return False
    
    run_content = run_match.group(0)
    
    # Check that exception handler exists
    if 'except Exception as e:' not in run_content:
        logger.error("❌ FAIL: Exception handler not found")
        return False
    logger.info("✅ Exception handler found")
    
    # Extract exception handler block
    exception_match = re.search(r'except Exception as e:.*', run_content, re.DOTALL)
    if not exception_match:
        logger.error("❌ FAIL: Could not extract exception handler")
        return False
    
    exception_content = exception_match.group(0)
    
    # Check that upload_error.emit is present
    if 'self.upload_error.emit' not in exception_content:
        logger.error("❌ FAIL: upload_error.emit not found in exception handler")
        return False
    logger.info("✅ upload_error.emit found")
    
    # Check that upload_finished.emit is also present in exception handler
    if 'self.upload_finished.emit' not in exception_content:
        logger.error("❌ FAIL: upload_finished.emit not found in exception handler")
        return False
    logger.info("✅ upload_finished.emit found in exception handler")
    
    # Verify that False is passed to indicate failure
    if 'self.upload_finished.emit(self.video_id, self.platform, False)' not in exception_content:
        logger.error("❌ FAIL: upload_finished.emit not called with False in exception handler")
        return False
    logger.info("✅ upload_finished.emit called with False to indicate failure")
    
    logger.info("✅ PASS: Worker thread always emits finish signal")
    return True


def run_all_tests():
    """Run all test functions."""
    logger.info("\n" + "=" * 80)
    logger.info("TikTok Uploader DraftJS Fixes - Test Suite")
    logger.info("=" * 80)
    
    tests = [
        test_draftjs_stability_detection,
        test_loading_icon_removed,
        test_draftjs_stability_called_before_insert,
        test_worker_thread_finish_signal,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
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
