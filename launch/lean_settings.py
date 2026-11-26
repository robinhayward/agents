#!/usr/bin/env python3
"""Print lean.json with every user-scope MCP server added to deniedMcpServers."""

import json
import os
import sys
from pathlib import Path

LEAN_SETTINGS = Path(__file__).resolve().parent / "lean.json"


def claude_config() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir).expanduser() / ".claude.json"
    return Path.home() / ".claude.json"


def user_mcp_servers() -> list[str]:
    try:
        config = json.loads(claude_config().read_text())
    except (OSError, json.JSONDecodeError):
        return []
    servers = config.get("mcpServers")
    return sorted(servers) if isinstance(servers, dict) else []


def lean_settings() -> dict:
    settings = json.loads(LEAN_SETTINGS.read_text())
    denied = settings.setdefault("deniedMcpServers", [])
    already = {entry.get("serverName") for entry in denied}
    denied.extend({"serverName": name} for name in user_mcp_servers() if name not in already)
    if not denied:
        del settings["deniedMcpServers"]
    return settings


def main() -> None:
    json.dump(lean_settings(), sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
