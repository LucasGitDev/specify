# Plan: studio-bugs

**Data**: 2026-06-30
**Spec**: .specify/tasks/studio-bugs/spec.md
**Status**: aprovado

## Critérios de sucesso

1. Nós de task com scope-links aparecem próximos das memórias conectadas no layout
2. Edges scope-link visualmente distintos dos edges semânticos
3. Botões de filtro permanecem visíveis após qualquer clique
4. Toggle de filtro oculta/reexibe nós do tipo correto
5. Nenhum elemento do painel de controle desaparece durante interação
6. Estado ativo/inativo refletido visualmente no botão

## Ciclo

- RED: testes para lógica de filtro e layout de grafo
- GREEN: fix bug layout (ForceAtlas2 params) + fix bug botões (DOM rerender)
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task studio-bugs --phase tests` | pass |
| lint | `specify gate run --task studio-bugs --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

- IDs de task com prefixo t:<slug> (não alterar)
- Backend /api/graph e /api/tasks/{slug} são somente leitura nesta task
- Sigma.js + Graphology — não trocar de lib

## Worktree

não — sessão principal