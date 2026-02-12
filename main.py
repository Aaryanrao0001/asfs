#!/usr/bin/env python3
"""
ASFS - Automated Short-Form Content System

Main entry point for the application.
Launches the web UI by default, or CLI mode with --cli flag.
"""

import sys
import argparse


def main():
    """Main entry point - route to web UI or CLI."""
    parser = argparse.ArgumentParser(
        description='ASFS - Automated Short-Form Content System',
        add_help=False
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode instead of web UI'
    )
    parser.add_argument(
        '--web',
        action='store_true',
        default=False,
        help='Run web server (default mode)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Web server port (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Web server host (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open browser automatically'
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
        print("  python main.py                    Launch web UI (default)")
        print("  python main.py --web [options]    Launch web UI with options")
        print("  python main.py --cli <args>       Run in CLI mode")
        print()
        print("Web UI Mode (default):")
        print("  --port PORT         Port to run server on (default: 5000)")
        print("  --host HOST         Host to bind to (default: 127.0.0.1)")
        print("  --no-browser        Don't open browser automatically")
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
        # Run web UI mode (default)
        print("Launching web UI...")
        from web.server import run_server
        run_server(
            host=args.host,
            port=args.port,
            debug=False,
            open_browser=not args.no_browser
        )


if __name__ == '__main__':
    main()
