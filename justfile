default:
    @just --list

# Install the `claude` / `claude fat` launcher into your shell profile
launcher:
    python3 launch/install.py

# Remove the launcher from your shell profile
launcher-uninstall:
    python3 launch/install.py --uninstall
