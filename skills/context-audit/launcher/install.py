#!/usr/bin/env python3
"""Install or remove the `claude` / `claude fat` launcher in the user's shell profile."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

LAUNCH_DIR = Path(__file__).resolve().parent
FUNCTION_FILE = LAUNCH_DIR / "claude.zsh"
LEAN_SETTINGS = LAUNCH_DIR / "lean.json"
LEAN_BUILDER = LAUNCH_DIR / "lean_settings.py"
USER_SETTINGS = Path.home() / ".claude" / "settings.json"

BEGIN = "# >>> agents/launch >>>"
END = "# <<< agents/launch <<<"

PROFILES = {
    "zsh": Path.home() / ".zshrc",
    "bash": Path.home() / ".bashrc",
}


def detect_profile() -> Path:
    shell = Path(os.environ.get("SHELL", "")).name
    if shell not in PROFILES:
        sys.exit(f"Unsupported shell '{shell or 'unknown'}'. Supported: {', '.join(PROFILES)}.")
    return PROFILES[shell]


def block() -> str:
    return "\n".join(
        [
            BEGIN,
            f'export CLAUDE_LAUNCH_DIR="{LAUNCH_DIR}"',
            'source "$CLAUDE_LAUNCH_DIR/claude.zsh"',
            END,
        ]
    )


def strip_block(text: str) -> tuple[str, bool]:
    start = text.find(BEGIN)
    if start == -1:
        return text, False
    end = text.find(END, start)
    if end == -1:
        sys.exit(f"Found '{BEGIN}' without a matching '{END}'. Fix the profile by hand and re-run.")
    end += len(END)
    parts = [p for p in (text[:start].rstrip("\n"), text[end:].strip("\n")) if p]
    return ("\n\n".join(parts) + "\n") if parts else "", True


def backup(profile: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = profile.with_name(f"{profile.name}.agents-backup-{stamp}")
    shutil.copy2(profile, target)
    return target


def lean_denies() -> set[str]:
    return set(json.loads(LEAN_SETTINGS.read_text())["permissions"]["deny"])


def conflicting_user_denies() -> set[str]:
    if not USER_SETTINGS.exists():
        return set()
    try:
        settings = json.loads(USER_SETTINGS.read_text())
    except json.JSONDecodeError:
        print(f"! Could not parse {USER_SETTINGS}; skipped the deny check.")
        return set()
    denies = set(settings.get("permissions", {}).get("deny", []))
    return denies & lean_denies()


def install(profile: Path) -> None:
    for required in (FUNCTION_FILE, LEAN_SETTINGS, LEAN_BUILDER):
        if not required.exists():
            sys.exit(f"Missing {required}; run from a complete checkout.")
    if shutil.which("claude") is None:
        print("! `claude` is not on your PATH; the launcher wraps it, so install Claude Code first.")

    original = profile.read_text() if profile.exists() else ""
    text, replaced = strip_block(original)
    updated = text.rstrip("\n") + ("\n\n" if text.strip() else "") + block() + "\n"

    if updated == original:
        print(f"✓ Already installed in {profile}; nothing to change.")
    else:
        if profile.exists():
            print(f"  Backed up {profile} to {backup(profile)}")
        profile.write_text(updated)
        print(f"✓ {'Updated' if replaced else 'Installed'} launcher in {profile}")

    conflicts = conflicting_user_denies()
    if conflicts:
        names = ", ".join(sorted(conflicts))
        print(
            f"\n! {USER_SETTINGS} denies {names}.\n"
            "  Deny rules from every settings source are combined, so `claude fat` would still\n"
            "  have these blocked. Remove them from permissions.deny there to get them back in fat mode."
        )

    print(
        f"\nNext:\n"
        f"  source {profile}\n"
        f"  type claude        # should say 'claude is a shell function'\n"
        f"  claude             # lean: {', '.join(sorted(lean_denies()))} denied\n"
        f"  claude fat         # every tool available\n"
        f"Compare 'System tools' in /context between the two."
    )


def uninstall(profile: Path) -> None:
    if not profile.exists():
        print(f"✓ {profile} does not exist; nothing to remove.")
        return
    original = profile.read_text()
    text, found = strip_block(original)
    if not found:
        print(f"✓ Launcher not found in {profile}; nothing to remove.")
        return
    print(f"  Backed up {profile} to {backup(profile)}")
    profile.write_text(text)
    print(f"✓ Removed launcher from {profile}. Open a new shell (or `unset -f claude`) to finish.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uninstall", action="store_true", help="remove the launcher from your shell profile")
    parser.add_argument("--profile", type=Path, help="shell profile to edit (default: from $SHELL)")
    args = parser.parse_args()

    profile = (args.profile or detect_profile()).expanduser()
    (uninstall if args.uninstall else install)(profile)


if __name__ == "__main__":
    main()
