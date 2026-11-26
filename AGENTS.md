# AGENTS.md

This repo is one Claude Code skill, `skills/context-audit/`, and the launcher it
ships with. `just skill` links the skill into `~/.claude/skills`; `just launcher`
installs the launcher.

Everything here is for anyone's machine and any project: never name a particular
person's servers, projects, paths or accounts. Work things out at run time instead
(see `skills/context-audit/launcher/lean_settings.py`).

## context-audit — the skill

- `SKILL.md` is the workflow; `references/` holds what is read only when a job needs
  it; `scripts/` are the three audit scripts. Keep `SKILL.md` short: a lesson that
  applies to one job goes in that job's reference file.
- A lesson earns a place when it came from a real audit and would change what the
  next one does. Write the reason beside the rule.
- Scripts are read-only: they report, and the agent or the user decides. Python 3
  standard library only, and they take the project as an argument, so nothing about
  one project's layout is built in (`--base` covers source roots).
- Test a script change with `just audit <a real project>`.

## launch — `claude` (lean) and `claude fat`

**Purpose:** start Claude Code without everything a session doesn't need, so it
starts faster and doesn't spend tokens on tool definitions, skills and servers that
go unused. `claude fat` starts with everything.

**Lean removes what is global, never what is project-specific.** It strips things that
ride along into every session regardless of where it runs:

- large, rarely used built-in tools (`permissions.deny` in `skills/context-audit/launcher/lean.json`)
- skills and connectors synced from the claude.ai account
- MCP servers defined at user scope
- Claude in Chrome

A project's own Claude Code config still loads in lean mode and takes precedence
for that project: its `CLAUDE.md`, `.claude/settings.json` and
`.claude/settings.local.json`, `.claude/skills/`, and `.mcp.json` / local-scope MCP
servers. When a choice is between a smaller context and the project's own config,
the project wins. Never add a lean option that skips project config (such as
`--setting-sources user` or `--strict-mcp-config`).

The one limit: a project can't switch back on something lean turned off. Deny rules
from every settings source are combined, and `syncClaudeAiSkills: false` or
`disableClaudeAiConnectors: true` can't be undone by another source. A project that
needs one of those uses `claude fat`.

### Working on the launcher

- `skills/context-audit/launcher/README.md` is the user-facing explanation; update it in the same change as
  any behaviour change, including the measured numbers.
- Measure savings with the API's reported input tokens, not `/context`. `/context`
  moves hidden skills' tokens into its "System tools" row and shows an unchanged total:

  ```sh
  claude -p "Reply with just: ok" --output-format json | python3 -c 'import sys,json; u=json.load(sys.stdin)["usage"]; print(u["input_tokens"]+u["cache_creation_input_tokens"]+u["cache_read_input_tokens"])'
  ```

- Test the shell function by sourcing `skills/context-audit/launcher/claude.zsh` with `CLAUDE_LAUNCH_DIR` set.
  Call `claude` directly: `timeout claude …` or `xargs claude …` run the binary and
  bypass the function.
- Test the installer with `--profile <scratch file>`, never the real shell profile.
- Python is standard library only (`python3`); the shell function must work in zsh
  and bash.
- Before adding a setting, check that it exists in the installed Claude Code version
  and that it works through `--settings` (flag scope), which some settings treat
  differently from user settings.
