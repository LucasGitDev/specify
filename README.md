# specify

Plugin Claude Code para Spec-Driven Development (SDD) com TDD e Agentic SDLC.

Define o fluxo `plan → sdd → review → close`, persiste memória por projeto via SQLite + busca vetorial, e suporta worktrees isolados para paralelismo.

---

## Instalação

```bash
git clone <repo> ~/projects/specify
cd ~/projects/specify
bash install.sh
```

Verifique que `~/.local/bin` está no PATH:
```bash
specify --help
```

---

## Primeiro uso

```bash
# 1. Inicializar no projeto
cd ~/meu-projeto
specify init

# 2. Editar stack e restrições
$EDITOR .specify/INDEX.md

# 3. Criar spec da task
mkdir -p .specify/tasks/add-healthcheck
$EDITOR .specify/tasks/add-healthcheck/spec.md

# 4. Planejar → implementar → revisar → fechar
/specify plan add-healthcheck
/specify sdd add-healthcheck
/specify review add-healthcheck
/specify close add-healthcheck
```

---

## Comandos CLI

| Comando | O que faz |
|---------|-----------|
| `specify init` | Inicializa `.specify/` no projeto |
| `specify task create/list/update/close` | Gerencia tasks |
| `specify gate run/record/history` | Executa e registra gates de validação |
| `specify memory set/search/list` | Persiste e busca memórias do projeto |
| `specify task create --worktree` | Cria task em worktree isolado |

## Skills

| Skill | Papel |
|-------|-------|
| `/specify plan` | Lê spec, valida, propõe ciclo, gate de aprovação humana |
| `/specify sdd` | RED→GREEN→REFACTOR integrado ao CLI |
| `/specify review` | Adversarial: crítico/importante/sugestão |
| `/specify close` | Gate check + result.md + commit/MR |
| `/specify memory` | Interface de memória com uso proativo |
| `/specify init` | Setup do projeto com orientação |

---

## Requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (instalado automaticamente pelo `install.sh`)
- Claude Code
- Git

---

## Desenvolvimento

```bash
task setup        # criar venv e instalar deps
task test         # testes unitários
task test:e2e     # smoke tests end-to-end
task lint         # ruff check
task dev:install  # instalar em modo dev (symlink)
```
