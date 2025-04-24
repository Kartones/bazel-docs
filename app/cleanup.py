import shutil
from pathlib import Path


def main() -> None:
    """Delete the input folder containing downloaded documentation."""
    input_dir = Path("input")
    if input_dir.exists() and input_dir.is_dir():
        shutil.rmtree(input_dir)
        print(f"Deleted {input_dir} directory")
    else:
        print(f"{input_dir} directory does not exist")
