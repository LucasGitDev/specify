# Plan: memory-format

**Data**: 2026-06-30
**Spec**: .specify/tasks/memory-format/spec.md
**Status**: aprovado

## Critérios de sucesso

1. `memory set --type constraint` sugere ALWAYS:/NEVER:/CHECK: se conteúdo não começa com prefixo reconhecido
2. `memory set --type pattern` sugere WHEN...DO... se ausente
3. `memory set --type decision` sugere DECIDED: se ausente
4. Sugestão não-bloqueante — memória salva independente do formato
5. `memory reformat [--id <id>] [--dry-run]` reformata memórias sem prefixo determinísticamente
6. `memory reformat` sem --id processa todas as memórias sem prefixo reconhecido
7. `memory list` exibe prefixo com destaque visual distinto do restante do conteúdo
8. Memória já com prefixo reconhecido não recebe sugestão no `memory set`

## Ciclo

- RED: testes para os 8 critérios + edge cases (prefixo parcial, dry-run, lote > 5)
- GREEN: implementar _suggest_prefix + cmd_set + cmd_reformat + cmd_list highlight (max 3 iter)
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task memory-format --phase tests` | pass |
| lint | `specify gate run --task memory-format --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

nenhum encontrado

## Worktree

não — sessão principal