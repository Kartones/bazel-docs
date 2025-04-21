"""Module to process Bazel documentation files."""

import argparse
from pathlib import Path
from typing import List

SKIP_FOLDERS = ["brand", "community", "release", "tutorials", "versions"]


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, create it if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def get_markdown_files(directory: Path) -> List[Path]:
    """Get all markdown files in a directory."""
    return list(directory.glob("*.md"))


def process_subfolder(subfolder: Path, output_dir: Path) -> None:
    """Process a subfolder and create/update its markdown file."""
    output_file = output_dir / f"{subfolder.name}.md"

    # Get all markdown files
    markdown_files = get_markdown_files(subfolder)

    # Find index.md if it exists
    index_file = next((f for f in markdown_files if f.name == "index.md"), None)

    # Process index.md first if it exists
    if index_file:
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

    # Process other markdown files
    other_files = [f for f in markdown_files if f.name != "index.md"]
    for file in other_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)


def main() -> None:
    """Main entry point for the script."""
    # This function is called from app.py, so we don't need to parse arguments here
    input_dir = Path("input/bazel-site/site/en")
    output_dir = Path("docs/bazel")

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    # Ensure output directory exists
    ensure_directory_exists(output_dir)

    # Process each subfolder
    for subfolder in input_dir.iterdir():
        if subfolder.is_dir():
            print(f"Processing {subfolder.name}...")
            process_subfolder(subfolder, output_dir)

    print("Documentation processing complete.")


if __name__ == "__main__":
    # Only parse arguments if running directly
    parser = argparse.ArgumentParser(description="Process Bazel documentation")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input/bazel-site/site/en"),
        help="Input directory containing Bazel documentation",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/bazel"),
        help="Output directory for processed documentation",
    )
    args = parser.parse_args()
    main()
