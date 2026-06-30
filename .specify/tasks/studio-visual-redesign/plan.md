# Plan: studio-visual-redesign

**Data**: 2026-06-30
**Spec**: .specify/tasks/studio-visual-redesign/spec.md
**Status**: aprovado

## Critérios de sucesso

1. Paleta petróleo/âmbar — #0b0f1a canvas, #0f1520 sidebar, #e8a045 acento
2. Dot-grid sutil no canvas via SVG background-image
3. Wordmark "specify / studio" + type stripe na sidebar
4. Toolbar em dois grupos: Ação | Filtro com gap visual
5. Filter buttons com dot colorido; legenda flutuante removida
6. JetBrains Mono para valores; Inter para labels/botões
7. Stats counter como rodapé da sidebar (removido do canvas)
8. Todos os textos de UI em inglês

## Ciclo

- RED: checklist de verificação dos 8 critérios mapeados contra o HTML atual
- GREEN: implementar todos os critérios em index.html
- REFACTOR: validar IDs/classes preservados; checar constraint Sigma; lint HTML
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task studio-visual-redesign --phase tests` | pass |
| lint | `specify gate run --task studio-visual-redesign --phase lint` | pass |
| adversarial | revisão manual contra spec | críticos = 0 |

## Contexto da memória

CONSTRAINT: Sigma.js limpa innerHTML de #sigma-container no kill(). Toolbar e wordmark devem ser irmãos de #sigma-container dentro de #graph-container, nunca filhos dele.

## Worktree

não — sessão principal