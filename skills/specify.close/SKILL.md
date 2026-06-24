---
name: specify.close
description: "Fecha uma task: verifica gates obrigatórios, gera result.md, atualiza status para closed, executa commit e MR. Use quando o usuário quiser fechar uma task, entregar uma implementação, executar '/specify close', ou após '/specify review' concluir sem críticos."
user-invocable: true
argument-hint: "Slug da task (ex: 'add-healthcheck')"
---

# specify close

Gate final antes da entrega. Verifica que todos os gates obrigatórios passaram, gera o resultado e fecha a task.

```
Verificar gates → Verificar commits pendentes → Gerar result.md → Fechar task → Commit result.md → MR
```

## Fase 0 — Gate check

```bash
specify gate history --task <slug> --json
```

Gates obrigatórios para fechar:

| Gate | Phase | Type |
|------|-------|------|
| Testes passando | `green` | `tests` |
| Lint limpo | `refactor` ou `lint` | `lint` |
| Review aprovado | `review` | `adversarial` |

Para cada gate obrigatório ausente ou com status `fail`:
```
Não é possível fechar '<slug>'. Gates pendentes:

  ✗ review/adversarial — execute /specify review <slug>
  ✗ refactor/lint      — execute /specify sdd <slug>

Resolva os gates acima antes de fechar.
```

## Fase 0.5 — Verificar commits pendentes

```bash
git status --short
git diff --stat HEAD
```

Se houver arquivos modificados não commitados:
```
⚠ Há mudanças não commitadas. Isso não deveria acontecer se /specify.sdd foi executado.

Arquivos pendentes:
<lista>

Commitando mudanças de código pendentes antes de fechar...
```

Se houver código pendente (não apenas `.specify/`): commitar com a estratégia definida no `plan.md`.
Arquivos de `.specify/` (spec, plan, sdd.log) são commitados junto com o `result.md` no commit de encerramento.

## Fase 1 — Salvar result.md via CLI

> **OBRIGATÓRIO**: salvar result.md antes de fechar a task.

```bash
specify artifact save --task <slug> --type result --content "$(cat <<'RESULT'
# Result: <slug>

**Status**: CLOSED  
**Data**: <data atual>

## Gates

| Gate | Status | Iterações |
|------|--------|-----------|
| RED/tests | ✓ pass | <N> |
| GREEN/tests | ✓ pass | <N> |
| REFACTOR/lint | ✓ pass | 1 |
| REVIEW/adversarial | ✓ pass | <N> |

## Critérios cobertos

<lista numerada dos critérios da spec com ✓>

## Arquivos modificados

<output de git diff --name-only main>

## Memórias geradas

<decisões ou padrões salvos durante a implementação, se houver>
RESULT
)"
```

## Fase 2 — Fechar task

```bash
specify task close <slug>
```

## Fase 3 — Commit de encerramento e MR

Commitar apenas os arquivos do `.specify/tasks/<slug>/` (result.md, sdd.log, review.md gerados neste fluxo):

```bash
git add .specify/tasks/<slug>/
git commit -m "chore(<slug>): close task and add specify artifacts"
```

- Mensagem fixa: `chore(<slug>): close task and add specify artifacts`
- Não misturar com código de produção — se houver código pendente, ele já foi commitado na Fase 0.5

Se disponível, invocar `/pullrequest-creator` para gerar título e descrição do MR com base nos commits da task:
```bash
git log --oneline origin/main..HEAD
```

Se em worktree isolado, orientar merge:
```bash
git checkout main
git merge <branch-worktree> --no-ff
```

## Resultado final

```
═══════════════════════════════════════════════════
  Task fechada — <slug>
═══════════════════════════════════════════════════

  Status:    closed
  Gates:     todos passando ✓
  Result:    .specify/tasks/<slug>/result.md
  Commit:    <hash> (se executado)

═══════════════════════════════════════════════════
```

## Quando NÃO usar

- Gates obrigatórios faltando — resolver com `/specify sdd` e `/specify review` primeiro
- Task já `closed` — já foi encerrada
