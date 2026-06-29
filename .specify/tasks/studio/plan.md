# Plan: studio

**Data**: 2026-06-29
**Spec**: roadmap/studio/mvp.md
**Status**: aprovado

## Critérios de sucesso

1. `specify studio` inicia servidor FastAPI local e abre browser
2. Graph renderiza nós de memórias (decision/pattern/constraint) com cores distintas
3. Arestas semânticas calculadas via cosine similarity (threshold ≥ 0.7, top-3 por nó)
4. Click em nó abre sidebar com conteúdo editável
5. Edição salva no SQLite e re-embed via fastembed (~200ms async)
6. Sem dependências de build — Sigma.js + Graphology via CDN

## Ciclo

- RED: escrever testes para graph.py (cosine similarity, node/edge building)
- GREEN: implementar em ordem: graph.py → app.py → index.html → cmd_studio.py
- REFACTOR: lint + fmt + re-run tests
- REVIEW: adversarial — críticos = 0
- CLOSE: gate check + result.md

## Estratégia de commits

automático

## Gates obrigatórios

| Gate | Comando | Critério |
|------|---------|----------|
| tests | `specify gate run --task studio --phase tests` | pass |
| lint | `specify gate run --task studio --phase lint` | pass |
| adversarial | `specify gate record --phase review --type adversarial` | pass, críticos = 0 |

## Contexto da memória

nenhum encontrado

## Worktree

sim — .claude/worktrees/studio/ (branch: specify/studio)