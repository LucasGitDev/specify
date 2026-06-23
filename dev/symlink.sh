#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_CACHE="$HOME/.claude/plugins/cache/specify/specify/dev"

# Plugin symlink
mkdir -p "$PLUGIN_CACHE"
ln -sfn "$REPO_DIR" "$PLUGIN_CACHE/plugin"

# CLI symlink
mkdir -p "$HOME/.local/bin"
ln -sfn "$REPO_DIR/.venv/bin/specify" "$HOME/.local/bin/specify"

echo "specify (dev mode)"
echo "  plugin: $PLUGIN_CACHE/plugin → $REPO_DIR"
echo "  cli:    ~/.local/bin/specify → $REPO_DIR/.venv/bin/specify"
