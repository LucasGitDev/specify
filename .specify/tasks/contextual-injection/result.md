# Result: contextual-injection

**Status**: closed
**Data**: 2026-06-30

## Entregáveis

- `cmd_task.py` — `task create` executa semantic search e exibe "Relevant prior knowledge" antes de confirmar criação; flag `--no-search` suprime
- `cmd_gate.py` — `gate run --phase tests` imprime "Constraint checklist" antes do gate; não aparece em lint/fmt
- `cmd_context.py` — novo subcomando `specify context <slug>`: retorna constraints e decisions relevantes por task, com e sem spec.md
- `main.py` — `cmd_context` registrado no CLI
- 14 testes novos em `tests/unit/test_contextual_injection.py`; 178 total passando

## Critérios vs implementação

1. ✓ task create mostra "Relevant prior knowledge" com até 5 resultados
2. ✓ seção omitida quando provider indisponível ou sem similaridade suficiente
3. ✓ specify context <slug> retorna constraints/decisions relevantes
4. ✓ specify context funciona sem spec.md (usa título da task)
5. ✓ gate run --phase tests imprime checklist de constraints antes do gate
6. ✓ checklist não bloqueia execução
7. ✓ checklist omitido quando provider indisponível
8. ✓ distância L2 usada corretamente (lower = more similar)

## Decisão de design persistida

vec_db.search retorna distância L2, não similaridade — threshold é invertido (dist <= max),
não (score >= min). Aplicado em cmd_task, cmd_gate e cmd_context.

## Nota para /specify.plan skill

Atualizar skill para instruir `specify context <slug>` como primeiro comando ao planejar.