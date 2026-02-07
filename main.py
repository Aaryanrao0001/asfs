#!/usr/bin/env python3
"""
ASFS - Automated Short-Form Content System

Main entry point for the application.
Launches the desktop UI by default, or CLI mode with --cli flag.
"""

import sys
import argparse


def main():
    """Main entry point - route to GUI or CLI."""
    parser = argparse.ArgumentParser(
        description='ASFS - Automated Short-Form Content System',
        add_help=False
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode instead of GUI'
    )
    parser.add_argument(
        '--help', '-h',
        action='store_true',
        help='Show this help message'
    )
    
    # Parse only known args to check for --cli flag
    args, remaining = parser.parse_known_args()
    
    if args.help and not args.cli:
        # Show combined help
        print("ASFS - Automated Short-Form Content System")
        print()
        print("Usage:")
        print("  python main.py              Launch desktop UI (default)")
        print("  python main.py --cli <args> Run in CLI mode")
        print()
        print("GUI Mode (default):")
        print("  Launches the desktop application with graphical interface")
        print()
        print("CLI Mode:")
        print("  python main.py --cli <video_path> [options]")
        print()
        print("  For CLI options, run: python main.py --cli --help")
        print()
        sys.exit(0)
    
    if args.cli:
        # Run in CLI mode
        print("Running in CLI mode...")
        from pipeline import main as cli_main
        
        # Remove --cli from sys.argv and run CLI
        sys.argv.remove('--cli')
        cli_main()
    else:
        # Run GUI mode (default)
        print("Launching desktop UI...")
        from ui.app import run_app
        sys.exit(run_app())


if __name__ == '__main__':
    main()
