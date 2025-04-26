import subprocess
from pathlib import Path
from typing import Optional


def _run_git_command(cmd: list[str], cwd: Optional[Path] = None) -> None:
    """Run a git command and handle errors."""
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.stderr}")
        raise


def _setup_sparse_checkout(repo_path: Path, pattern: str = "docs/*") -> None:
    """Configure git sparse checkout.

    Args:
        repo_path: Path to the repository
        pattern: Sparse checkout pattern, defaults to "docs/*"
    """
    _run_git_command(["git", "config", "core.sparseCheckout", "true"], cwd=repo_path)
    with open(repo_path / ".git" / "info" / "sparse-checkout", "w") as f:
        f.write(f"{pattern}\n")


def _clone_repository(repo_path: Path, repo_url: str, branch: str = "main", sparse_pattern: str = "docs/*") -> None:
    """Clone the repository with sparse checkout."""
    print("Cloning repository")
    _run_git_command(["git", "init"], cwd=repo_path)
    _setup_sparse_checkout(repo_path, sparse_pattern)
    _run_git_command(
        ["git", "remote", "add", "origin", repo_url],
        cwd=repo_path,
    )
    _run_git_command(["git", "fetch", "--depth", "1", "origin", branch], cwd=repo_path)
    _run_git_command(["git", "checkout", branch], cwd=repo_path)
    print("Repository cloned successfully.")


def _update_repository(repo_path: Path, branch: str = "main") -> None:
    """Update the existing repository."""
    print("Updating repository")
    _run_git_command(["git", "fetch", "--depth", "1", "origin", branch], cwd=repo_path)
    _run_git_command(["git", "reset", "--hard", f"origin/{branch}"], cwd=repo_path)
    print("Repository updated successfully.")


def download_repository(repo_path: Path, repo_url: str, branch: str = "main", sparse_pattern: str = "docs/*") -> None:
    """Main function to download or update a repository.

    Args:
        repo_path: Path where the repository should be located
        repo_url: URL of the git repository
        branch: Branch to clone or update, defaults to "main"
        sparse_pattern: Sparse checkout pattern, defaults to "docs/*"
    """
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if not repo_path.exists():
        repo_path.mkdir()
        _clone_repository(repo_path, repo_url, branch, sparse_pattern)
    else:
        _update_repository(repo_path, branch)
