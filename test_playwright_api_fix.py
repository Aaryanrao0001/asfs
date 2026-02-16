#!/usr/bin/env python3
"""
Test to verify Playwright wait_for_function API is used correctly.

This test validates that the fixed code uses the correct keyword argument syntax
for page.wait_for_function() calls.
"""

import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_wait_for_function_syntax():
    """
    Test that wait_for_function calls use correct keyword argument syntax.
    
    Playwright's Python API signature:
        page.wait_for_function(expression, *, arg=None, timeout=None)
    
    The '*' means all arguments after expression MUST be keyword arguments.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Playwright wait_for_function API Syntax")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Find all wait_for_function calls
    pattern = r'page\.wait_for_function\(\s*""".*?"""\s*,\s*([^)]+)\)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    all_correct = True
    call_count = 0
    
    for match in matches:
        call_count += 1
        args_str = match.group(1).strip()
        logger.info(f"\nFound wait_for_function call #{call_count}:")
        logger.info(f"  Arguments: {args_str[:60]}...")
        
        # Check if any positional arguments are passed (except for keyword args)
        # Valid patterns:
        # - timeout=value
        # - arg=value, timeout=value
        # Invalid patterns:
        # - selector, timeout=value (selector is positional)
        # - value, arg=value (value is positional)
        
        # Split by comma, but be careful with nested function calls
        args_parts = [arg.strip() for arg in args_str.split(',')]
        
        for i, part in enumerate(args_parts):
            # Check if it's a keyword argument (contains '=')
            if '=' not in part:
                logger.error(f"  ❌ FAIL: Positional argument found: '{part}'")
                logger.error(f"     All arguments after expression must be keyword arguments")
                all_correct = False
            else:
                # It's a keyword argument
                key = part.split('=')[0].strip()
                if key not in ['arg', 'timeout', 'polling']:
                    logger.warning(f"  ⚠️  Unknown keyword argument: '{key}'")
                else:
                    logger.info(f"  ✅ Correct keyword argument: {key}=...")
    
    logger.info(f"\nTotal wait_for_function calls found: {call_count}")
    
    if call_count == 0:
        logger.error("❌ FAIL: No wait_for_function calls found")
        return False
    
    if all_correct:
        logger.info("✅ PASS: All wait_for_function calls use correct syntax")
        return True
    else:
        logger.error("❌ FAIL: Some wait_for_function calls use incorrect syntax")
        return False


def test_draftjs_function_uses_arg_keyword():
    """
    Specifically test that _wait_for_draftjs_stable uses arg=selector.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: DraftJS Function Uses arg= Keyword")
    logger.info("=" * 80)
    
    with open('uploaders/brave_tiktok.py', 'r') as f:
        content = f.read()
    
    # Extract _wait_for_draftjs_stable function
    func_match = re.search(r'def _wait_for_draftjs_stable.*?(?=\ndef |\Z)', content, re.DOTALL)
    if not func_match:
        logger.error("❌ FAIL: Could not extract _wait_for_draftjs_stable function")
        return False
    
    func_content = func_match.group(0)
    
    # Check for the specific pattern: page.wait_for_function("""...""", arg=selector, timeout=timeout)
    # The function takes a selector parameter and should pass it using arg=
    if 'arg=selector' in func_content:
        logger.info("✅ Found 'arg=selector' in _wait_for_draftjs_stable")
        logger.info("✅ PASS: DraftJS function correctly uses arg= keyword argument")
        return True
    else:
        # Check if old buggy pattern exists
        if re.search(r'page\.wait_for_function\([^)]*"""\s*,\s*selector\s*,', func_content):
            logger.error("❌ FAIL: Old buggy pattern found: passing selector as positional argument")
            return False
        else:
            logger.warning("⚠️  Could not verify arg=selector pattern")
            return False


def run_all_tests():
    """Run all test functions."""
    logger.info("\n" + "=" * 80)
    logger.info("Playwright API Fix Verification - Test Suite")
    logger.info("=" * 80)
    
    tests = [
        test_wait_for_function_syntax,
        test_draftjs_function_uses_arg_keyword,
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
