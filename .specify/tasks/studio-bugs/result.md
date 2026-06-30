# Result: studio-bugs

**Status**: CLOSED
**Data**: 2026-06-30

## Gates

| Gate | Status | Iterações |
|------|--------|-----------|
| RED/tests | ✓ fail (esperado) | 1 |
| GREEN/tests | ✓ pass | 1 |
| REFACTOR/lint | ✓ pass | 1 |
| REVIEW/adversarial | ✓ pass | 0 correções |

## Critérios cobertos

1. ✓ Nós de task com scope-links aparecem próximos das memórias conectadas — applyLayout diferencia scope (d/3) vs semantic (d/10)
2. ✓ Edges scope-link visualmente distintos dos semânticos — EDGE_COLORS preservado do studio-v2
3. ✓ Botões de filtro permanecem visíveis após qualquer clique — sigma-container isolado como filho de graph-container
4. ✓ Toggle oculta/reexibe nós do tipo correto — activeFilters + rebuildGraph funcional
5. ✓ Nenhum elemento do painel de controle desaparece — toolbar/legend são irmãos de sigma-container
6. ✓ Estado ativo/inativo refletido visualmente no botão — classList.add/remove('active') preservado

## Arquivos modificados

- src/studio/static/index.html — sigma-container div + layout scope force + sigmaContainer refs
- tests/unit/test_studio_bugs.py — 7 testes novos

## Memórias geradas

- constraint [5]: Sigma.js deve renderizar em #sigma-container, não em #graph-container diretamente