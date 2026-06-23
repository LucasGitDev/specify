#!/usr/bin/env bash
set -euo pipefail

_green() { printf '\033[32m%s\033[0m\n' "$*"; }
_step()  { printf '\n→ %s\n' "$*"; }

_step "Removendo symlinks..."
rm -f "${HOME}/.local/bin/specify"
rm -rf "${HOME}/.claude/plugins/cache/specify"
_green "symlinks removidos"

_step "Pronto."
printf '\nVenv e repo preservados em ~/projects/specify\n'
printf 'Para remover completamente: rm -rf ~/projects/specify\n\n'
