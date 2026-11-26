# Settings that decide what a session carries

Settings change between Claude Code versions. Before writing one, confirm it exists in the installed version (the settings docs, or the `claude-code-guide` agent where available).

## Scopes

| File | Scope | Shared? |
|---|---|---|
| `~/.claude/settings.json` | every project on this machine | no |
| `<project>/.claude/settings.json` | this project | yes, committed |
| `<project>/.claude/settings.local.json` | this project, this person | no, gitignored |
| `--settings <json or file>` | one session | no |

Prefer the project file for anything true of the project ("this repo has no Swift, so the Swift skills are off"). It travels with the repo and leaves other projects alone.

## What to set

- **A whole plugin off for this project:**

  ```json
  "enabledPlugins": { "<plugin>@<marketplace>": false }
  ```

  The key is the one shown in the user's settings where the plugin is enabled.

- **One skill off, or hidden from the model but still typed by hand:**

  ```json
  "skillOverrides": { "<skill>": "off" }
  "skillOverrides": { "<skill>": "user-invocable-only" }
  ```

- **An MCP server not started:**

  ```json
  "deniedMcpServers": [{ "serverName": "<name>" }]
  ```

  A project's own servers live in `.mcp.json`; removing one there is cleaner than denying it.

- **A built-in tool removed:** `"permissions": { "deny": ["<ToolName>"] }`.

- **Account-synced skills and connectors** (`syncClaudeAiSkills`, `disableClaudeAiConnectors`): per-session only, through the launcher. See below.

## Traps

- **Deny rules combine and cannot be lifted.** `permissions.deny` from every scope is merged; no other scope can re-allow a denied tool. The same holds for `syncClaudeAiSkills: false` and `disableClaudeAiConnectors: true`. So put a deny in the narrowest scope that needs it, and never in user settings unless it should hold everywhere.
- **`syncClaudeAiSkills: false` in user settings removes the synced copies from disk.** Passed with `--settings` it only hides them for that session. This is why the launcher passes it per session.
- **A hook or plugin can add context too.** A `SessionStart` hook that prints a long preamble costs tokens in every session and does not show up as an instruction file. Read the project's and the user's hooks when the measured total is larger than the files explain.

## Checking the result

Start a fresh session and measure (SKILL.md, "Measure"). A setting that is spelled wrong is ignored silently, so an unchanged token count means it did not take.
