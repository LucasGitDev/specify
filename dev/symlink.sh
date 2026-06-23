#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

# CLI symlink
mkdir -p "$HOME/.local/bin"
ln -sfn "$REPO_DIR/.venv/bin/specify" "$HOME/.local/bin/specify"
echo "cli: ~/.local/bin/specify → $REPO_DIR/.venv/bin/specify"

# Skill symlinks em ~/.claude/skills/
mkdir -p "$SKILLS_DIR"
for skill_dir in "$REPO_DIR/skills"/specify.*; do
    skill_name="$(basename "$skill_dir")"
    ln -sfn "$skill_dir" "$SKILLS_DIR/$skill_name"
    echo "skill: ~/.claude/skills/$skill_name → $skill_dir"
done

# Hook SessionStart em settings.json (se ausente)
HOOK_CMD="$REPO_DIR/.venv/bin/python3 $REPO_DIR/src/hooks/session_start.py"
if ! grep -q "session_start.py" "$SETTINGS" 2>/dev/null; then
    python3 - <<PYEOF
import json

with open('$SETTINGS') as f:
    s = json.load(f)

hook = {
    'type': 'command',
    'command': '$HOOK_CMD',
    'timeout': 10,
    'statusMessage': 'Loading specify context...'
}

hooks = s.setdefault('hooks', {}).setdefault('SessionStart', [{}])
if not hooks[0].get('hooks'):
    hooks[0]['hooks'] = []
if not any('session_start.py' in h.get('command','') for h in hooks[0]['hooks']):
    hooks[0]['hooks'].append(hook)

with open('$SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
PYEOF
    echo "hook: SessionStart registrado em settings.json"
else
    echo "hook: já presente em settings.json"
fi

echo ""
echo "specify (dev mode) instalado"
echo "  Reinicie o Claude Code para ativar."
