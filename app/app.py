"""Main application module."""

import argparse
from typing import NoReturn

from app.download_bazel_site import main as download_main
from app.process_bazel_docs import main as process_main


def main() -> NoReturn:
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="CLI Application")
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download Bazel documentation",
        description="Download Bazel documentation using git sparse checkout",
    )
    download_parser.add_argument(
        "--output-dir",
        type=str,
        default="input/bazel-site",
        help="Output directory for the documentation",
    )

    # Process command
    process_parser = subparsers.add_parser(
        "process",
        help="Process Bazel documentation",
        description="Process downloaded Bazel documentation into markdown files",
    )
    process_parser.add_argument(
        "--input-dir",
        type=str,
        default="input/bazel-site/site/en",
        help="Input directory containing Bazel documentation",
    )
    process_parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/bazel",
        help="Output directory for processed documentation",
    )

    args = parser.parse_args()

    if args.command == "download":
        download_main()
    elif args.command == "process":
        process_main()
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
