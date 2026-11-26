# agents

A Claude Code skill, `context-audit`, that keeps a project's agent instructions small and true, and the `claude` launcher it ships with.

Recipes are run with [`just`](https://github.com/casey/just); `just` on its own lists them.

| What | What it does | Install |
|---|---|---|
| [context-audit](skills/context-audit/) | Measures what a project loads into every session, finds stale facts and broken paths and imports in `AGENTS.md` / `CLAUDE.md`, restructures them so less loads, and lists skills, plugins and MCP servers nobody uses | `just skill` |
| [launcher](skills/context-audit/launcher/) | `claude` starts lean (large, rarely used tools denied); `claude fat` starts with everything | `just launcher` |

After `just skill`, ask Claude in any project to "audit the agent instructions", or run the scripts alone with `just audit <project>`.
