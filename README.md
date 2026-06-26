<h1 align="center">specify</h1>

<p align="center">
  <strong>spec primeiro. código depois. sempre.</strong>
</p>

<p align="center">
  <a href="https://github.com/LucasGitDev/specify/actions/workflows/ci.yml">
    <img src="https://github.com/LucasGitDev/specify/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/LucasGitDev/specify/actions/workflows/ci.yml">
    <img src="badges/coverage.svg" alt="Coverage">
  </a>
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/claude--code-plugin-orange" alt="Claude Code plugin">
</p>

---

Plugin [Claude Code](https://claude.ai/code) que implementa **Spec-Driven Development (SDD)** com TDD e Agentic SDLC como um fluxo coeso — do planejamento ao merge, com estado persistente por projeto.

**→ [Como funciona em detalhe](docs/how-it-works.md)**

## Por que

Agentes de IA são rápidos mas propensos a drift: começam a implementar antes de entender o problema, perdem contexto entre sessões, e entregam código que passa nos testes mas não atende ao requisito real.

**specify força o fluxo correto:**

```
sem specify                          com specify
─────────────────────────────────    ─────────────────────────────────────────
"implementa autenticação JWT"    →   spec escrita e aprovada
  → agent escreve código             → interface definida antes do código
  → código não cobre edge cases      → testes escritos e falhando (RED)
  → revisão manual descobre gaps     → implementação mínima (GREEN)
  → retrabalho                       → lint + fmt validados (REFACTOR)
                                     → review adversarial contra a spec
                                     → gates verificados antes do merge
```

Não é sobre ter um agente mais inteligente. É sobre um processo que não deixa o agente improvisar onde não deve.

## Como funciona

**Um ciclo por task, sem pular etapas:**

```
/specify.plan <slug>    →  lê spec, valida critérios, propõe ciclo
                            gate: sua aprovação antes de qualquer código

/specify.sdd <slug>     →  RED  (escreve testes, verifica falha)
                            GREEN (implementação mínima, max 3 tentativas)
                            REFACTOR (lint + fmt + re-run tests)

/specify.review <slug>  →  adversarial: tenta refutar contra a spec
                            crítico / importante / sugestão
                            gate: zero críticos antes de avançar

/specify.close <slug>   →  verifica todos os gates
                            gera result.md, fecha task, commit + MR
```

**O estado persiste entre sessões** via SQLite em `.specify/specify.db` — tasks, gates, histórico de iterações, e memória vetorial do projeto (busca semântica com fastembed ONNX).

**O hook `SessionStart`** injeta automaticamente o contexto do projeto — stack, tasks ativas, memórias recentes — sem você precisar pedir nada.

## Instalação

**Requisitos:** Python 3.12+, Claude Code, Git.

```bash
git clone https://github.com/LucasGitDev/specify.git ~/projects/specify
cd ~/projects/specify
bash install.sh
```

`install.sh` instala [uv](https://github.com/astral-sh/uv) se ausente, cria o venv, registra as skills e o hook. Sem sudo. Reinicie o Claude Code depois.

```bash
specify --help   # verifica instalação
```

## Primeiro uso

### 1. Inicializar no projeto

```bash
cd ~/meu-projeto
specify init
```

Cria `.specify/` com banco de dados e `INDEX.md` com a stack detectada automaticamente.

### 2. Preencher o INDEX.md

```bash
$EDITOR .specify/INDEX.md
```

Adicione arquitetura e restrições reais do projeto. Esse arquivo é o contexto injetado em toda sessão.

### 3. Criar a spec e executar o fluxo

Se não tem spec escrita, use `/specify.new` — ele entrevista e escreve por você:

```
/specify.new add-healthcheck
```

Com a spec pronta:

```
/specify.plan add-healthcheck
/specify.sdd add-healthcheck
/specify.review add-healthcheck
/specify.close add-healthcheck
```

## Skills

| Skill | Quando usar |
|-------|-------------|
| `/specify.init` | Configurar specify num projeto novo |
| `/specify.new` | Criar spec de task do zero — entrevista guiada |
| `/specify.plan` | Spec pronta — valida, propõe ciclo, aguarda aprovação |
| `/specify.sdd` | Implementar: RED→GREEN→REFACTOR com gates automáticos |
| `/specify.review` | Revisar adversarialmente antes do merge |
| `/specify.close` | Gate final, result.md, commit, MR |
| `/specify.memory` | Salvar e buscar decisões e padrões do projeto |

## CLI

```bash
# Tasks
specify task create --slug <slug> --title "<título>"
specify task list
specify task update <slug> --status in_progress
specify task close <slug>

# Gates
specify gate run --task <slug> --phase tests
specify gate run --task <slug> --phase lint
specify gate history --task <slug>

# Memória
specify memory set --type decision --content "<decisão>"
specify memory set --type pattern  --content "<padrão>"
specify memory search "<query>"
specify memory list --type decision
```

## Estrutura `.specify/`

```
.specify/
├── INDEX.md          ← stack + arquitetura + restrições (editável)
├── specify.db        ← estado persistente (gitignored automaticamente)
└── tasks/
    └── <slug>/
        ├── spec.md   ← fonte de verdade da task
        ├── plan.md   ← ciclo aprovado
        ├── gates.md  ← histórico de gates
        └── result.md ← resultado final
```

## Worktrees

Tasks longas ou paralelas podem rodar em worktrees isolados:

```bash
specify task create --slug minha-task --title "..." --worktree
# cria .claude/worktrees/minha-task/ com branch specify/minha-task
```

Adicione `.worktreeinclude` na raiz para que o `specify.db` seja copiado automaticamente:

```bash
cp ~/projects/specify/templates/worktreeinclude ./.worktreeinclude
```

## Memória semântica

O specify usa [fastembed](https://github.com/qdrant/fastembed) (`BAAI/bge-small-en-v1.5`, ONNX, ~90MB local) para busca semântica nas memórias. Sem API key, sem GPU. Se fastembed não estiver disponível, cai para substring silenciosamente.

## Contribuindo

```bash
git clone https://github.com/LucasGitDev/specify.git ~/projects/specify
cd ~/projects/specify
task setup        # cria venv e instala deps
task test         # testes unitários
task test:e2e     # smoke tests end-to-end
task dev:install  # instala em modo dev (symlinks + hook)
```

Para editar skills: `skills/specify.*/SKILL.md` — as mudanças refletem na próxima sessão sem reinstalar.

Para novo comando CLI: adicione em `src/cli/cmd_*.py`, registre em `src/cli/main.py`, escreva testes em `tests/unit/`.

---

<p align="center">
  <sub>specify é um projeto privado. inicialize com <code>specify init</code> antes de usar.</sub>
</p>
