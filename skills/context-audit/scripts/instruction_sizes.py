#!/usr/bin/env python3
"""What the instruction files cost: loaded in every session, and added per folder.

Usage: python3 instruction_sizes.py [project]   (default: the current directory)

"Every session" is the user's own CLAUDE.md, the project root's instruction
files and everything they @-import. Each nested folder is then listed with what
working in it adds on top. Tokens are estimated at four bytes each; for a real
figure, compare API input tokens before and after (see SKILL.md, "Measure").
"""

import re
import sys
from pathlib import Path

from repo import INSTRUCTION_NAMES, instruction_files, repo_root, tokens

IMPORT = re.compile(r"(?:^|\s)@((?:~/|\.{0,2}/)?[\w.-]+(?:/[\w.-]+)*\.\w+)")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
USER_FILE = Path.home() / ".claude" / "CLAUDE.md"


def import_targets(file: Path) -> list[Path]:
    text = CODE.sub("", file.read_text(errors="replace"))
    return [resolve(file, target) for target in IMPORT.findall(text)]


def resolve(file: Path, target: str) -> Path:
    if target.startswith("~/"):
        return Path(target).expanduser()
    return (file.parent / target).resolve()


def with_imports(file: Path, seen: list[Path]) -> list[Path]:
    """The file and everything it imports, each once, in reading order."""
    if file in seen or not file.is_file():
        return seen
    seen.append(file)
    for target in import_targets(file):
        with_imports(target, seen)
    return seen


def loaded_from(files: list[Path], already: list[Path]) -> list[Path]:
    seen = list(already)
    for file in files:
        with_imports(file, seen)
    return seen[len(already) :]


def label(file: Path, repo: Path) -> str:
    if file.is_relative_to(repo):
        return str(file.relative_to(repo))
    return str(file).replace(str(Path.home()), "~", 1)


def section(title: str, files: list[Path], repo: Path) -> list[str]:
    total = sum(file.stat().st_size for file in files)
    rows = [f"  {file.stat().st_size:>8}  {label(file, repo)}" for file in files]
    return [f"{title}: {total} bytes, about {tokens(total)} tokens", *rows, ""]


def nested_folders(repo: Path) -> list[Path]:
    folders = {file.parent for file in instruction_files(repo)}
    return sorted(folders - {repo})


def report(repo: Path) -> str:
    root_files = [repo / name for name in INSTRUCTION_NAMES]
    always = loaded_from([USER_FILE, *root_files], [])
    lines = section("Every session", always, repo)
    for folder in nested_folders(repo):
        added = loaded_from([folder / name for name in INSTRUCTION_NAMES], always)
        lines += section(f"Working in {folder.relative_to(repo)}/ adds", added, repo)
    return "\n".join(lines).rstrip()


def main() -> int:
    start = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(report(repo_root(start)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
