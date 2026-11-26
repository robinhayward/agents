claude() {
  case "$1" in
    fat)
      shift
      command claude "$@"
      ;;
    agents|attach|auth|auto-mode|doctor|gateway|import|install|kill|logs|mcp|plugin|plugins|purge|respawn|rm|setup-token|stop|ultrareview|update|upgrade)
      command claude "$@"
      ;;
    *)
      local chrome=(--no-chrome)
      local arg
      for arg in "$@"; do
        [[ "$arg" == "--chrome" ]] && chrome=()
      done
      local settings
      settings="$(python3 "$CLAUDE_LAUNCH_DIR/lean_settings.py" 2>/dev/null)" || settings="$CLAUDE_LAUNCH_DIR/lean.json"
      command claude --settings "$settings" "${chrome[@]}" "$@"
      ;;
  esac
}
