# Result: studio

**Status**: done
**Data**: 2026-06-29

## Entregues

- `src/studio/graph.py` — cosine similarity + build_graph (nodes/edges de sqlite + vec_memories)
- `src/studio/app.py` — FastAPI: GET /api/graph, GET/PUT/DELETE /api/memories/:id
- `src/studio/static/index.html` — Sigma.js 2.4.0 + Graphology UMD, force layout inline, dark theme
- `src/cli/cmd_studio.py` — `specify studio [--host] [--port] [--no-browser]`
- `src/db/connection.py` — check_same_thread param (False para studio)
- `tests/unit/test_graph.py` — 16 testes unitários (cosine + build_graph)

## Critérios

- [x] `specify studio` inicia servidor e abre browser
- [x] Graph renderiza nós decision/pattern/constraint com cores distintas
- [x] Arestas semânticas via cosine similarity (threshold=0.7, top_k=3)
- [x] Click em nó abre sidebar com conteúdo editável
- [x] Edição salva no SQLite (re-embed quando fastembed disponível)
- [x] Sem build step — CDN only

## Gates

| Gate | Status |
|------|--------|
| green/tests | pass (101 passed) |
| refactor/lint | pass (ruff clean) |
| review/adversarial | pass (0 críticos) |