---
name: context-audit
description: Audit and slim what a project loads into every Claude Code session - AGENTS.md and CLAUDE.md files, their @-imports, and the skills, plugins, MCP servers and agents that ride along. Use when the user asks to clean up, restructure, trim or shrink agent instructions; says sessions start heavy or context fills fast; asks whether AGENTS.md / CLAUDE.md is out of date, bloated or has broken paths or imports; asks which skills, plugins or MCP servers are unused or what they cost; wants per-project settings for skills and plugins; wants a lean `claude` launcher installed; or asks for the regular instruction health check on a project that has had one before.
---

# Context audit

Everything in a project's instruction files is paid for in every session and competes with the task for the model's attention. Instructions also rot: paths move, decisions are reversed, and a file that is half wrong teaches agents to distrust all of it. This skill measures what a project loads, finds what is stale or broken, and restructures it so that less loads and what loads is true.

It has four jobs. Work out which the user wants; a first run on a project is usually 1 then 2, a repeat run is 1 alone.

| Job | When | Changes files? |
|---|---|---|
| 1. Audit | Always first, and on its own as the regular check | No |
| 2. Restructure | First time, or when the audit shows the root file has grown | Yes, on a branch |
| 3. Trim the extras | The inventory shows skills, plugins or servers nobody uses | Project settings only, with the user's yes |
| 4. Install the launcher | The user wants lean sessions on their own machine | Their shell profile, with their yes |

The scripts are Python 3, standard library only. Run them by path from the project being audited; `<skill>` below is this skill's folder.

## 1. Audit

Run all three and read the output before saying anything:

```sh
python3 <skill>/scripts/instruction_sizes.py      # what loads, and what each folder adds
python3 <skill>/scripts/instruction_check.py      # broken paths, imports and links; exit 1 on any
python3 <skill>/scripts/context_inventory.py      # skills, plugins, MCP servers, agents and their use
```

Then do the part no script can: **check the facts.** A path that exists can still sit in a sentence that is no longer true. Read each instruction file and, for every claim about how the project works (a command, a layer rule, "X is enforced by Y", "we never do Z", a count, a name), confirm it against the code or config. For a large project, give read-only subagents one area each and ask for claims that the code contradicts, with the file and line that contradicts them; then verify each finding yourself before reporting it, because an agent's report of a contradiction is a lead, not a fact.

Things that have turned out to be wrong in real audits, worth looking for by name:

- A rule said to be enforced by a linter, a boundary check or CI, where the tool's config does not cover it. Read the config; do not take the instruction's word.
- A `CLAUDE.md` that is empty or does not import the `AGENTS.md` beside it. Claude Code reads the `CLAUDE.md` and never loads the other (the check reports this as `UNLOADED`).
- A big document pulled in with `@path`. Imports load in full, at session start, whether or not the task needs them.
- Decision records that contradict each other or the code, and instructions that still cite the losing one.
- Hooks, agent definitions and skills under `.claude/` that name folders which have moved.
- A rule that cites something only one person has (a private memory file, a chat).
- The same rule in two files, in slightly different words.
- A plugin that writes into the repo by default (plans, specs) and so keeps recreating a folder the project deleted.

Report the audit as: the size table; the broken references; the stale facts, each with its evidence; the unused extras; and what you would change, in order of tokens saved. Change nothing yet unless the user asked for the fix as well.

### Measure

The size script estimates at four bytes a token, which is good for comparing before and after. `/context` is not: it moves hidden skills' tokens into another row and shows the same total. For a real figure compare the API's reported input tokens in a fresh headless session, before and after the change:

```sh
claude -p "Reply with just: ok" --output-format json
```

and add `input_tokens`, `cache_creation_input_tokens` and `cache_read_input_tokens` from `usage`.

## 2. Restructure

Read `references/restructuring.md` before starting: it holds the target layout, the order of work and the report to hand back. The rules that matter most, and why:

- **Move, don't lose.** Every rule in the old files ends up somewhere, or is listed as deliberately dropped with the reason. A rule's author cannot review what silently vanished.
- **Never quietly delete a rule because its reference is broken.** A dead path usually means the thing moved, not that the rule died. Find where it went; if you cannot, list it for the user.
- **Do not reword beyond trimming.** Wording in an instruction file is often the scar of a past mistake. Cut filler; keep the claim, the names and the emphasis.
- **One copy of each rule.** When a doc already covers something, merge into it and point at it. Two copies drift.
- **Drop only what is truly enforced or recorded elsewhere,** and say where. Confirm the enforcement first.
- **A branch, one commit per step, one PR, not merged.** The user reviews a restructure by reading it move by move.

## 3. Unused skills, plugins and servers

The inventory lists everything a session in this project carries with its use over the last 30 days (`--days` to change). Read it with care:

- Zero uses is a question for the user, not a verdict. The skill may be new, used only in another project, or kept for a rare job. Ask about the expensive zero-use rows first.
- A plugin's cost is the sum of its skills' descriptions. One plugin can cost more than the whole root instruction file.
- An MCP server's cost is its tool definitions, which are not on disk, so the script shows `?`. Compare measured tokens with and without it if it matters.
- The count covers this project's transcripts only.

Switch things off **for the project**, in `.claude/settings.json`, so the choice is shared and other projects are untouched. `references/settings.md` lists the settings, which scope each belongs in, and the two traps (deny rules cannot be undone by another scope; some settings behave differently in user settings). Check a setting exists in the installed Claude Code version before writing it. Propose the diff and wait for a yes; never edit the user's own `~/.claude/settings.json` without being asked.

## 4. The launcher

`launcher/` is a shell wrapper that makes plain `claude` start lean (large rarely used tools, account-synced skills, user-scope MCP servers and Claude in Chrome off) and `claude fat` start with everything. It strips only what is global; a project's own config always loads. `launcher/README.md` explains it and how to customise it.

Offer it when the audit shows the weight is coming from the user's machine and not the project. Installing edits their shell profile, so ask first, then:

```sh
python3 <skill>/launcher/install.py              # backs the profile up, adds a marked block
python3 <skill>/launcher/install.py --uninstall
```

## Keeping it true

After a restructure, make the check part of the project so the instructions cannot rot unnoticed: copy or call `scripts/instruction_check.py` from whatever the project already runs before merging (a `just` recipe, a `make` target, a pre-commit hook, a CI step), with a `--base` for each source root that instructions write paths relative to. Follow the project's own conventions for where scripts live.

The script catches broken references. Stale facts need the reading pass in job 1, so suggest the user re-run this skill after any large refactor and otherwise every few weeks; on a repeat run, compare the size table with the last report and say what grew.
