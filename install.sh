#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
UV_BIN="${HOME}/.local/bin/uv"
VENV="${REPO_DIR}/.venv"

_green()  { printf '\033[32m%s\033[0m\n' "$*"; }
_yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
_red()    { printf '\033[31m%s\033[0m\n' "$*" >&2; }
_step()   { printf '\n→ %s\n' "$*"; }

# ── 1. uv ────────────────────────────────────────────────────────────────────
_step "Verificando uv..."
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$UV_BIN" ]; then
    _yellow "uv não encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
fi
UV="$(command -v uv 2>/dev/null || echo "$UV_BIN")"
_green "uv: $($UV --version)"

# ── 2. venv + deps ───────────────────────────────────────────────────────────
_step "Configurando ambiente Python..."
if [ ! -d "$VENV" ]; then
    "$UV" venv "$VENV"
fi
"$UV" pip install -e "$REPO_DIR" --quiet
"$UV" pip install pytest pytest-cov ruff --quiet
_green "deps instaladas"

# ── 3. symlinks ──────────────────────────────────────────────────────────────
_step "Instalando symlinks..."
bash "${REPO_DIR}/dev/symlink.sh"

# ── 4. gitignore global ──────────────────────────────────────────────────────
_step "Verificando ~/.gitignore_global..."
GLOBAL_GITIGNORE="${HOME}/.gitignore_global"
if [ -f "$GLOBAL_GITIGNORE" ]; then
    if ! grep -q "\.specify" "$GLOBAL_GITIGNORE"; then
        printf '\n.specify\n' >> "$GLOBAL_GITIGNORE"
        _green ".specify adicionado ao gitignore global"
    else
        _yellow ".specify já presente no gitignore global"
    fi
else
    printf '.specify\n' > "$GLOBAL_GITIGNORE"
    _green "~/.gitignore_global criado com .specify"
fi

# ── 5. PATH hint ─────────────────────────────────────────────────────────────
if ! command -v specify >/dev/null 2>&1; then
    _yellow ""
    _yellow "ATENÇÃO: ~/.local/bin não está no PATH."
    _yellow "Adicione ao ~/.zshrc ou ~/.bashrc:"
    _yellow '  export PATH="$HOME/.local/bin:$PATH"'
    _yellow "Depois recarregue: source ~/.zshrc"
fi

# ── 6. verificação final ──────────────────────────────────────────────────────
printf '\n'
_green "═══════════════════════════════════════"
_green " specify instalado com sucesso!"
_green "═══════════════════════════════════════"
printf '\nPróximo passo:\n'
printf '  specify --help\n'
printf '  cd <projeto> && specify init\n\n'
