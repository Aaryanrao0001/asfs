#!/usr/bin/env python3
"""
Build script for creating ASFS executable using PyInstaller.

Builds a single-file executable with all dependencies bundled.
"""

import sys
import os
import shutil
from pathlib import Path
import PyInstaller.__main__

def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"  Removed {spec_file}")
    
    print("Clean complete.\n")


def build_executable():
    """Build the executable using PyInstaller."""
    print("Building ASFS executable...")
    print()
    
    # PyInstaller options
    options = [
        'main.py',                      # Entry point
        '--name=asfs',                  # Executable name
        '--onefile',                    # Single file executable
        '--windowed',                   # No console window (GUI app)
        '--icon=NONE',                  # No icon (can add later)
        
        # Add data files
        '--add-data=config:config',     # Include config directory
        
        # Hidden imports (modules not detected automatically)
        '--hidden-import=PySide6',
        '--hidden-import=playwright',
        '--hidden-import=faster_whisper',
        '--hidden-import=yaml',
        '--hidden-import=ollama',
        
        # Exclude unnecessary packages to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        
        # Clean build
        '--clean',
        
        # Additional options
        '--noconfirm',                  # Overwrite without asking
    ]
    
    # Platform-specific options
    if sys.platform == 'win32':
        # Windows-specific options
        options.extend([
            '--console',  # Show console for now (can change to --noconsole later)
        ])
    
    print(f"PyInstaller options: {' '.join(options)}")
    print()
    
    # Run PyInstaller
    PyInstaller.__main__.run(options)
    
    print()
    print("Build complete!")
    print()
    print(f"Executable location: dist/asfs{'exe' if sys.platform == 'win32' else ''}")
    print()


def main():
    """Main build process."""
    print("=" * 80)
    print("ASFS Executable Build Script")
    print("=" * 80)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    try:
        build_executable()
        
        print("=" * 80)
        print("BUILD SUCCESSFUL")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Test the executable in dist/")
        print("2. For Playwright browsers, run: playwright install")
        print("3. Distribute the executable to users")
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("BUILD FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
