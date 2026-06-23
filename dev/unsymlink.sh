#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

# Remover CLI symlink
rm -f "$HOME/.local/bin/specify"
echo "cli: removido"

# Remover skill symlinks
for skill_dir in "$REPO_DIR/skills"/specify.*; do
    skill_name="$(basename "$skill_dir")"
    rm -f "$SKILLS_DIR/$skill_name"
    echo "skill: $skill_name removida"
done

# Remover hook de settings.json
python3 - <<PYEOF
import json

with open('$SETTINGS') as f:
    s = json.load(f)

for group in s.get('hooks', {}).get('SessionStart', []):
    group['hooks'] = [
        h for h in group.get('hooks', [])
        if 'session_start.py' not in h.get('command', '')
    ]

with open('$SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
PYEOF
echo "hook: removido de settings.json"

echo ""
echo "specify removido. Venv e repo preservados."
