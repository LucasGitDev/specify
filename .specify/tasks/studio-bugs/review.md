# Review: studio-bugs

**Data**: 2026-06-30
**Iterações de correção**: 0

## Findings

| Critério | Severidade | Status | Descrição |
|----------|-----------|--------|-----------|
| Task nodes próximos de memórias conectadas | ✓ | aprovado | applyLayout diferencia scope (d/3) vs semantic (d/10) |
| Scope-link edges visualmente distintos | ✓ | aprovado | EDGE_COLORS já distinguia — preservado do studio-v2 |
| Botões de filtro permanecem visíveis | ✓ | aprovado | sigma-container isolado; toolbar/legend são irmãos, não filhos |
| Toggle oculta/reexibe nós corretamente | ✓ | aprovado | activeFilters + rebuildGraph preservados e funcionais |
| Nenhum elemento do painel desaparece | ✓ | aprovado | coberto por test_toolbar_appears_before_sigma_container |
| Estado ativo/inativo refletido no botão | ✓ | aprovado | classList.add/remove('active') preservado de antes |

## Correções realizadas

nenhuma — implementação cobriu todos os critérios sem correção de review

## Resultado

APROVADO — zero críticos