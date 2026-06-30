# Plan: memory-audit-gate

**Data**: 2026-06-30
**Spec**: .specify/tasks/memory-audit-gate/spec.md
**Status**: aprovado

## Critérios de sucesso

1. gate run --phase memory-audit retorna PASS/FAIL com diagnóstico
2. FAIL quando constraint com dist <= 0.25 não tem evidência de endereçamento
3. Evidência: termos da constraint em arquivos git-modificados, plan.md, ou link not-applicable
4. Output de FAIL lista ID, conteúdo, fonte, e comando exato para marcar not-applicable
5. memory link --kind not-applicable --memory <id> --task <slug> --note "..." persiste exceção
6. memory link sem --note é rejeitado
7. gate run sem --phase executa memory-audit automaticamente antes de tests
8. gate run --skip-memory-audit suprime fase (registrado no histórico)
9. PASS silencioso quando nenhuma constraint atinge threshold

## Decisão de design

- vec_db.search retorna L2 distance — dist <= 0.25 (mais estrito) para reduzir falsos positivos
- memory_links mínima (migration 5) — não o schema completo do Spec D
- Evidência = substring match de termos-chave, sem NLI/embedding

## Ciclo

- RED: testes para os 9 critérios + edge cases
- GREEN: schema migration + db/links.py + cmd memory link + cmd gate memory-audit
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task memory-audit-gate --phase tests` | pass |
| lint | `specify gate run --task memory-audit-gate --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

- [8] ALWAYS: vec_db.search retorna L2 dist — dist <= max aplicado no threshold
- Specs A (memory-format) e B (contextual-injection) fechadas — pré-requisitos satisfeitos

## Worktree

não — sessão principal