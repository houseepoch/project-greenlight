"""
Project Greenlight CLI Entry Point.

Usage:
    python -m greenlight server [--host HOST] [--port PORT] [--reload]
    python -m greenlight --help
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Project Greenlight - AI-Powered Cinematic Storyboard Generation"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if args.command == "server":
        from greenlight.api.main import start_server
        print(f"Starting Project Greenlight API server on {args.host}:{args.port}")
        start_server(host=args.host, port=args.port, reload=args.reload)

    elif args.command == "version":
        from greenlight import __version__
        print(f"Project Greenlight v{__version__}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
