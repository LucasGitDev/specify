---
name: specify.close
description: "Fecha uma task: verifica gates obrigatórios, gera result.md, atualiza status para closed, executa commit e MR. Use quando o usuário quiser fechar uma task, entregar uma implementação, executar '/specify close', ou após '/specify review' concluir sem críticos."
user-invocable: true
argument-hint: "Slug da task (ex: 'add-healthcheck')"
---

# specify close

Gate final antes da entrega. Verifica que todos os gates obrigatórios passaram, gera o resultado e fecha a task.

```
Verificar gates → Gerar result.md → Fechar task → Commit → MR
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

## Fase 1 — Gerar result.md

Escrever `.specify/tasks/<slug>/result.md`:

```markdown
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
```

## Fase 2 — Fechar task

```bash
specify task close <slug>
```

## Fase 3 — Commit e MR

Invocar `/commit` para gerar commit semântico.

Se disponível, invocar `/pullrequest-creator` para gerar título e descrição do MR.

Se em worktree isolado, orientar merge:
```bash
# Verificar branch atual
git branch --show-current

# Merge na branch principal
git checkout main
git merge <branch-worktree> --no-ff -m "feat(<slug>): <título da task>"
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
