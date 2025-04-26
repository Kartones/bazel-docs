import argparse
from pathlib import Path

from app.cleanup import main as cleanup_main
from app.helpers.download_helpers import download_repository
from app.helpers.process_helpers import process_standard_docs, process_subfolder_docs


REPOSITORIES = {
    "bazel-site": {
        "path": "input/bazel-site",
        "url": "https://github.com/bazelbuild/bazel.git",
        "branch": "master",
        "sparse_pattern": "site/en/*",
    },
    "rules-nodejs": {
        "path": "input/rules-nodejs",
        "url": "https://github.com/bazel-contrib/rules_nodejs.git",
        "branch": "main",
        "sparse_pattern": "docs/*",
    },
    "rules-js": {
        "path": "input/rules-js",
        "url": "git@github.com:aspect-build/rules_js.git",
        "branch": "main",
        "sparse_pattern": "docs/*",
    },
    "rules-ts": {
        "path": "input/rules-ts",
        "url": "git@github.com:aspect-build/rules_ts.git",
        "branch": "main",
        "sparse_pattern": "docs/*",
    },
    "bazel-lib": {
        "path": "input/bazel-lib",
        "url": "git@github.com:bazel-contrib/bazel-lib.git",
        "branch": "main",
        "sparse_pattern": "docs/*",
    },
    "starlark": {
        "path": "input/starlark",
        "url": "git@github.com:bazelbuild/starlark.git",
        "branch": "master",
        "sparse_pattern": "*",
    },
}


def _download_all() -> None:
    """Download all documentation repositories."""
    for repo_name, config in REPOSITORIES.items():
        print(f"Downloading: {repo_name}")
        download_repository(Path(config["path"]), config["url"], config["branch"], config["sparse_pattern"])


def _process_all() -> None:
    """Process all documentation repositories."""
    print("Processing: bazel-site")
    process_subfolder_docs(
        input_dir=Path("input/bazel-site/site/en"),
        output_dir=Path("docs"),
        skip_folders={"about", "brand", "community", "contribute", "migrate", "release", "tutorials", "versions"},
        include_filename_as_title=True,
        combined_filename="bazel.md",
    )

    print("Processing: rules-nodejs")
    process_standard_docs(
        input_dir=Path("input/rules-nodejs/docs"),
        output_file=Path("docs/rules_nodejs.md"),
        skip_files=["README.md"],
        sort_key=lambda x: x.name != "index.md",
    )

    print("Processing: rules-js")
    process_standard_docs(
        input_dir=Path("input/rules-js/docs"),
        output_file=Path("docs/rules_js.md"),
        skip_files=["README.md"],
        sort_key=lambda x: x.name != "index.md",
        include_filename_as_title=True,
    )

    print("Processing: rules-ts")
    process_standard_docs(
        input_dir=Path("input/rules-ts/docs"),
        output_file=Path("docs/rules_ts.md"),
        skip_files=[],
        sort_key=lambda x: x.name != "index.md",
        include_filename_as_title=True,
    )

    print("Processing: bazel-lib")
    process_standard_docs(
        input_dir=Path("input/bazel-lib/docs"),
        output_file=Path("docs/bazel_lib.md"),
        skip_files=[],
        sort_key=lambda x: x.name != "index.md",
        include_filename_as_title=True,
    )

    print("Processing: Starlark")
    process_standard_docs(
        input_dir=Path("input/starlark"),
        output_file=Path("docs/starlark.md"),
        skip_files=["CONTRIBUTING.md", "README.md", "users.md"],
        sort_key=lambda x: x.name != "index.md",
        include_filename_as_title=True,
    )


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
        _download_all()
    elif args.command == "process":
        _process_all()
    elif args.command == "cleanup":
        cleanup_main()
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
