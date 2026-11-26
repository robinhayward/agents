skill := "skills/context-audit"

default:
    @just --list

# Link the context-audit skill into ~/.claude/skills so every project can use it
skill:
    mkdir -p ~/.claude/skills
    ln -sfn "{{justfile_directory()}}/{{skill}}" ~/.claude/skills/context-audit

# Remove the context-audit skill link
skill-uninstall:
    rm -f ~/.claude/skills/context-audit

# Install the `claude` / `claude fat` launcher into your shell profile
launcher:
    python3 {{skill}}/launcher/install.py

# Remove the launcher from your shell profile
launcher-uninstall:
    python3 {{skill}}/launcher/install.py --uninstall

# Run the skill's three audit scripts against a project
audit project=".":
    python3 {{skill}}/scripts/instruction_sizes.py "{{project}}"
    -python3 {{skill}}/scripts/instruction_check.py "{{project}}"
    python3 {{skill}}/scripts/context_inventory.py "{{project}}"
