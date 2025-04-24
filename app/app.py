import argparse

from app.download_bazel_site import main as download_bazel_main
from app.process_bazel_docs import main as process_bazel_main
from app.download_rules_nodejs import main as download_rules_nodejs_main
from app.process_rules_nodejs_docs import main as process_rules_nodejs_docs
from app.cleanup import main as cleanup_main


def main() -> None:
    parser = argparse.ArgumentParser(description="")
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    subparsers.add_parser(
        "download",
        help="Download documentation",
        description="Download all documentation using git sparse checkout",
    )

    subparsers.add_parser(
        "process",
        help="Process documentation",
        description="Process downloaded documentation into markdown files",
    )

    subparsers.add_parser(
        "cleanup",
        help="Delete input folder",
        description="Delete the input folder containing downloaded documentation",
    )

    args = parser.parse_args()

    if args.command == "download":
        download_bazel_main()
        download_rules_nodejs_main()
    elif args.command == "process":
        process_bazel_main()
        process_rules_nodejs_docs()
    elif args.command == "cleanup":
        cleanup_main()
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
