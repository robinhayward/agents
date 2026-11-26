"""The project being audited: its root and its instruction files."""

import subprocess
from pathlib import Path

INSTRUCTION_NAMES = ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md")
INSTRUCTION_GLOBS = ("*AGENTS.md", "*CLAUDE.md", "*CLAUDE.local.md")
BYTES_PER_TOKEN = 4


def git_lines(repo: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return result.stdout.splitlines()


def repo_root(start: Path) -> Path:
    """The git root above `start`, or `start` itself outside a repository."""
    top = git_lines(start, "rev-parse", "--show-toplevel")
    return Path(top[0]) if top else start.resolve()


def instruction_files(repo: Path) -> list[Path]:
    """Every instruction file git tracks or would track, plus local ones on disk."""
    listed = git_lines(
        repo, "ls-files", "--cached", "--others", "--exclude-standard", "--", *INSTRUCTION_GLOBS
    )
    local = [path for name in INSTRUCTION_NAMES for path in [repo / name] if path.is_file()]
    files = {repo / line for line in listed} | set(local)
    return sorted(file for file in files if file.is_file())


def tokens(size: int) -> int:
    return size // BYTES_PER_TOKEN
