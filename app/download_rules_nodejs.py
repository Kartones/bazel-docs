import subprocess
from pathlib import Path
from typing import Optional


def run_git_command(cmd: list[str], cwd: Optional[Path] = None) -> None:
    """Run a git command and handle errors."""
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.stderr}")
        raise


def setup_sparse_checkout(repo_path: Path) -> None:
    """Configure git sparse checkout."""
    run_git_command(["git", "config", "core.sparseCheckout", "true"], cwd=repo_path)
    with open(repo_path / ".git" / "info" / "sparse-checkout", "w") as f:
        f.write("docs/*\n")


def clone_repository(repo_path: Path) -> None:
    """Clone the repository with sparse checkout."""
    print("Cloning repository...")
    run_git_command(["git", "init"], cwd=repo_path)
    setup_sparse_checkout(repo_path)
    run_git_command(
        ["git", "remote", "add", "origin", "https://github.com/bazel-contrib/rules_nodejs.git"],
        cwd=repo_path,
    )
    run_git_command(["git", "fetch", "--depth", "1", "origin", "main"], cwd=repo_path)
    run_git_command(["git", "checkout", "main"], cwd=repo_path)
    print("Repository cloned successfully.")


def update_repository(repo_path: Path) -> None:
    """Update the existing repository."""
    print("Updating repository...")
    run_git_command(["git", "fetch", "--depth", "1", "origin", "main"], cwd=repo_path)
    run_git_command(["git", "reset", "--hard", "origin/main"], cwd=repo_path)
    print("Repository updated successfully.")


def main() -> None:
    """Main entry point for the command."""
    repo_path = Path("input/rules-nodejs")
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if not repo_path.exists():
        repo_path.mkdir()
        clone_repository(repo_path)
    else:
        update_repository(repo_path)
