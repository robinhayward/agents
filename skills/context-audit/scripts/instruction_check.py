#!/usr/bin/env python3
"""References in the agent instructions that no longer resolve. Exit 1 on any.

Usage: python3 instruction_check.py [project] [--base DIR ...]

Reads every AGENTS.md, CLAUDE.md and CLAUDE.local.md in the project, and every
agent, skill and command definition under `.claude/`. It reports:

  MISSING   a backticked path whose first segment is in the project but which
            is not. Checked up to its first placeholder segment (`<name>`,
            `*`, `...`), against the file's own folder, every folder above it
            and each --base (for paths written relative to a source root).
  IMPORT    an `@path` import whose target does not exist.
  LINK      a relative markdown link whose target does not exist.
  UNLOADED  an AGENTS.md beside a CLAUDE.md that does not import it. Claude
            Code reads the CLAUDE.md and stops, so the AGENTS.md never loads.

A route (`/admin/users`) or a command is not a path. A path the project has
never contained is not reported: there is no way to tell it from an example.
"""

import argparse
import re
import sys
from itertools import takewhile
from pathlib import Path

from instruction_sizes import CODE, IMPORT, resolve
from repo import instruction_files, repo_root

DEFINITION_GLOBS = (".claude/agents/*.md", ".claude/skills/*/SKILL.md", ".claude/commands/**/*.md")
BACKTICKED = re.compile(r"`([^`\n]+)`")
PATH = re.compile(r"^[\w.-]+(/[^\s/]+)+/?(:\d+(-\d+)?)?$")
PLACEHOLDER = re.compile(r"[<>*{}$…]|\.\.\.")
LINE_NUMBER = re.compile(r":\d+(-\d+)?$")
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
EXTERNAL = re.compile(r"^([a-z][a-z0-9+.-]*:|/)")


def concrete(token: str) -> str:
    """The path up to its first placeholder segment."""
    segments = LINE_NUMBER.sub("", token).strip("/").split("/")
    return "/".join(takewhile(lambda part: not PLACEHOLDER.search(part), segments))


def cited_paths(text: str) -> list[str]:
    tokens = [token for token in BACKTICKED.findall(text) if PATH.match(token)]
    return sorted({concrete(token) for token in tokens} - {""})


def roots_for(file: Path, repo: Path, bases: list[Path]) -> list[Path]:
    above = [parent for parent in file.parents if parent == repo or parent.is_relative_to(repo)]
    return [*above, *bases]


def is_stale(path: str, roots: list[Path]) -> bool:
    """A path whose first segment is the project's but which is nowhere in it."""
    first = path.split("/")[0]
    known = any((root / first).exists() for root in roots)
    return known and not any((root / path).exists() for root in roots)


def missing_paths(file: Path, text: str, roots: list[Path]) -> list[str]:
    return [f"MISSING   {path}" for path in cited_paths(text) if is_stale(path, roots)]


def broken_imports(file: Path, text: str) -> list[str]:
    targets = IMPORT.findall(CODE.sub("", text))
    return [f"IMPORT    @{target}" for target in targets if not resolve(file, target).exists()]


def broken_links(text: str, roots: list[Path]) -> list[str]:
    """Links that resolve from neither the file's folder nor any folder above it."""
    targets = [target for target in LINK.findall(text) if not EXTERNAL.match(target)]
    lost = [target for target in targets if not any((root / target).exists() for root in roots)]
    return [f"LINK      {target}" for target in sorted(set(lost))]


def unloaded(file: Path, text: str) -> list[str]:
    sibling = file.parent / "AGENTS.md"
    if file.name != "CLAUDE.md" or not sibling.is_file():
        return []
    imports = {resolve(file, target) for target in IMPORT.findall(CODE.sub("", text))}
    return [] if sibling.resolve() in imports else ["UNLOADED  AGENTS.md (not imported here)"]


def checked_files(repo: Path) -> list[Path]:
    definitions = [path for glob in DEFINITION_GLOBS for path in repo.glob(glob)]
    return sorted({*instruction_files(repo), *definitions})


def findings_in(file: Path, repo: Path, bases: list[Path]) -> list[str]:
    text = file.read_text(errors="replace")
    roots = roots_for(file, repo, bases)
    found = [
        *missing_paths(file, text, roots),
        *broken_imports(file, text),
        *broken_links(text, roots),
        *unloaded(file, text),
    ]
    return [f"{file.relative_to(repo)}: {finding}" for finding in found]


def findings(repo: Path, bases: list[Path]) -> list[str]:
    return [line for file in checked_files(repo) for line in findings_in(file, repo, bases)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--base", action="append", default=[], help="extra root, project-relative")
    args = parser.parse_args()
    repo = repo_root(Path(args.project).resolve())
    found = findings(repo, [repo / base for base in args.base])
    print("\n".join(found) or "instruction-check: clean")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
