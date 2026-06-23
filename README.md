<h1 align="center">specify</h1>

<p align="center">
  <strong>spec primeiro. código depois. sempre.</strong>
</p>

<p align="center">
  <a href="#por-que">Por que</a> •
  <a href="#como-funciona">Como funciona</a> •
  <a href="#instalação">Instalação</a> •
  <a href="#primeiro-uso">Primeiro uso</a> •
  <a href="#skills">Skills</a> •
  <a href="#cli">CLI</a> •
  <a href="#worktrees">Worktrees</a> •
  <a href="#contribuindo">Contribuindo</a>
</p>

---

Plugin [Claude Code](https://claude.ai/code) que implementa **Spec-Driven Development (SDD)** com TDD e Agentic SDLC como um fluxo coeso — do planejamento ao merge, com estado persistente por projeto.

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

```bash
git clone <repo-url> ~/projects/specify
cd ~/projects/specify
bash install.sh
```

`install.sh` instala [uv](https://github.com/astral-sh/uv) se ausente, cria o venv, registra as skills e o hook. Sem sudo. Reinicie o Claude Code depois.

Verifique:
```bash
specify --help          # CLI disponível
# /specify.init         # skill disponível no Claude Code
```

**Requisitos:** Python 3.12+, Claude Code, Git. uv é instalado automaticamente.

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

Adicione arquitetura e restrições reais do projeto. Esse arquivo é o contexto que o agente lê em toda sessão.

### 3. Escrever a spec

```bash
mkdir -p .specify/tasks/add-healthcheck
$EDITOR .specify/tasks/add-healthcheck/spec.md
```

Uma spec mínima válida:

```markdown
# Adicionar endpoint de healthcheck

## Critérios de Sucesso

- GET /health retorna 200 com `{"status": "ok"}`
- GET /health retorna 503 se dependência crítica estiver indisponível
- Latência do endpoint não bloqueia outras rotas
```

### 4. Executar o fluxo

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
| `/specify.plan` | Antes de qualquer código — valida spec e propõe ciclo |
| `/specify.sdd` | Implementar: RED→GREEN→REFACTOR com gates automáticos |
| `/specify.review` | Revisar adversarialmente antes do merge |
| `/specify.close` | Gate final, result.md, commit, MR |
| `/specify.memory` | Salvar e buscar decisões e padrões do projeto |

## CLI

O CLI `specify` é a camada de persistência que as skills usam. Você pode chamar diretamente também.

```bash
# Tasks
specify task create --slug <slug> --title "<título>"
specify task list
specify task update <slug> --status in_progress
specify task close <slug>

# Gates
specify gate run --task <slug> --phase tests    # executa go test ./... e registra
specify gate run --task <slug> --phase lint
specify gate history --task <slug>

# Memória (busca semântica por padrão, substring como fallback)
specify memory set --type decision --content "JWT via lestrrat-go/jwx/v3"
specify memory set --type pattern  --content "handlers em api/, lógica em pkg/service/"
specify memory search "autenticação"
specify memory list --type decision
```

## Estrutura `.specify/` no projeto

```
.specify/
├── INDEX.md          ← stack + arquitetura + restrições (editável)
├── specify.db        ← estado persistente (gitignored automaticamente)
└── tasks/
    └── <slug>/
        ├── spec.md   ← fonte de verdade da task (você escreve)
        ├── plan.md   ← ciclo aprovado (gerado pelo /specify.plan)
        ├── gates.md  ← histórico de gates human-readable
        └── result.md ← resultado final (gerado pelo /specify.close)
```

## Worktrees

Tasks longas ou paralelas podem rodar em worktrees isolados — arquivos separados, sem conflito:

```bash
specify task create --slug minha-task --title "..." --worktree
# cria .claude/worktrees/minha-task/ com branch specify/minha-task
```

Adicione `.worktreeinclude` na raiz do projeto para que o `specify.db` seja copiado automaticamente para novos worktrees:

```bash
cp ~/projects/specify/templates/worktreeinclude ./.worktreeinclude
```

## Memória vetorial

O specify usa [fastembed](https://github.com/qdrant/fastembed) (modelo `BAAI/bge-small-en-v1.5`, ONNX, ~90MB local) para busca semântica nas memórias. Sem API key, sem GPU.

O modelo é baixado automaticamente na primeira chamada a `specify memory set` ou `memory search`.

Se fastembed não estiver disponível, a busca cai para substring silenciosamente.

## Contribuindo

```bash
git clone <repo-url> ~/projects/specify
cd ~/projects/specify
task setup            # cria venv e instala deps
task test             # 67 testes unitários
task test:e2e         # 12 smoke tests end-to-end
task dev:install      # instala em modo dev (symlinks + hook)
```

Para editar as skills basta editar os arquivos em `skills/specify.*/SKILL.md` — as mudanças refletem na próxima sessão Claude Code sem reinstalar.

Para adicionar um novo comando CLI: adicione em `src/cli/cmd_*.py`, registre em `src/cli/main.py`, escreva testes em `tests/unit/`.

**79 testes passando (67 unitários + 12 e2e).**

---

<p align="center">
  <sub>specify é um projeto privado. não esqueça de inicializar com <code>specify init</code> antes de usar.</sub>
</p>
