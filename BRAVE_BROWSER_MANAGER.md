# Brave Browser Manager - Fix Documentation

## Overview

This document explains the fixes applied to resolve critical bugs in the Brave browser automation pipeline that prevented proper profile reuse and caused upload failures.

## Problems Solved

### Bug 1: Multiple Browser Instances Killing Each Other
**Problem**: Each uploader (TikTok, Instagram, YouTube) created its own `BraveBrowserBase` instance, which called `_kill_brave_processes()` during launch, terminating the previous uploader's browser.

**Solution**: Created a singleton `BraveBrowserManager` that manages a single browser instance across all uploads.

### Bug 2: Multiple Playwright Instances Causing Profile Lock Conflicts
**Problem**: Each uploader started a new `sync_playwright().start()`, causing profile lock conflicts when multiple uploaders tried to access the same Brave profile.

**Solution**: The `BraveBrowserManager` starts Playwright only once and shares it across all uploaders.

### Bug 3: Empty Credentials Causing Temp Profile Fallback
**Problem**: Pipeline passed empty dictionaries `{}` as credentials, so uploaders received `None` for `user_data_dir`, triggering the fallback to temporary profiles (users logged out).

**Solution**: Pipeline now loads browser configuration from environment variables and passes it to all uploaders via credentials.

### Bug 4: Individual close() Calls Destroying Shared Resources
**Problem**: Each uploader called `browser.close()` which stopped the Playwright instance, breaking subsequent uploads.

**Solution**: Uploaders now only close their individual pages, while the manager handles final browser cleanup.

## Architecture

### BraveBrowserManager (Singleton)

The `BraveBrowserManager` class provides:

1. **Single Playwright Instance**: One `sync_playwright().start()` for entire pipeline
2. **Single Persistent Context**: One `launch_persistent_context()` call with real profile
3. **Process Cleanup Once**: `_kill_brave_processes()` called only at initialization
4. **Page Management**: Each uploader gets a new page (tab) from shared context
5. **Thread-Safe**: Uses double-checked locking for singleton pattern

### Usage in Pipeline

```python
from uploaders import BraveBrowserManager

# Initialize once before uploads
browser_manager = BraveBrowserManager.get_instance()
browser_manager.initialize(
    brave_path=brave_path,
    user_data_dir=brave_user_data_dir,  # REQUIRED for persistent login
    profile_directory=brave_profile_directory
)

try:
    # Upload clips...
    # Each uploader will automatically use the shared browser
finally:
    # Cleanup once after all uploads
    browser_manager.close()
```

### Usage in Uploaders

Each uploader wrapper function (`upload_to_tiktok`, `upload_to_instagram`, `upload_to_youtube`) now:

1. Checks if `BraveBrowserManager` is initialized
2. If yes → Uses `_upload_to_<platform>_with_manager()` (shared browser)
3. If no → Falls back to `upload_to_<platform>_browser()` (standalone mode)

This maintains **backward compatibility** with standalone test scripts.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Optional - auto-detects if not set
BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe

# REQUIRED for persistent login (no temp profiles)
BRAVE_USER_DATA_DIR=C:\Users\YourName\AppData\Local\BraveSoftware\Brave-Browser\User Data

# Default profile or "Profile 1", "Profile 2", etc.
BRAVE_PROFILE_DIRECTORY=Default
```

### Finding Your Profile Path

**Windows**:
```
User Data Dir: C:\Users\<USERNAME>\AppData\Local\BraveSoftware\Brave-Browser\User Data
Profiles: Default, Profile 1, Profile 2, ...
```

**macOS**:
```
User Data Dir: /Users/<USERNAME>/Library/Application Support/BraveSoftware/Brave-Browser
Profiles: Default, Profile 1, Profile 2, ...
```

**Linux**:
```
User Data Dir: /home/<username>/.config/BraveSoftware/Brave-Browser
Profiles: Default, Profile 1, Profile 2, ...
```

## Backward Compatibility

### Standalone Scripts (Still Work)

```python
from uploaders import upload_to_tiktok_browser

# Direct browser launch (no manager)
upload_to_tiktok_browser(
    video_path="video.mp4",
    title="My Video",
    description="Description",
    tags="#viral #trending",
    brave_path=None,  # Auto-detect
    user_data_dir=r"C:\Users\Me\AppData\Local\BraveSoftware\Brave-Browser\User Data",
    profile_directory="Default"
)
```

### Pipeline Mode (Automatic)

The pipeline automatically initializes the manager when browser config is provided:

```python
# Pipeline detects manager is initialized and uses shared context
upload_to_tiktok(video_path, caption, hashtags, credentials)
upload_to_instagram(video_path, caption, hashtags, credentials)
upload_to_youtube(video_path, caption, hashtags, credentials)
```

## Benefits

1. **No More Profile Lock Conflicts**: Single persistent context
2. **Persistent Login Sessions**: Real profile reuse across uploads
3. **No Browser Restarts**: Browser stays open between uploads
4. **Better Performance**: No kill/restart overhead
5. **Clean Tab Management**: Each uploader gets fresh page, navigates to about:blank after
6. **Backward Compatible**: Existing test scripts still work

## Implementation Details

### Files Changed

1. **uploaders/brave_manager.py** (new): Singleton manager class
2. **uploaders/__init__.py**: Export `BraveBrowserManager`
3. **uploaders/brave_tiktok.py**: Use manager when available
4. **uploaders/brave_instagram.py**: Use manager when available
5. **uploaders/brave_youtube.py**: Use manager when available
6. **pipeline.py**: Initialize manager, populate credentials, cleanup in finally

### Key Constraints Met

- ✅ Windows platform, Brave browser, Playwright sync API
- ✅ Real user profile reuse (no temp profiles)
- ✅ Headed mode only (no headless)
- ✅ Backward compatibility with existing function signatures
- ✅ Does NOT break standalone test scripts using `BraveBrowserBase` directly

## Testing

### Manual Test - Standalone Mode

```python
from uploaders import upload_to_tiktok_browser

result = upload_to_tiktok_browser(
    video_path="test_video.mp4",
    title="Test",
    description="Test upload",
    tags="#test",
    user_data_dir=r"C:\Users\Me\AppData\Local\BraveSoftware\Brave-Browser\User Data"
)
print(result)
```

### Manual Test - Pipeline Mode

```bash
# Set environment variables
export BRAVE_USER_DATA_DIR="/Users/me/Library/Application Support/BraveSoftware/Brave-Browser"
export BRAVE_PROFILE_DIRECTORY="Default"

# Run pipeline
python pipeline.py input_video.mp4
```

## Troubleshooting

### Issue: Still logged out

**Check**:
1. Is `BRAVE_USER_DATA_DIR` set correctly?
2. Does the profile directory exist?
3. Are you logged in to TikTok/Instagram/YouTube in that profile?

### Issue: Profile lock error

**Check**:
1. Close all Brave browser windows before running pipeline
2. Ensure no other scripts are using the same profile

### Issue: Browser crashes

**Check**:
1. Use headed mode (headless breaks Google login)
2. Ensure Brave is not auto-updating during upload

## Future Improvements

1. Add retry logic for network failures
2. Add screenshot capture on upload errors
3. Add upload progress tracking
4. Add parallel upload support (requires multiple profiles)
