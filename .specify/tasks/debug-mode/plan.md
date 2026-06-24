# Plan: debug-mode

**Data**: 2026-06-24
**Spec**: .specify/tasks/debug-mode/spec.md
**Status**: aprovado

## Critérios de sucesso

1. SPECIFY_DEBUG=1 → CLI escreve em ~/.claude/specify.log cada operação (comando, projeto root, DB path, resultado)
2. SPECIFY_DEBUG=1 → session_start.py escreve no mesmo log em exceções, com traceback completo
3. Formato de log: [ISO timestamp] [nível] mensagem, append
4. SPECIFY_DEBUG ausente → zero efeito colateral, comportamento atual preservado
5. Falha ao escrever log → comando continua sem erro

## Ciclo

- RED: escrever testes para cada critério + edge cases
- GREEN: implementar src/core/logger.py + integrar em main.py e session_start.py
- REFACTOR: ruff check + ruff format + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

controlado

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task debug-mode --phase tests` | pass |
| lint | `specify gate run --task debug-mode --phase lint` | pass |
| adversarial | `specify gate record --task debug-mode --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

nenhum encontrado

## Worktree

não — sessão principal