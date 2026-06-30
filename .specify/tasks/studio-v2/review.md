# Review: studio-v2

**Data**: 2026-06-30
**Iterações de correção**: 1

## Findings

| Critério | Severidade | Status | Descrição |
|----------|-----------|--------|-----------|
| Tasks aparecem como nós roxos e maiores | ✓ | aprovado | — |
| Arestas scope-link com kind=scope, cor distinta | ✓ | aprovado | — |
| Tasks sem memórias aparecem como nós isolados | ✓ | aprovado | — |
| Click em task abre sidebar com title, status, gates, result.md | crítico | resolvido | Query usava colunas inexistentes: `result` e `recorded_at`. Schema real: `status` e `created_at`. Endpoint retornaria OperationalError em produção. |
| Filtro por tipo inclui 'task' como quarta categoria | ✓ | aprovado | — |
| GET /api/graph retorna tasks + scope-links | ✓ | aprovado | — |

## Correções realizadas

- `fix(studio): correct gates column names in /api/tasks/:slug query`

## Resultado

APROVADO — zero críticos após 1 ciclo de correção