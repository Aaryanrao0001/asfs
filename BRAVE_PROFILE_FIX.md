# Brave Profile Fix: Resolving Google Login Issues

## Problem Statement

When using Playwright to automate uploads to platforms requiring Google login (YouTube, etc.), the browser was being blocked with the error:

```
❌ "This browser may not be secure"
```

**Root Cause**: Playwright was creating temporary, sandboxed profiles instead of using the user's real Brave profile where they're already logged in.

## Solution Overview

The fix ensures that Playwright uses the **actual Brave browser profile** with existing login sessions, eliminating the need for repeated logins and avoiding security blocks.

### Key Changes

1. **Use `launch_persistent_context()` instead of `launch()`**
   - This is the ONLY correct way to maintain real profile sessions
   - The user data directory is passed as the first parameter
   - The profile directory is specified via `--profile-directory` argument

2. **Separate User Data Dir and Profile Directory**
   - **User Data Dir**: The main Brave data folder (e.g., `C:\Users\<USER>\AppData\Local\BraveSoftware\Brave-Browser\User Data`)
   - **Profile Directory**: The specific profile within that folder (e.g., "Default", "Profile 1", "Profile 2")

3. **Hard Validation**
   - The system now fails immediately if the profile doesn't exist
   - Provides helpful error messages listing available profiles

4. **Anti-Detection Arguments**
   - `--disable-blink-features=AutomationControlled`: Hides automation indicators
   - `--no-first-run`: Skips first run wizard
   - `--no-default-browser-check`: Skips default browser prompt

## Configuration

### Windows Example

```python
from uploaders.brave_base import BraveBrowserBase

browser = BraveBrowserBase(
    brave_path="C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
    user_data_dir=r"C:\Users\pooja\AppData\Local\BraveSoftware\Brave-Browser\User Data",
    profile_directory="Default"
)
```

### macOS Example

```python
browser = BraveBrowserBase(
    brave_path="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    user_data_dir=os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
    profile_directory="Default"
)
```

### Linux Example

```python
browser = BraveBrowserBase(
    brave_path="/usr/bin/brave-browser",
    user_data_dir=os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
    profile_directory="Default"
)
```

## Finding Your Profile

### Windows

1. Press `Win + R` and type `%LOCALAPPDATA%`
2. Navigate to `BraveSoftware\Brave-Browser\User Data`
3. You'll see folders like `Default`, `Profile 1`, `Profile 2`
4. Pick the one where you're logged into Google

### macOS

1. Open Finder
2. Press `Cmd + Shift + G` and enter `~/Library/Application Support/BraveSoftware/Brave-Browser`
3. Look for `Default`, `Profile 1`, etc.

### Linux

1. Navigate to `~/.config/BraveSoftware/Brave-Browser`
2. Look for profile directories

## UI Usage

The Upload tab now has three key fields:

### 1. Brave Browser Executable
- Path to the Brave executable
- Leave empty to auto-detect
- Browse button available

### 2. User Data Directory
- The main Brave data folder containing all profiles
- **Required** for login persistence
- Browse button available
- Auto-populates with platform default

### 3. Profile Directory
- Dropdown showing available profiles in the user data dir
- Select which profile to use (e.g., "Default", "Profile 1")
- Refresh button to re-scan for profiles
- Editable if you know the exact name

### 4. Test Profile Button
- Opens Google in Brave to verify configuration
- Confirms you're logged in
- Browser closes automatically after 15 seconds
- **Use this before running uploads** to ensure correct setup

## Technical Implementation

### BraveBrowserBase Changes

**Before:**
```python
# ❌ WRONG: Creates temp profile
browser = self.playwright.chromium.launch(
    executable_path=self.brave_path,
    args=[f"--user-data-dir={self.profile_path}"]
)
```

**After:**
```python
# ✅ CORRECT: Uses real persistent profile
self.context = self.playwright.chromium.launch_persistent_context(
    user_data_dir=self.user_data_dir,
    executable_path=self.brave_path,
    headless=False,
    args=[
        f"--profile-directory={self.profile_directory}",
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]
)
```

### New Methods

1. **`_validate_profile()`**
   - Checks that user data dir exists
   - Checks that profile directory exists within it
   - Lists available profiles if validation fails

2. **`get_available_profiles(user_data_dir)`** (static)
   - Returns list of profile directories in a user data dir
   - Filters for "Default" and "Profile *" directories

### Uploader Function Signatures

All Brave uploaders now use the new signature:

```python
def upload_to_<platform>_browser(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    brave_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    profile_directory: str = "Default"
) -> Optional[str]:
```

Changed from:
- `profile_path` → `user_data_dir` + `profile_directory`

## Important Rules

### ✅ DO

- Specify both user_data_dir and profile_directory for production
- Use the profile where you're already logged in
- Test your configuration with the "Test Profile" button
- Use headless=False for platforms requiring login

### ❌ DO NOT

- Use `--incognito` mode
- Use `--disable-web-security`
- Use temporary directories
- Use headless mode for Google login
- Forget to validate your profile exists

## Troubleshooting

### Error: "Brave user data directory not found"

**Solution**: Check that the path is correct. On Windows, it should be:
```
C:\Users\<YOUR_USERNAME>\AppData\Local\BraveSoftware\Brave-Browser\User Data
```

### Error: "Brave profile not found"

**Solution**: 
1. The error message lists available profiles
2. Pick one from the list (usually "Default")
3. Or check which profile you use in Brave browser

### Google Still Blocking

**Checklist**:
1. Are you using the correct profile where you're logged in?
2. Did you test with the "Test Profile" button first?
3. Is headless mode disabled (headless=False)?
4. Is user_data_dir correctly set?

### Profile Test Fails

**Possible causes**:
1. Brave not installed at specified path
2. User data directory path incorrect
3. Profile directory name wrong
4. Network issues
5. Brave already running (close it first)

## Backward Compatibility

If `user_data_dir` is not specified, the system falls back to temp profile mode with a warning:

```
WARNING: No user_data_dir specified - using temporary profile.
This may cause login failures on Google and other platforms.
Specify user_data_dir and profile_directory for production use.
```

## Migration Guide

If you have existing code using the old API:

**Before:**
```python
browser = BraveBrowserBase(
    brave_path="...",
    profile_path="C:\\Users\\user\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"
)
```

**After:**
```python
browser = BraveBrowserBase(
    brave_path="...",
    user_data_dir="C:\\Users\\user\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data",
    profile_directory="Default"
)
```

**Credentials dict (for backward-compatible functions):**

Before:
```python
credentials = {
    "brave_path": "...",
    "brave_profile_path": "..."
}
```

After:
```python
credentials = {
    "brave_path": "...",
    "brave_user_data_dir": "...",
    "brave_profile_directory": "Default"
}
```

## Credits

This fix implements the production-grade solution for Playwright + Brave profile reuse, ensuring reliable platform uploads without repeated logins or security blocks.
