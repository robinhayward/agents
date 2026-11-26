#!/usr/bin/env python3
"""Skills, plugins, MCP servers and agents a project's sessions carry, and how often each was used.

Usage: python3 context_inventory.py [project] [--days 30]

"Uses" counts calls in this project's session transcripts from the last
`--days` days: the Skill tool and typed /commands for skills, `mcp__<server>__`
tools for servers, the Agent tool's subagent type for agents. "Tokens" is the
name and description every session carries, at four bytes each; an MCP
server's tool definitions are not on disk, so its cost is not shown.

Zero uses is a question, not a verdict: a skill may be new, or used from
another project. Read SKILL.md, "Unused skills, plugins and servers".
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

from repo import repo_root, tokens

CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
STATE_FILE = (
    CONFIG_DIR / ".claude.json" if "CLAUDE_CONFIG_DIR" in os.environ else Path.home() / ".claude.json"
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)
DESCRIPTION = re.compile(r"^description:(.*?)(?=^[A-Za-z_-]+:|\Z)", re.DOTALL | re.MULTILINE)
NAME = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
COMMAND = re.compile(r"<command-name>/?([\w:.-]+)</command-name>")
SECONDS_PER_DAY = 86400


def read_json(path: Path) -> dict:
    try:
        loaded = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def merged_setting(repo: Path, key: str) -> dict:
    """One settings key across user, project and local settings, later ones winning."""
    sources = [
        CONFIG_DIR / "settings.json",
        repo / ".claude" / "settings.json",
        repo / ".claude" / "settings.local.json",
    ]
    merged: dict = {}
    for source in sources:
        merged.update(read_json(source).get(key) or {})
    return merged


def described(file: Path, fallback: str) -> tuple[str, int]:
    """A definition's name and the size of what every session carries of it."""
    front = FRONTMATTER.match(file.read_text(errors="replace"))
    block = front.group(1) if front else ""
    name = NAME.search(block)
    description = DESCRIPTION.search(block)
    text = description.group(1).strip() if description else ""
    resolved = name.group(1).strip().strip("\"'") if name else fallback
    return resolved, len(resolved.encode()) + len(text.encode())


def skill_files(folder: Path) -> list[Path]:
    return sorted(folder.glob("*/SKILL.md")) + sorted(folder.glob("synced/*/*/SKILL.md"))


def standalone_skills(repo: Path) -> list[dict]:
    places = {"project": repo / ".claude" / "skills", "user": CONFIG_DIR / "skills"}
    rows = []
    for source, folder in places.items():
        for file in skill_files(folder):
            name, size = described(file, file.parent.name)
            origin = "claude.ai" if "synced" in file.parts else source
            rows.append({"kind": "skill", "name": name, "source": origin, "size": size})
    return rows


def plugin_skill_files(plugin: str, marketplace: str) -> dict[str, Path]:
    """A plugin's skills by folder name; the newest cached version wins."""
    cache = CONFIG_DIR / "plugins" / "cache" / marketplace / plugin
    return {file.parent.name: file for file in sorted(cache.rglob("SKILL.md"))}


def plugin_rows(repo: Path) -> list[dict]:
    rows = []
    for key, enabled in sorted(merged_setting(repo, "enabledPlugins").items()):
        plugin, _, marketplace = key.partition("@")
        files = plugin_skill_files(plugin, marketplace).values()
        skills = [described(file, file.parent.name) for file in files]
        rows.append(
            {
                "kind": "plugin",
                "name": plugin,
                "source": marketplace,
                "size": sum(size for _, size in skills),
                "state": "on" if enabled else "off",
                "skills": [name for name, _ in skills],
            }
        )
    return rows


def mcp_rows(repo: Path) -> list[dict]:
    state = read_json(STATE_FILE)
    local = (state.get("projects") or {}).get(str(repo), {}).get("mcpServers") or {}
    scopes = {
        "user": state.get("mcpServers") or {},
        "local": local,
        "project": read_json(repo / ".mcp.json").get("mcpServers") or {},
    }
    return [
        {"kind": "mcp", "name": name, "source": scope, "size": None}
        for scope, servers in scopes.items()
        for name in sorted(servers)
    ]


