"""Main application module."""

import argparse
from pathlib import Path

from app.download_bazel_site import main as download_bazel_main
from app.process_bazel_docs import main as process_bazel_main
from app.download_rules_nodejs import main as download_rules_nodejs_main
from app.process_rules_nodejs_docs import main as process_rules_nodejs_main


def main() -> None:
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="CLI Application")
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download documentation",
        description="Download Bazel and rules_nodejs documentation using git sparse checkout",
    )
    download_parser.add_argument(
        "--bazel-output-dir",
        type=str,
        default="input/bazel-site",
        help="Output directory for Bazel documentation",
    )
    download_parser.add_argument(
        "--rules-nodejs-output-dir",
        type=str,
        default="input/rules-nodejs",
        help="Output directory for rules_nodejs documentation",
    )

    # Process command
    process_parser = subparsers.add_parser(
        "process",
        help="Process documentation",
        description="Process downloaded documentation into markdown files",
    )
    process_parser.add_argument(
        "--bazel-input-dir",
        type=str,
        default="input/bazel-site/site/en",
        help="Input directory containing Bazel documentation",
    )
    process_parser.add_argument(
        "--bazel-output-dir",
        type=str,
        default="docs/bazel",
        help="Output directory for processed Bazel documentation",
    )
    process_parser.add_argument(
        "--rules-nodejs-input-dir",
        type=str,
        default="input/rules-nodejs",
        help="Input directory containing rules_nodejs documentation",
    )
    process_parser.add_argument(
        "--rules-nodejs-output-file",
        type=str,
        default="docs/rules_nodejs.md",
        help="Output file for processed rules_nodejs documentation",
    )

    args = parser.parse_args()

    if args.command == "download":
        download_bazel_main()
        download_rules_nodejs_main()
    elif args.command == "process":
        # Process Bazel docs
        process_bazel_main()
        # Process rules_nodejs docs
        from app.process_rules_nodejs_docs import process_docs
        process_docs(
            input_dir=Path(args.rules_nodejs_input_dir),
            output_file=Path(args.rules_nodejs_output_file),
        )
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
