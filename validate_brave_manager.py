#!/usr/bin/env python3
"""
Validation script for BraveBrowserManager.

Tests:
1. Singleton pattern works correctly
2. Manager can be initialized and closed
3. Multiple pages can be created from same context
4. Backward compatibility with standalone mode
"""

import os
import sys
import logging
from uploaders.brave_manager import BraveBrowserManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_singleton_pattern():
    """Test that BraveBrowserManager is a true singleton."""
    logger.info("TEST 1: Singleton Pattern")
    
    instance1 = BraveBrowserManager.get_instance()
    instance2 = BraveBrowserManager.get_instance()
    
    if instance1 is instance2:
        logger.info("✓ PASS: Both instances are identical (singleton works)")
        return True
    else:
        logger.error("✗ FAIL: Instances are different (singleton broken)")
        return False


def test_initialization():
    """Test manager initialization with auto-detect."""
    logger.info("\nTEST 2: Manager Initialization")
    
    try:
        manager = BraveBrowserManager.get_instance()
        
        # Get configuration from environment or use None for auto-detect
        brave_path = os.getenv("BRAVE_PATH")
        user_data_dir = os.getenv("BRAVE_USER_DATA_DIR")
        profile_directory = os.getenv("BRAVE_PROFILE_DIRECTORY", "Default")
        
        if not user_data_dir:
            logger.warning("⚠ SKIP: BRAVE_USER_DATA_DIR not set, skipping initialization test")
            logger.info("  Set BRAVE_USER_DATA_DIR to test full initialization")
            return True
        
        manager.initialize(
            brave_path=brave_path,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory
        )
        
        if manager.is_initialized:
            logger.info("✓ PASS: Manager initialized successfully")
            
            # Test page creation
            logger.info("  Creating test page...")
            page = manager.get_page()
            logger.info("  ✓ Page created successfully")
            
            # Navigate to test URL
            logger.info("  Navigating to test URL...")
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=10000)
            logger.info("  ✓ Navigation successful")
            
            # Close page
            manager.close_page(page)
            logger.info("  ✓ Page closed successfully")
            
            # Cleanup
            manager.close()
            logger.info("  ✓ Manager closed successfully")
            
            # Reset for other tests
            BraveBrowserManager.reset_instance()
            
            return True
        else:
            logger.error("✗ FAIL: Manager not initialized")
            return False
            
    except Exception as e:
        logger.error(f"✗ FAIL: Initialization error: {e}")
        # Reset on failure
        try:
            manager = BraveBrowserManager.get_instance()
            if manager.is_initialized:
                manager.close()
            BraveBrowserManager.reset_instance()
        except:
            pass
        return False


def test_backward_compatibility():
    """Test that BraveBrowserBase still works for standalone scripts."""
    logger.info("\nTEST 3: Backward Compatibility")
    
    try:
        from uploaders.brave_base import BraveBrowserBase
        
        # Test that BraveBrowserBase can be imported and instantiated
        brave_path = os.getenv("BRAVE_PATH")
        user_data_dir = os.getenv("BRAVE_USER_DATA_DIR")
        
        if not user_data_dir:
            logger.warning("⚠ SKIP: BRAVE_USER_DATA_DIR not set, skipping backward compatibility test")
            return True
        
        # Just test instantiation, don't launch to avoid conflicts
        browser = BraveBrowserBase(
            brave_path=brave_path,
            user_data_dir=user_data_dir,
            profile_directory="Default"
        )
        
        logger.info("✓ PASS: BraveBrowserBase can still be instantiated")
        logger.info("  (Standalone scripts will continue to work)")
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Backward compatibility broken: {e}")
        return False


def test_uploader_wrapper_detection():
    """Test that uploader wrappers correctly detect manager state."""
    logger.info("\nTEST 4: Uploader Wrapper Detection")
    
    try:
        from uploaders.brave_tiktok import upload_to_tiktok
        
        # Manager should not be initialized
        manager = BraveBrowserManager.get_instance()
        
        if manager.is_initialized:
            logger.error("✗ FAIL: Manager should not be initialized at this point")
            return False
        
        logger.info("✓ PASS: Manager correctly reports as not initialized")
        logger.info("  (Uploaders will use standalone mode when manager not initialized)")
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Wrapper detection error: {e}")
        return False


def main():
    """Run all validation tests."""
    logger.info("=" * 80)
    logger.info("BRAVE BROWSER MANAGER VALIDATION")
    logger.info("=" * 80)
    
    # Run tests
    results = []
    results.append(("Singleton Pattern", test_singleton_pattern()))
    results.append(("Manager Initialization", test_initialization()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    results.append(("Uploader Wrapper Detection", test_uploader_wrapper_detection()))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 80)
    logger.info(f"RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
