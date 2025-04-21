"""Script to process rules_nodejs documentation into a single markdown file."""

import argparse
from pathlib import Path
from typing import List

SKIP_FILES = ["BUILD.bazel", "README.md"]


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, create it if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def get_markdown_files(directory: Path) -> List[Path]:
    """Get all markdown files in a directory, excluding files in SKIP_FILES."""
    markdown_files = list(directory.glob("*.md"))
    filtered_files = [f for f in markdown_files if f.name not in SKIP_FILES]
    if len(filtered_files) != len(markdown_files):
        skipped = set(f.name for f in markdown_files) - set(f.name for f in filtered_files)
        print(f"Skipping files: {', '.join(skipped)}")
    return filtered_files


def process_markdown_file(file_path: Path) -> str:
    """Process a single markdown file and return its content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_output_file(output_file: Path, content: str) -> None:
    """Write the processed content to the output file."""
    ensure_directory_exists(output_file.parent)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def process_docs(input_dir: Path, output_file: Path) -> None:
    """Process all markdown files in the docs directory."""
    print(f"Processing documentation from {input_dir}...")

    docs_dir = input_dir / "docs"
    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    markdown_files = get_markdown_files(docs_dir)
    if not markdown_files:
        raise FileNotFoundError(f"No markdown files found in {docs_dir}")

    # Sort files to ensure index.md is first
    markdown_files.sort(key=lambda x: x.name != "index.md")

    # Process all markdown files
    combined_content = []
    for file_path in markdown_files:
        print(f"Processing {file_path.name}...")
        content = process_markdown_file(file_path)
        combined_content.append(content)

    # Write the combined content
    final_content = "\n\n".join(combined_content)
    write_output_file(output_file, final_content)
    print(f"Documentation processed successfully. Output written to {output_file}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Process rules_nodejs documentation")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input/rules-nodejs"),
        help="Input directory containing the documentation",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("docs/rules_nodejs.md"),
        help="Output file path for the processed documentation",
    )
    args = parser.parse_args()

    process_docs(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()