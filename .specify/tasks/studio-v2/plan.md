# Plan: studio-v2

**Data**: 2026-06-30
**Spec**: .specify/tasks/studio-v2/spec.md
**Status**: aprovado

## Critérios de sucesso

1. Tasks aparecem no grafo como nós roxos e maiores que memórias
2. Arestas scope-link conectam task → memórias do mesmo scope
3. Tasks sem memórias aparecem como nós isolados
4. Click em task abre sidebar com title, status, gates, link result.md
5. Filtro por tipo inclui 'task' como quarta categoria funcional
6. GET /api/graph retorna tasks + scope-links no formato existente

## Ciclo

- RED: testes para build_graph() com tasks + scope-links + filtragem por tipo
- GREEN: graph.py TaskNode + app.py /api/tasks/:slug + index.html sidebar/filtro
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task studio-v2 --phase tests` | pass |
| lint | `specify gate run --task studio-v2 --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

Nenhum encontrado — task nova sem decisões anteriores.

## Worktree

não — sessão principal (task focada em 3 arquivos)