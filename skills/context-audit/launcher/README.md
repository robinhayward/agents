# launch — `claude` lean by default, `claude fat` when you need everything

Claude Code sends the full definition of every always-loaded tool with every request.
Some are large and rarely needed in a coding session — `Artifact` alone is roughly
7–8k tokens — and the skills synced from your claude.ai account (Word, PowerPoint,
Excel, PDF, browser, …) add about 3k more, and Claude in Chrome another 2k. This
launcher wraps the `claude` command so a normal session starts without them, and
`claude fat` starts one with everything.

Measured on a minimal headless request (which never loads `Artifact`, so interactive
sessions save more): fat 18.9k input tokens, lean 12.9k.

| Command | Tools |
|---|---|
| `claude …` | tools and MCP servers in [`lean.json`](lean.json) off, claude.ai skills hidden, Claude in Chrome off |
| `claude fat …` | everything available |
| `claude mcp`, `claude update`, `claude doctor`, … | subcommands run unchanged |

All the usual flags and prompts pass through: `claude --resume`, `claude "fix the bug"`,
`claude fat -c`, and so on. `claude --chrome` gives a lean session with the browser on.

## Install

From the repo root:

```sh
just launcher
source ~/.zshrc
```

The installer ([`install.py`](install.py), Python 3 standard library only):

- picks your profile from `$SHELL` (`~/.zshrc` or `~/.bashrc`; override with `--profile`)
- backs it up to `<profile>.agents-backup-<timestamp>` before changing it
- adds a marked block that points at this checkout — re-running replaces the block,
  so it's safe to repeat, e.g. after moving the repo:

  ```sh
  # >>> agents/launch >>>
  export CLAUDE_LAUNCH_DIR="/path/to/agents/launch"
  source "$CLAUDE_LAUNCH_DIR/claude.zsh"
  # <<< agents/launch <<<
  ```

- warns if `~/.claude/settings.json` already denies any of the same tools. Deny
  rules from every settings source are combined and can't be lifted by a later one,
  so a deny there would also apply to `claude fat`.

Because the profile sources the files from this checkout, a `git pull` updates the
launcher; open a new shell to pick it up.

## Uninstall

```sh
just launcher-uninstall
```

Removes the marked block (after taking a backup). Open a new shell, or run
`unset -f claude`, to drop the function from the current one.

## Check it works

```sh
type claude   # claude is a shell function
```

Compare the real input tokens of a lean and a fat request (see the command under
[Customise](#customise)): `claude -p …` against `claude fat -p …`. The lean one should
be several thousand tokens smaller.

## Customise

[`lean.json`](lean.json) is an ordinary Claude Code settings file, read each time
`claude` starts — no reinstall needed.

- `permissions.deny` — tool names to remove, e.g. `"WebSearch"`, `"NotebookEdit"`.
- `"syncClaudeAiSkills": false` — hides every skill synced from your claude.ai
  account for that session only. Passed through `--settings`, nothing on disk is
  moved or deleted; `claude fat` still sees them. (Put in `~/.claude/settings.json`
  instead, it would trash the synced copies.)
- `"disableClaudeAiConnectors": true` — leaves out the MCP connectors from your
  claude.ai account.
- `deniedMcpServers` — extra MCP servers not to start, e.g. `[{"serverName": "github"}]`.
  You rarely need it: see [MCP servers](#mcp-servers).
- To hide only some synced skills, drop `syncClaudeAiSkills` and use
  `"skillOverrides": {"docx": "user-invocable-only", …}` — the model no longer sees
  the skill, but you can still type `/docx`.

Measure with real API usage rather than `/context`, which moves hidden skills'
tokens into its "System tools" row and shows the same total:

```sh
claude -p "Reply with just: ok" --output-format json | python3 -c 'import sys,json; u=json.load(sys.stdin)["usage"]; print(u["input_tokens"]+u["cache_creation_input_tokens"]+u["cache_read_input_tokens"])'
```

## How it works

[`claude.zsh`](claude.zsh) defines a `claude` shell function that calls the real
binary via `command claude`:

- `fat` is stripped and the remaining arguments are passed straight through.
- Subcommands (`mcp`, `update`, `doctor`, …) are passed straight through. The list
  matches `claude --help` at the time of writing; add new subcommands to it so they
  don't receive `--settings`.
- Everything else gets `--settings` with the JSON from `lean_settings.py` (lean.json
  plus your user-scope MCP servers denied) and `--no-chrome` (left out when you pass
  `--chrome` yourself).

`--settings` is used rather than `--disallowedTools` because the latter takes a
variadic list and would swallow a positional prompt (`claude "fix the bug"`).

## What the denied tools do

- **Artifact** — publishes HTML pages (reports, dashboards, decks) to claude.ai.
- **ScheduleWakeup** — self-paced `/loop` without an interval.
- **SendFeedback** — lets Claude draft Claude Code feedback reports (`/feedback` still works).
- **ListAgents** — lists other Claude sessions to message.

`ReportFindings` (~0.7k) is left in because `/code-review` uses it; add it to the deny
list if you don't run reviews.

## MCP servers

Lean mode doesn't start any MCP server defined at **user** scope (`claude mcp add -s user`,
stored under `mcpServers` in `~/.claude.json`, or `$CLAUDE_CONFIG_DIR/.claude.json`).
Claude Code has no wildcard for this, so [`lean_settings.py`](lean_settings.py) reads
those names each time `claude` starts (~20ms) and adds them to `deniedMcpServers` on
top of `lean.json`. Servers aren't launched at all — not just hidden — and nothing is
named in this repo. If the script fails, `lean.json` is used as is.

Project (`.mcp.json`) and local-scope servers still start: they belong to the project
you're in, like its `CLAUDE.md` and settings. Plugin-provided servers follow the
plugin's enabled state.

## Claude in Chrome

Off in lean mode via `--no-chrome` — it's a command-line flag, not a setting, so it
lives in [`claude.zsh`](claude.zsh) rather than `lean.json`. Its 20 browser tools,
instructions and system-prompt section cost about 2.2k tokens.

## What the hidden skills are

Anthropic's skills enabled on your claude.ai account, synced to
`~/.claude/skills/synced/`: docx, pptx, xlsx, pdf, docs, google-workspace,
built-in-browser, chrome-browser, computer-use, deep-research, import-memory, morning,
skill-creator. Skills you install yourself (`~/.claude/skills/<name>`, plugins) are
unaffected.
