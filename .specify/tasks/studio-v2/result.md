# Result: studio-v2

**Status**: CLOSED
**Data**: 2026-06-30

## Gates

| Gate | Status | Iterações |
|------|--------|-----------|
| GREEN/tests | ✓ pass | 1 |
| REFACTOR/lint | ✓ pass | 1 |
| REVIEW/adversarial | ✓ pass | 1 (1 crítico resolvido) |

## Critérios cobertos

1. ✓ Tasks aparecem no grafo como nós roxos (color #d2a8ff) e maiores (size=16 vs 10)
2. ✓ Arestas scope-link conectam task → memórias do mesmo scope (kind='scope', cor distinta)
3. ✓ Tasks sem memórias aparecem como nós isolados
4. ✓ Click em task abre sidebar com title, status, gates passados, link result.md
5. ✓ Filtro por tipo inclui 'task' como quarta categoria funcional (toggle independente)
6. ✓ GET /api/graph retorna tasks como nós e scope-links como arestas no formato existente

## Arquivos modificados

- src/studio/graph.py — TaskNode dataclass + scope-links em build_graph()
- src/studio/app.py — GET /api/tasks/{slug} + import tasks_db
- src/studio/static/index.html — cor/tamanho distintos para tasks, sidebar de task, filtros por tipo
- tests/unit/test_graph.py — 8 testes novos para tasks-as-nodes
- tests/unit/test_studio_app.py — 5 testes de endpoint (novo arquivo)

## Memórias geradas

- [decision] Studio v2: tasks como nós usam prefixo 't:<slug>' no ID para evitar colisão com IDs numéricos
- [constraint] Queries SQL no studio: tabela 'gates' tem 'status' e 'created_at', não 'result' e 'recorded_at'