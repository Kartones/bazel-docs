import re
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set

FULL_LINE_CLEANUPS = [
    "Project: /_project.yaml",
    "Book: /_book.yaml",
    "<!-- Generated with Stardoc: http://skydoc.bazel.build -->",
]

REGEX_LINE_CLEANUPS = [
    r"\{% include.*?%}",
    r"\{% dynamic.*?%}",
    r"\{# .*? #\}",
    r" \{\:#.*?\}",
    r"---\n.*?---\n",
]

REPLACEMENTS: Dict[str, str] = {}


def cleanup_content(content: str) -> str:
    """Clean up content by removing unwanted lines and patterns."""
    for cleanup in FULL_LINE_CLEANUPS:
        content = content.replace(cleanup, "")

    for regex_cleanup in REGEX_LINE_CLEANUPS:
        content = re.sub(regex_cleanup, "", content, flags=re.DOTALL)

    for replacement, replacement_value in REPLACEMENTS.items():
        content = content.replace(replacement, replacement_value)

    prev_content = ""
    while prev_content != content:
        prev_content = content
        content = re.sub(r"\n{3,}", "\n\n", content)

    return content


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, create it if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def get_markdown_files(directory: Path, skip_files: Optional[List[str]] = None) -> List[Path]:
    """Get all markdown files in a directory, excluding files in skip_files."""
    skip_files = skip_files or []
    markdown_files = list(directory.glob("*.md"))
    filtered_files = [f for f in markdown_files if f.name not in skip_files]

    if len(filtered_files) != len(markdown_files):
        skipped = set(f.name for f in markdown_files) - set(f.name for f in filtered_files)
        print(f"Skipping files: {', '.join(skipped)}")

    return filtered_files


def process_markdown_file(file_path: Path, include_filename_as_title: bool = False) -> str:
    """Process a single markdown file and return its content.

    Args:
        file_path: Path to the markdown file
        include_filename_as_title: If True, prepends the filename as a markdown title
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    cleaned_content = cleanup_content(content)

    if include_filename_as_title:
        return f"# {file_path.name}\n{cleaned_content}"
    return cleaned_content


def write_output_file(output_file: Path, content: str) -> None:
    """Write the processed content to the output file."""
    ensure_directory_exists(output_file.parent)
    if output_file.exists():
        output_file.unlink()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def append_to_output_file(output_file: Path, content: str) -> None:
    """Append content to the output file."""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write("\n" + content)


def process_standard_docs(
    input_dir: Path,
    output_file: Path,
    skip_files: Optional[List[str]] = None,
    sort_key: Optional[Callable[[Path], bool]] = None,
    include_filename_as_title: bool = False,
) -> None:
    """Process all markdown files in the docs directory and combine into one file.

    Args:
        input_dir: Directory containing markdown files
        output_file: File to write combined content to
        skip_files: List of filenames to skip
        sort_key: Function to sort files with
        include_filename_as_title: If True, prepends each filename as a markdown title
    """
    print(f"Processing documentation from {input_dir}...")
    skip_files = skip_files or []

    docs_dir = input_dir
    if not docs_dir.exists():
        raise FileNotFoundError(f"Directory not found: {docs_dir}")

    markdown_files = get_markdown_files(docs_dir, skip_files)
    if not markdown_files:
        raise FileNotFoundError(f"No markdown files found in {docs_dir}")

    # Sort files if a sort key is provided
    if sort_key:
        markdown_files.sort(key=sort_key)

    combined_content = []
    for file_path in markdown_files:
        print(f"Processing: {file_path.name}")
        content = process_markdown_file(file_path, include_filename_as_title)
        combined_content.append(content)

    final_content = "\n".join(combined_content)
    write_output_file(output_file, final_content)
    print(f"Documentation processed successfully. Output written to {output_file}")


def process_subfolder_docs(
    input_dir: Path,
    output_dir: Path,
    skip_folders: Optional[Set[str]] = None,
    include_filename_as_title: bool = False,
    combined_filename: Optional[str] = None,
) -> None:
    """Process a directory with subfolders, creating one file per subfolder.

    Args:
        input_dir: Directory containing subdirectories with markdown files
        output_dir: Directory to write output files to
        skip_folders: Set of folder names to skip
        include_filename_as_title: If True, prepends each filename as a markdown title
        combined_filename: If provided, combines all output into a single file with this name
    """
    skip_folders = skip_folders or set()

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return

    ensure_directory_exists(output_dir)

    combined_content = []

    for subfolder in input_dir.iterdir():
        if subfolder.is_dir():
            if subfolder.name in skip_folders:
                print(f"Skipping: {subfolder.name}.")
                continue

            print(f"Processing: {subfolder.name}.")
            folder_content = []

            if include_filename_as_title:
                folder_content.append(f"# {subfolder.name}")

            markdown_files = get_markdown_files(subfolder)

            index_file = next((f for f in markdown_files if f.name == "index.md"), None)
            if index_file:
                content = process_markdown_file(index_file, False)
                folder_content.append(content)

            other_files = [f for f in markdown_files if f.name != "index.md"]
            for file in other_files:
                content = process_markdown_file(file, False)
                folder_content.append(content)

            folder_text = "\n".join(folder_content)

            if combined_filename:
                combined_content.append(folder_text)
            else:
                output_file = output_dir / f"{subfolder.name}.md"
                if output_file.exists():
                    output_file.unlink()
                write_output_file(output_file, folder_text)

    if combined_filename and combined_content:
        combined_output_file = output_dir / combined_filename
        write_output_file(combined_output_file, "\n\n".join(combined_content))

    print("Documentation processing complete.")
