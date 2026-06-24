# Plan: expand-debug-logging

**Data**: 2026-06-24
**Spec**: .specify/tasks/expand-debug-logging/spec.md
**Status**: aprovado

## Critérios de sucesso

1. artifact save → loga path + primeiros 200 chars do content
2. gate run → loga comando, duração, status, output completo
3. gate record → loga task/phase/type/status
4. task create/update/close → loga slug + mudança de status
5. memory search → loga query + N resultados
6. session_start → loga tasks ativas e memórias carregadas
7. Hook PostToolUse (bash) → appenda ferramenta, input resumido, exit status em specify.log quando SPECIFY_DEBUG=1
8. specify log tail → exibe últimas N linhas (padrão 50)
9. specify log clear → apaga arquivo de log

## Ciclo

- RED: testes para critérios 1-6, 8-9 (hook PostToolUse é bash, não testável com pytest)
- GREEN: get_logger().debug() nos cmds existentes + cmd_log.py (tail/clear) + hook PostToolUse em settings.json
- REFACTOR: ruff check + ruff format + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

manual

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task expand-debug-logging --phase tests` | pass |
| lint | `specify gate run --task expand-debug-logging --phase lint` | pass |
| adversarial | `specify gate record --task expand-debug-logging --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

nenhum encontrado — padrão do logger já estabelecido em src/core/logger.py

## Worktree

não — sessão principal