# Result: memory-audit-gate

**Status**: closed
**Data**: 2026-06-30

## Entregáveis

- `src/db/schema.py` — migration 5: tabela `memory_links`
- `src/db/links.py` — novo módulo: `insert`, `exists`, `list_for_task`
- `src/cli/cmd_memory.py` — subcomando `memory link`: persiste not-applicable com --note obrigatório
- `src/cli/cmd_gate.py`:
  - `_extract_keywords` — extrai termos de constraint para evidence matching
  - `_has_evidence` — verifica working tree, staged, HEAD commit e plan.md
  - `_run_memory_audit` — executa audit, registra gate, retorna (status, output)
  - `cmd_run` — aceita `--phase memory-audit`, pipeline sem `--phase`, `--skip-memory-audit`
- 11 testes novos; 189 total passando

## Critérios vs implementação

1. ✓ gate run --phase memory-audit retorna PASS/FAIL com diagnóstico
2. ✓ FAIL quando constraint (dist <= 0.25) sem evidência de endereçamento
3. ✓ Evidência: termos em git-modified files (HEAD commit incluído), plan.md, not-applicable link
4. ✓ Output de FAIL inclui ID, conteúdo, fonte e comando exato de remediação
5. ✓ memory link --kind not-applicable --note persiste exceção
6. ✓ memory link sem --note rejeitado com ClickException
7. ✓ gate run sem --phase executa memory-audit antes de tests
8. ✓ --skip-memory-audit suprime fase e registra skip no histórico
9. ✓ PASS silencioso quando provider indisponível ou sem constraints próximas

## Decisões de design

- memory_links mínima (não schema completo do Spec D) — evita over-engineering
- dist <= 0.25 (mais estrito que checklist 0.4) — reduz falsos positivos
- Evidence inclui HEAD commit (git show) além de working tree — necessário quando arquivo foi commitado
- keywords vazia → constraint sempre flagrada (comportamento correto: constraint malformada)