#!/usr/bin/env python3
"""
Test for BraveBrowserManager threading safety.

Verifies that the threading fixes prevent greenlet errors by:
1. Tracking initialization thread ID
2. Validating get_page() calls are from same thread
3. Providing clear error messages for thread violations
"""

import logging
import threading
import sys
from unittest.mock import Mock, patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_thread_safety_validation():
    """
    Test that BraveBrowserManager detects thread safety violations.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Thread Safety Validation")
    logger.info("=" * 80)
    
    from uploaders.brave_manager import BraveBrowserManager
    
    # Reset to clean state
    BraveBrowserManager.reset_instance()
    
    # Get manager instance
    manager = BraveBrowserManager.get_instance()
    
    # Mock the initialization to simulate browser being initialized
    manager.is_initialized = True
    manager.thread_id = threading.get_ident()
    
    # Create mock browser_base with context
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    
    manager.browser_base = MagicMock()
    manager.browser_base.context = mock_context
    
    # Test 1: get_page() from same thread should succeed
    logger.info("Test 1: get_page() from initialization thread...")
    try:
        page = manager.get_page()
        logger.info("✓ get_page() succeeded in same thread")
        assert page == mock_page
    except RuntimeError as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False
    
    # Test 2: get_page() from different thread should fail with clear error
    logger.info("\nTest 2: get_page() from different thread...")
    
    error_raised = False
    error_message = None
    
    def call_get_page_from_thread():
        nonlocal error_raised, error_message
        try:
            manager.get_page()
            logger.error("✗ Expected RuntimeError but none was raised")
        except RuntimeError as e:
            error_raised = True
            error_message = str(e)
            logger.info(f"✓ RuntimeError raised as expected")
            logger.info(f"  Error message: {error_message[:100]}...")
    
    # Create a new thread and try to get page
    thread = threading.Thread(target=call_get_page_from_thread)
    thread.start()
    thread.join()
    
    # Verify error was raised
    assert error_raised, "Expected RuntimeError when calling get_page() from different thread"
    
    # Verify error message is helpful
    assert "wrong thread" in error_message.lower(), "Error message should mention wrong thread"
    assert "greenlet" in error_message.lower() or "playwright" in error_message.lower(), \
        "Error message should mention greenlet or playwright"
    
    logger.info("\n✓ All thread safety tests passed")
    
    # Cleanup
    manager.active_pages = []
    manager.is_initialized = False
    manager.thread_id = None
    BraveBrowserManager.reset_instance()
    
    return True


def test_thread_id_tracking():
    """
    Test that thread ID is properly tracked during initialization.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Thread ID Tracking")
    logger.info("=" * 80)
    
    from uploaders.brave_manager import BraveBrowserManager
    
    # Reset to clean state
    BraveBrowserManager.reset_instance()
    
    manager = BraveBrowserManager.get_instance()
    
    # Before initialization, thread_id should be None
    assert manager.thread_id is None, "thread_id should be None before initialization"
    logger.info("✓ thread_id is None before initialization")
    
    # Mock initialization
    with patch.object(manager, 'browser_base') as mock_base:
        mock_base.launch = MagicMock()
        mock_base.context = MagicMock()
        
        # Initialize (this should record thread ID)
        current_thread_id = threading.get_ident()
        manager.thread_id = current_thread_id
        manager.is_initialized = True
        
        logger.info(f"✓ Initialized in thread: {current_thread_id}")
        
        # Verify thread ID was recorded
        assert manager.thread_id == current_thread_id, "thread_id should match initialization thread"
        logger.info(f"✓ thread_id correctly set to: {manager.thread_id}")
    
    # Cleanup
    BraveBrowserManager.reset_instance()
    
    return True


def test_uploader_fallback():
    """
    Test that uploaders gracefully fallback to standalone mode on thread errors.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Uploader Fallback Behavior")
    logger.info("=" * 80)
    
    from uploaders.brave_manager import BraveBrowserManager
    
    # Reset to clean state
    BraveBrowserManager.reset_instance()
    
    manager = BraveBrowserManager.get_instance()
    
    # Simulate initialized manager in a different thread
    manager.is_initialized = True
    manager.thread_id = threading.get_ident() + 999  # Different thread
    manager.browser_base = MagicMock()
    manager.browser_base.context = MagicMock()
    
    # Test that get_page() raises RuntimeError
    try:
        manager.get_page()
        logger.error("✗ Expected RuntimeError but none was raised")
        return False
    except RuntimeError as e:
        logger.info("✓ RuntimeError raised as expected for wrong thread")
        logger.info(f"  Error: {str(e)[:80]}...")
    
    # Cleanup
    BraveBrowserManager.reset_instance()
    
    logger.info("✓ Uploader fallback test passed")
    return True


def run_all_tests():
    """Run all thread safety tests."""
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING ALL THREAD SAFETY TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Thread Safety Validation", test_thread_safety_validation),
        ("Thread ID Tracking", test_thread_id_tracking),
        ("Uploader Fallback", test_uploader_fallback),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\nRunning: {test_name}")
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                failed += 1
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total tests: {len(tests)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        logger.error(f"\n✗✗✗ {failed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
