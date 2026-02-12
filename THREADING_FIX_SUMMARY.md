# Threading Bug Fix & Feature Additions - Summary

## Overview

This update addresses the critical greenlet threading error in Playwright/BraveBrowserManager and adds several important features to improve the application's robustness and usability.

## Critical Bug Fixed

### Greenlet Threading Error

**Problem**: The application was experiencing fatal threading errors:
```
ERROR - YouTube browser upload failed: Cannot switch to a different thread
  Current:  <greenlet.greenlet object at 0x7cf22f6f1880>
  Expected: <greenlet.greenlet object at 0x7cf223c01380>
```

**Root Cause**: Playwright's sync API uses greenlets which are NOT thread-safe. The BraveBrowserManager was being initialized in one thread (main thread) but worker threads (UploadWorker, scheduler) were trying to call `get_page()` from different threads.

**Solution Implemented**:
1. **Thread Tracking**: BraveBrowserManager now tracks the thread ID where it was initialized
2. **Thread Validation**: Every `get_page()` call validates it's from the same thread
3. **Clear Error Messages**: When thread mismatch is detected, a detailed error explains the issue
4. **Graceful Fallback**: Uploaders catch the threading error and fall back to standalone browser mode

## New Features

### 1. BulkUploadScheduler

A new scheduler for uploading multiple videos to multiple platforms:

**Features**:
- Upload N videos to M platforms in sequence
- Configurable delay between uploads (prevents rate limiting)
- Pause/resume capability
- Cancel operation at any time
- Progress tracking via Qt signals
- Per-platform selection

**Usage**:
```python
from scheduler import BulkUploadScheduler

scheduler = BulkUploadScheduler(
    video_ids=['video1', 'video2', 'video3'],
    platforms=['Instagram', 'TikTok', 'YouTube'],
    delay_seconds=60,  # 1 minute between uploads
    upload_callback=my_upload_function
)

scheduler.upload_started.connect(on_upload_started)
scheduler.all_finished.connect(on_all_finished)
scheduler.start()
```

### 2. Enhanced Dependency Validation

Improved dependency checking with better error messages:

**Before**:
```python
check_ffmpeg()  # Returns: (True, "/usr/bin/ffmpeg")
```

**After**:
```python
check_ffmpeg()  # Returns: (True, "/usr/bin/ffmpeg (ffmpeg version 4.4.2-0ubuntu0.22.04.1)")
```

**Improvements**:
- Version detection for ffmpeg/ffprobe
- Timeout handling (5 second timeout)
- Empty stdout protection
- Better error messages with installation links

### 3. Improved CSV Validation

Enhanced CSV metadata loading with comprehensive validation:

**Features**:
- Row-by-row validation with line numbers
- Empty row detection and warnings
- UTF-8 encoding error detection
- Missing column validation
- Better error messages

**Before**:
```
Error: Failed to load CSV metadata: 'reader' object has no attribute 'line_num'
```

**After**:
```
Error: CSV missing required columns. Required at least one of: title, caption, description, tags. Found: wrong_column1, wrong_column2
Error: Row 3: Empty or all whitespace, skipping
Error: CSV file encoding error. Please save as UTF-8: /path/to/file.csv
```

## Testing

### Test Coverage

All changes are thoroughly tested:

1. **test_threading_fix.py** (3 tests)
   - Thread safety validation
   - Thread ID tracking
   - Uploader fallback behavior

2. **test_dependency_validation.py** (1 test)
   - Dependency checks with version info

3. **test_csv_validation.py** (5 tests)
   - Valid CSV loading
   - Empty row handling
   - Missing column detection
   - Empty CSV error handling
   - Non-CSV file rejection

**Result**: ✓ All 9 tests pass

### Security Scan

- **CodeQL**: ✓ No security vulnerabilities found
- **Code Review**: ✓ All feedback addressed

## Breaking Changes

**None** - All changes are backward compatible:
- Existing code continues to work
- Graceful fallback for threading issues
- Enhanced validation doesn't break valid inputs

## Migration Guide

No migration needed! The changes are transparent to existing code:

1. **Threading**: Existing code will see improved error messages if threading issues occur
2. **Dependencies**: Existing dependency checks work as before, just with more information
3. **CSV Loading**: Existing CSV files load as before, with better error messages for invalid files

## Recommendations

### For Production Use

1. **Initialize browser in main thread**: Ensure BraveBrowserManager.initialize() is called from the main thread
2. **Use BulkUploadScheduler**: For multiple uploads, use the new scheduler to avoid rate limiting
3. **Validate dependencies early**: Call check_all_dependencies() at startup to provide early feedback

### For Development

1. **Test threading**: If adding new workers, test with the threading validation
2. **Use enhanced errors**: The new error messages provide actionable guidance
3. **Test CSV files**: Use the CSV validator before attempting to load metadata

## Technical Details

### Thread Safety Implementation

```python
class BraveBrowserManager:
    def __init__(self):
        self.thread_id: Optional[int] = None
        self._page_lock = threading.Lock()
    
    def initialize(self, ...):
        self.thread_id = threading.get_ident()  # Record thread
        # ... initialize browser
    
    def get_page(self) -> Page:
        current_thread = threading.get_ident()
        if current_thread != self.thread_id:
            raise RuntimeError(
                f"BraveBrowserManager.get_page() called from wrong thread!\n"
                f"  Manager initialized in thread: {self.thread_id}\n"
                f"  Current thread: {current_thread}\n"
                f"  Playwright sync API requires same-thread usage."
            )
        # ... create page
```

### Uploader Fallback

```python
def _upload_to_youtube_with_manager(...):
    try:
        page = manager.get_page()
    except RuntimeError as e:
        logger.error(f"Thread safety violation: {e}")
        logger.warning("Falling back to standalone browser mode")
        return upload_to_youtube_browser(...)  # Fallback
```

## Performance Impact

- **Minimal**: Thread validation is a simple integer comparison
- **No overhead**: Only runs when get_page() is called
- **Safer**: Prevents crashes that would otherwise occur

## Future Improvements

Potential enhancements for future versions:

1. **Thread-local browser instances**: Support multiple threads by creating browser per thread
2. **UI integration**: Add bulk upload UI to videos_tab.py
3. **Advanced scheduling**: Time-based scheduling, cron-like expressions
4. **Upload queue**: Priority-based upload queue with retry logic

## Support

If you encounter issues:

1. Check the error message - they now include actionable guidance
2. Verify threading requirements are met
3. Run dependency checks: `python -c "from validator.dependencies import check_all_dependencies; print(check_all_dependencies())"`
4. Review test files for examples
