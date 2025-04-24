from pathlib import Path

from typing import List

from app.helpers.process_helpers import cleanup_content


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

    markdown_files = get_markdown_files(subfolder)

    index_file = next((f for f in markdown_files if f.name == "index.md"), None)

    if output_file.exists():
        output_file.unlink()

    if index_file:
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = cleanup_content(content)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

    other_files = [f for f in markdown_files if f.name != "index.md"]
    for file in other_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        content = cleanup_content(content)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write("\n" + content)


def main() -> None:
    """Main entry point for the command."""
    input_dir = Path("input/bazel-site/site/en")
    output_dir = Path("docs/bazel")

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    ensure_directory_exists(output_dir)

    for subfolder in input_dir.iterdir():
        if subfolder.is_dir():
            if subfolder.name in SKIP_FOLDERS:
                print(f"Skipping {subfolder.name}...")
                continue
            print(f"Processing {subfolder.name}...")
            process_subfolder(subfolder, output_dir)

    print("Documentation processing complete.")
