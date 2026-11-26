# Restructuring a project's agent instructions

## How Claude Code loads them

- At session start it loads the user's `~/.claude/CLAUDE.md`, then the project root's `CLAUDE.md` (and `CLAUDE.local.md`), with every `@path` import inside them, in full.
- A root `AGENTS.md` is read on its own only when there is no `CLAUDE.md`. Where both exist, `CLAUDE.md` must contain `@AGENTS.md` or the `AGENTS.md` is never seen. An empty `CLAUDE.md` is the worst case: it loads nothing and hides the other file.
- A `CLAUDE.md` in a subfolder loads lazily, the first time a file in that subtree is read. This is what makes the split below cheap.
- `@path` resolves relative to the file that contains it.

Loading behaviour changes between versions. If a result looks wrong, confirm against the current Claude Code docs before building on it.

## Target layout

| File | Holds | Size |
|---|---|---|
| Root `AGENTS.md` | What the project is in a paragraph; a "where to read" table; the gates; rules that apply to every change in every area | 60 to 100 lines |
| Root `CLAUDE.md` | `@AGENTS.md` and nothing else | 1 line |
| `<area>/AGENTS.md` + `<area>/CLAUDE.md` | Rules for that area only (a language, a framework, a design system) | as short as the area allows |
| `docs/…` | Explanation, architecture, testing method, history | not loaded; pointed at |

Keeping the content in `AGENTS.md` and a one-line `CLAUDE.md` beside it means other agent tools read the same rules.

The test for the root file: would an agent doing *any* task in this repo need this line? If only some tasks need it, it belongs in an area file or a doc.

Replace `@docs/thing.md` imports with a row in the "where to read" table ("Working on X: read `docs/thing.md`"). The agent then reads it when the work calls for it, not in every session.

## Order of work

One commit per step, on a branch.

1. **Baseline.** Run `instruction_sizes.py` and keep the output. Inventory every section of every instruction file: you will account for each one at the end.
2. **Imports become pointers.** Remove `@` imports of documents; add the table.
3. **Move area material out.** Each block that concerns one area goes to that area's `AGENTS.md`, with a `CLAUDE.md` beside it. Where a doc already covers the material, merge into the doc and leave a pointer; do not keep two copies.
4. **Delete what is enforced or recorded elsewhere.** Formatting a formatter owns, a rule a linter fails on, a decision an ADR records. Open the tool's config and confirm it covers the rule; if it only partly does, keep the rule and say what is not enforced.
5. **Verify every reference.** Every path, command, recipe and decision record named in what remains. Fix the ones that moved. List the ones you cannot place.
6. **Add the check** (`instruction_check.py`) to the project's pre-merge gate.
7. **Tighten.** A separate pass, a separate commit: cut filler and repetition from each file without changing what it claims. Do the docs the root file points at as well, since agents now read those on demand.
8. **Run the project's gates,** then measure again.

Only then open the PR. Do not merge it.

## Trimming without rewording

Cut: preamble, restated headings, the same point made twice, examples beyond the first that teaches, history of how a rule came about (unless the history is the reason to obey it), hedges.

Keep: the rule's own nouns and verbs, names of commands and files, the word "binding" or its like, who decided and when if the file records it, the one example that makes the rule concrete, the reason.

If trimming a sentence would change what an agent does on reading it, it was not filler.

## The report

Hand back, in this order:

1. Tokens before and after: every session, and per area.
2. A table of every old section and where it went (or "deleted: enforced by …").
3. Stale items: broken references you fixed, ones you could not place, facts the code contradicts, enforcement that turned out not to exist. These are the user's to decide; do not bury them.
4. The new root file in full.
5. The PR link.

## Decision records

If instructions lean on ADRs or similar, audit those in the same spirit once the instruction files are done: for each record, does the code still do what it says, does a later record contradict it, and is it still cited? Correct the ones that drifted, retire the dead ones (the project's own convention decides whether that means deleting or marking superseded), and fix every citation in the same change so nothing points at a missing record. Ask before deleting a record; a decision the user no longer wants recorded is their call.
