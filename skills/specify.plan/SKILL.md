---
name: specify.plan
description: "Planeja o ciclo de desenvolvimento de uma task: lê spec, valida critérios, propõe fases RED→GREEN→REFACTOR→REVIEW→CLOSE, aguarda aprovação humana e inicializa a task no DB. Use quando o usuário quiser planejar uma implementação, usar '/specify plan', iniciar uma task com spec, ou dizer 'quero implementar <feature>'."
user-invocable: true
argument-hint: "Slug da task (ex: 'add-healthcheck'). A spec deve existir em .specify/tasks/<slug>/spec.md"
---

# specify plan

Lê a spec de uma task, valida, propõe o ciclo de desenvolvimento e aguarda aprovação antes de iniciar qualquer código.

A spec é a fonte de verdade. Sem spec válida, não há plano.

```
Ler spec → Validar → Buscar contexto → Propor ciclo → GATE: aprovação → Salvar plan.md → Inicializar task
```

## Fase 0 — Resolver spec

Se o usuário forneceu um slug como argumento:
```bash
cat .specify/tasks/<slug>/spec.md
```

Se não forneceu, listar specs disponíveis:
```bash
find .specify/tasks -name "spec.md" 2>/dev/null
```

Se nenhuma encontrada:
> "Nenhuma spec encontrada. Crie `.specify/tasks/<slug>/spec.md` antes de continuar."

## Fase 1 — Validar spec

Uma spec válida requer:
- Linha de título começando com `# `
- Seção de critérios com heading contendo "critério", "aceite", "success" ou "sucesso"

Se inválida, interromper com mensagem clara indicando o que falta.

Extrair critérios da spec — serão usados para propor os testes na fase RED.

## Fase 2 — Buscar contexto do projeto

```bash
# Decisões arquiteturais que podem impactar a implementação
specify memory search "<palavras-chave da spec>"

# Restrições globais
specify memory list --type constraint

# Tasks relacionadas (evitar conflito)
specify task list --status in_progress
```

Usar o contexto para enriquecer a proposta (ex: "decidimos usar JWT, confirmar que a implementação segue esse padrão").

## Fase 3 — Propor ciclo

Exibir proposta estruturada:

```
═══════════════════════════════════════════════════
  Plano — <slug>
═══════════════════════════════════════════════════

  Spec:     .specify/tasks/<slug>/spec.md
  Título:   <título da spec>

  Critérios de sucesso:
  1. <critério>
  2. <critério>
  ...

  Ciclo proposto:
  → RED      escrever testes para cada critério + edge cases
  → GREEN    implementar código mínimo (max 3 iterações)
  → REFACTOR lint + fmt + re-run tests
  → REVIEW   adversarial: verificar critérios vs implementação
  → CLOSE    gate check + result.md + commit

  Gates obrigatórios:
  - GREEN: specify gate run --phase tests (pass)
  - REFACTOR: specify gate run --phase lint (pass)
  - REVIEW: classify críticos = 0

  Contexto relevante da memória:
  <decisões/padrões encontrados, ou "nenhum encontrado">

  Prosseguir com este plano? [s para continuar]
═══════════════════════════════════════════════════
```

**Aguardar aprovação.** Não avançar sem confirmação explícita.

## Fase 3.1 — Salvar plan.md imediatamente após aprovação

Assim que o usuário aprovar, escrever `.specify/tasks/<slug>/plan.md` **antes** de qualquer comando CLI. O arquivo é a fonte de verdade do plano — não o chat.

```markdown
# Plan: <slug>

**Data**: <data atual>
**Spec**: .specify/tasks/<slug>/spec.md
**Status**: aprovado

## Critérios de sucesso

1. <critério extraído da spec>
2. <critério>
...

## Ciclo

- RED: escrever testes para cada critério + edge cases
- GREEN: implementar código mínimo (max 3 iterações)
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md + commit

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task <slug> --phase tests` | pass |
| lint | `specify gate run --task <slug> --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

<decisões e padrões relevantes encontrados, ou "nenhum encontrado">

## Worktree

<"sim — .claude/worktrees/<slug>/ (branch: specify/<slug>)" ou "não — sessão principal">
```

Confirmar escrita:
```bash
cat .specify/tasks/<slug>/plan.md
```

## Fase 4 — Decidir worktree vs sessão principal

Usar **worktree isolado** quando:
- Task afeta muitos arquivos ou leva mais de ~30 min
- Há outras tasks `in_progress` na sessão atual
- Usuário quer trabalhar em paralelo com outra tarefa

Usar **sessão principal** quando:
- Task pequena e focada
- Nenhum outro worktree ativo no projeto

Se worktree:
```bash
specify task create --slug <slug> --title "<título>" --spec <spec_path> --worktree
# Output inclui: worktree path e instrução para entrar
```

Se sessão principal:
```bash
specify task create --slug <slug> --title "<título>" --spec <spec_path>
```

## Fase 5 — Inicializar task

```bash
# Criar task (com ou sem --worktree conforme decisão da Fase 4)
specify task create --slug <slug> --title "<título>" --spec .specify/tasks/<slug>/spec.md
# ou
specify task create --slug <slug> --title "<título>" --spec .specify/tasks/<slug>/spec.md --worktree

# Marcar como in_progress
specify task update <slug> --status in_progress
```

Confirmar:
```
✓ plan.md salvo em .specify/tasks/<slug>/plan.md
Task '<slug>' criada e marcada como in_progress.
Worktree: <path> (branch: specify/<slug>) — ou "sessão principal"
Próximo passo: /specify.sdd <slug>
```

## Quando NÃO usar

- Sem spec escrita — escreva `.specify/tasks/<slug>/spec.md` primeiro
- Task já em `in_progress` com gates registrados — use `/specify sdd` diretamente
