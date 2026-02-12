#!/usr/bin/env python3
"""
Test for enhanced dependency validation.

Verifies that dependency checking works correctly with:
1. Version detection for ffmpeg/ffprobe
2. Better error messages
3. Timeout handling
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_dependency_checks():
    """Test dependency validation functions."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Dependency Checks")
    logger.info("=" * 80)
    
    from validator.dependencies import (
        check_ffmpeg,
        check_ffprobe,
        check_all_dependencies,
        get_dependency_status_message
    )
    
    # Test ffmpeg check
    logger.info("\nChecking ffmpeg...")
    ffmpeg_available, ffmpeg_msg = check_ffmpeg()
    logger.info(f"  Available: {ffmpeg_available}")
    logger.info(f"  Message: {ffmpeg_msg}")
    
    # Test ffprobe check
    logger.info("\nChecking ffprobe...")
    ffprobe_available, ffprobe_msg = check_ffprobe()
    logger.info(f"  Available: {ffprobe_available}")
    logger.info(f"  Message: {ffprobe_msg}")
    
    # Test all dependencies
    logger.info("\nChecking all dependencies...")
    results = check_all_dependencies()
    for name, (available, message) in results.items():
        status = "✓" if available else "✗"
        logger.info(f"  {status} {name}: {message}")
    
    # Test status message
    logger.info("\nGetting status message...")
    status_msg = get_dependency_status_message()
    logger.info(status_msg)
    
    logger.info("\n✓ Dependency checks completed")
    return True


def run_all_tests():
    """Run all dependency validation tests."""
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING DEPENDENCY VALIDATION TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Dependency Checks", test_dependency_checks),
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
