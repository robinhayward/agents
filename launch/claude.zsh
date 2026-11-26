# The launcher moved into the context-audit skill. This keeps a shell profile
# installed from the old location working; re-run `just launcher` to point the
# profile at the new one, after which this file is no longer read.
CLAUDE_LAUNCH_DIR="${CLAUDE_LAUNCH_DIR%/launch}/skills/context-audit/launcher"
source "$CLAUDE_LAUNCH_DIR/claude.zsh"
