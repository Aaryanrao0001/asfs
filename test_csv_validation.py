#!/usr/bin/env python3
"""
Test for enhanced CSV metadata validation.

Verifies that CSV validation works correctly with:
1. Row-by-row validation
2. UTF-8 encoding error detection
3. Better error messages
4. Empty row handling
"""

import logging
import sys
import tempfile
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_valid_csv():
    """Test loading a valid CSV file."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Valid CSV Loading")
    logger.info("=" * 80)
    
    from metadata.csv_loader import load_csv_metadata
    
    # Create a valid test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("title,caption,tags\n")
        f.write("Test Title 1,Test Caption 1,\"tag1, tag2, tag3\"\n")
        f.write("Test Title 2,Test Caption 2,\"tag4, tag5\"\n")
        csv_path = f.name
    
    try:
        metadata = load_csv_metadata(csv_path)
        
        logger.info(f"Loaded titles: {metadata['titles']}")
        logger.info(f"Loaded captions: {metadata['captions']}")
        logger.info(f"Loaded tags: {metadata['tags']}")
        
        assert len(metadata['titles']) == 2, "Should have 2 titles"
        assert len(metadata['captions']) == 2, "Should have 2 captions"
        assert len(metadata['tags']) == 5, "Should have 5 unique tags"
        
        logger.info("✓ Valid CSV loaded successfully")
        return True
    finally:
        os.unlink(csv_path)


def test_empty_rows():
    """Test CSV with empty rows."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: CSV with Empty Rows")
    logger.info("=" * 80)
    
    from metadata.csv_loader import load_csv_metadata
    
    # Create CSV with empty rows
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("title,caption,tags\n")
        f.write("Test Title 1,Test Caption 1,tag1\n")
        f.write(",,\n")  # Empty row
        f.write("   ,  ,  \n")  # Whitespace row
        f.write("Test Title 2,Test Caption 2,tag2\n")
        csv_path = f.name
    
    try:
        metadata = load_csv_metadata(csv_path)
        
        logger.info(f"Loaded titles: {metadata['titles']}")
        logger.info(f"Loaded captions: {metadata['captions']}")
        
        assert len(metadata['titles']) == 2, "Should skip empty rows"
        assert len(metadata['captions']) == 2, "Should skip empty rows"
        
        logger.info("✓ Empty rows handled correctly")
        return True
    finally:
        os.unlink(csv_path)


def test_missing_columns():
    """Test CSV with missing required columns."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: CSV with Missing Columns")
    logger.info("=" * 80)
    
    from metadata.csv_loader import load_csv_metadata
    
    # Create CSV with wrong columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("wrong_column1,wrong_column2\n")
        f.write("value1,value2\n")
        csv_path = f.name
    
    try:
        metadata = load_csv_metadata(csv_path)
        logger.error("✗ Should have raised ValueError for missing columns")
        return False
    except ValueError as e:
        logger.info(f"✓ Correctly raised ValueError: {str(e)[:100]}")
        assert "required columns" in str(e).lower() or "missing" in str(e).lower()
        return True
    finally:
        os.unlink(csv_path)


def test_empty_csv():
    """Test completely empty CSV file."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Empty CSV File")
    logger.info("=" * 80)
    
    from metadata.csv_loader import load_csv_metadata
    
    # Create empty CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("title,caption,tags\n")
        # No data rows
        csv_path = f.name
    
    try:
        metadata = load_csv_metadata(csv_path)
        logger.error("✗ Should have raised ValueError for no data")
        return False
    except ValueError as e:
        logger.info(f"✓ Correctly raised ValueError: {str(e)[:100]}")
        assert "no valid data" in str(e).lower()
        return True
    finally:
        os.unlink(csv_path)


def test_non_csv_file():
    """Test error when file is not CSV."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Non-CSV File")
    logger.info("=" * 80)
    
    from metadata.csv_loader import load_csv_metadata
    
    # Create non-CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Not a CSV file")
        txt_path = f.name
    
    try:
        metadata = load_csv_metadata(txt_path)
        logger.error("✗ Should have raised ValueError for non-CSV file")
        return False
    except ValueError as e:
        logger.info(f"✓ Correctly raised ValueError: {str(e)[:100]}")
        assert "csv format" in str(e).lower()
        return True
    finally:
        os.unlink(txt_path)


def run_all_tests():
    """Run all CSV validation tests."""
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING CSV VALIDATION TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Valid CSV Loading", test_valid_csv),
        ("Empty Rows", test_empty_rows),
        ("Missing Columns", test_missing_columns),
        ("Empty CSV", test_empty_csv),
        ("Non-CSV File", test_non_csv_file),
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
