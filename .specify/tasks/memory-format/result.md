# Result: memory-format

**Status**: closed
**Data**: 2026-06-30

## Entregáveis

- `_suggest_prefix(type, content) -> str | None` — lógica determinística de sugestão por tipo
- `_highlight_content(content) -> str` — wrap de prefixo reconhecido em `[PREFIX:]`
- `cmd_set` — imprime sugestão de formato após salvar quando prefixo ausente
- `cmd_reformat` — novo subcomando: reformata memórias sem prefixo; suporta --id, --dry-run; confirma quando > 5 registros
- `cmd_list` — destaque visual de prefixos reconhecidos via `_highlight_content`
- 22 testes novos em `tests/unit/test_memory_format.py`; 164 total passando

## Critérios vs implementação

1. ✓ constraint sugere ALWAYS:/NEVER:/CHECK:
2. ✓ pattern sugere WHEN...DO...
3. ✓ decision sugere DECIDED:
4. ✓ sugestão não-bloqueante
5. ✓ reformat --dry-run não altera banco
6. ✓ reformat sem --id processa todas sem prefixo
7. ✓ list exibe prefixo destacado com [PREFIX:]
8. ✓ memória já prefixada não recebe sugestão

## Edge cases observados (não bloqueantes)

- `content = ""` → sugestão `"ALWAYS: "` — inócuo, click rejeita antes
- `"DECIDED"` sem colon → sugestão `"DECIDED: DECIDED"` — cosmético, caminho impossível na prática

## Prefixos reconhecidos

`ALWAYS:`, `NEVER:`, `CHECK:`, `DECIDED:`, `AVOID:`, `WHEN` (sem colon obrigatório)