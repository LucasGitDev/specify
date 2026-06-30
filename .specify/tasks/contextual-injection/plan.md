# Plan: contextual-injection

**Data**: 2026-06-30
**Spec**: .specify/tasks/contextual-injection/spec.md
**Status**: aprovado

## Critérios de sucesso

1. task create executa semantic search + exibe "Relevant prior knowledge" (até 5 resultados)
2. Seção omitida quando similaridade < 0.5 ou provider indisponível (sem ruído)
3. specify context <slug> retorna constraints/decisions relevantes à task (substitui critério CLI do plan)
4. specify context funciona mesmo sem spec.md — usa título da task
5. gate run --phase tests imprime checklist de constraints antes do gate
6. Checklist não bloqueia execução
7. Checklist omitido quando nenhuma constraint com similaridade >= 0.4
8. Semantic search em task create e gate run < 2 segundos

## Decisão de design

`specify plan` é uma skill do agent — sem CLI testável. Critérios 3/4 implementados via
`specify context <slug>`: novo subcomando que o agent invoca ao planejar, retornando
constraints e decisions relevantes à task. A skill /specify.plan será atualizada para
instruir sua chamada.

## Ciclo

- RED: testes para os 8 critérios + edge cases
- GREEN: cmd_task.py (search no create) + cmd_gate.py (checklist) + cmd_context.py (novo)
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task contextual-injection --phase tests` | pass |
| lint | `specify gate run --task contextual-injection --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

- [7] memory-format fechado — pré-requisito satisfeito
- Sem cmd_plan.py no CLI — specify plan é skill do agent

## Worktree

não — sessão principal