def agent_rows(repo: Path) -> list[dict]:
    places = {"project": repo / ".claude" / "agents", "user": CONFIG_DIR / "agents"}
    rows = []
    for source, folder in places.items():
        for file in sorted(folder.glob("*.md")):
            name, size = described(file, file.stem)
            rows.append({"kind": "agent", "name": name, "source": source, "size": size})
    return rows


def transcripts(repo: Path, days: int) -> list[Path]:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(repo))
    cutoff = time.time() - days * SECONDS_PER_DAY
    files = (CONFIG_DIR / "projects" / slug).rglob("*.jsonl")
    return [file for file in files if file.stat().st_mtime >= cutoff]


def tool_uses(entry: dict) -> list[dict]:
    content = (entry.get("message") or {}).get("content")
    blocks = content if isinstance(content, list) else []
    return [block for block in blocks if isinstance(block, dict) and block.get("type") == "tool_use"]


def usage_key(call: dict) -> str | None:
    name, given = call.get("name", ""), call.get("input") or {}
    if name == "Skill":
        return f"skill:{given.get('skill', '')}"
    if name == "Agent":
        return f"agent:{given.get('subagent_type', '')}"
    if name.startswith("mcp__"):
        return f"mcp:{name.split('__')[1]}"
    return None


def count_line(line: str, seen: set[str], uses: Counter) -> None:
    for command in COMMAND.findall(line):
        uses[f"skill:{command}"] += 1
    if '"tool_use"' not in line:
        return
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return
    for call in tool_uses(entry):
        key = usage_key(call)
        if key and call.get("id") not in seen:
            seen.add(call.get("id"))
            uses[key] += 1


def usage(repo: Path, days: int) -> tuple[Counter, int]:
    uses: Counter = Counter()
    seen: set[str] = set()
    files = transcripts(repo, days)
    for file in files:
        with file.open(errors="replace") as lines:
            for line in lines:
                count_line(line, seen, uses)
    return uses, len(files)


def normalised(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def uses_of(row: dict, uses: Counter) -> int:
    name = row["name"]
    if row["kind"] == "plugin":
        prefixes = (f"skill:{name}:", f"mcp:plugin_{normalised(name)}_", f"agent:{name}:")
        return sum(count for key, count in uses.items() if key.startswith(prefixes))
    if row["kind"] == "mcp":
        return uses[f"mcp:{normalised(name)}"]
    exact, namespaced = f"{row['kind']}:{name}", f":{name}"
    return sum(count for key, count in uses.items() if key == exact or key.endswith(namespaced))


def state_of(row: dict, overrides: dict) -> str:
    if "state" in row:
        return row["state"]
    return overrides.get(row["name"], "on") if row["kind"] == "skill" else "on"


def line_for(row: dict, uses: Counter, overrides: dict) -> str:
    cost = "?" if row["size"] is None else str(tokens(row["size"]))
    state = state_of(row, overrides)
    return f"{uses_of(row, uses):>5} {cost:>7}  {row['kind']:<7} {state:<20} {row['name']} ({row['source']})"


def report(repo: Path, days: int) -> str:
    uses, sessions = usage(repo, days)
    overrides = merged_setting(repo, "skillOverrides")
    rows = [*plugin_rows(repo), *standalone_skills(repo), *mcp_rows(repo), *agent_rows(repo)]
    rows.sort(key=lambda row: (row["kind"], uses_of(row, uses), row["name"]))
    header = f"{'uses':>5} {'tokens':>7}  {'kind':<7} {'state':<20} name (source)"
    body = [line_for(row, uses, overrides) for row in rows]
    footer = f"\n{sessions} transcripts from the last {days} days for {repo}"
    return "\n".join([header, *body, footer])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    print(report(repo_root(Path(args.project).resolve()), args.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
