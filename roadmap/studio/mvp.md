# specify studio — MVP

## Objetivo

Responder visualmente: **"o que o agent sabe, e como essas coisas se relacionam?"**

Comando: `specify studio` — sobe servidor local, abre browser.

---

## 3 áreas de interface

### 1. Grafo principal (canvas central)

- Nós coloridos por tipo:
  - `decision` → azul
  - `pattern` → verde
  - `constraint` → laranja
  - `task` → roxo
- **Arestas de scope**: memória → task quando `scope != global`
- **Arestas semânticas**: top-3 vizinhos por cosine similarity (threshold ≥ 0.7)
- Tamanho do nó proporcional à recência (memórias recentes maiores)
- Layout: ForceAtlas2 via Sigma.js + Graphology

### 2. Sidebar (ao clicar num nó)

- Conteúdo completo da memória
- Metadados: tipo, scope, source, created_at, updated_at
- Ações:
  - **Editar**: textarea inline → PUT `/api/memories/:id` → re-embeda → grafo atualiza
  - **Deletar**: DELETE `/api/memories/:id` → nó some do grafo
- Lista de vizinhos semânticos com score de similaridade

### 3. Toolbar (topo)

- Toggle buttons por tipo (decision / pattern / constraint / task)
- Dropdown de scope/task
- Campo de busca semântica: nós relevantes aumentam, irrelevantes desfocam (opacity)

---

## Stack

| Componente | Tecnologia |
|---|---|
| Servidor | FastAPI + uvicorn (dep optional) |
| Frontend | HTML único (~400 linhas) servido pelo FastAPI |
| Grafo | Sigma.js + Graphology via CDN |
| Subprocess | `specify studio` → `uvicorn src.studio.app:app` |
| Browser | `webbrowser.open("http://localhost:8765")` automático |

---

## Endpoints

```
GET  /                        → serve HTML único
GET  /api/graph               → {nodes, edges} computado do SQLite
PUT  /api/memories/:id        → update content + re-embed
DELETE /api/memories/:id      → delete memory + embedding
GET  /api/search?q=...        → busca semântica, retorna IDs rankeados
```

### Formato `/api/graph`

```json
{
  "nodes": [
    {"id": "m:1", "label": "decisão sobre X", "type": "decision", "scope": "global", "size": 12},
    {"id": "t:feat-auth", "label": "feat-auth", "type": "task", "scope": "feat-auth", "size": 8}
  ],
  "edges": [
    {"source": "m:1", "target": "t:feat-auth", "kind": "scope"},
    {"source": "m:1", "target": "m:3", "kind": "semantic", "score": 0.87}
  ]
}
```

---

## Cálculo das arestas semânticas

No endpoint `/api/graph`, para cada memória com embedding:
1. Carregar todos os embeddings do sqlite-vec
2. Calcular cosine similarity par a par
3. Para cada nó: manter top-3 com score ≥ 0.7
4. Deduplicar arestas bidirecionais

Sem dependência nova — `sqlite-vec` já tem os vetores, cosine similarity é álgebra pura.

---

## Fora do MVP

- PCA positioning (requer scikit-learn)
- Timeline view
- Cluster automático com labels
- Task orbit view alternativo
- Source tracking (arquivo → memória)
- Diff view

---

## Estrutura de arquivos

```
src/
  studio/
    __init__.py
    app.py          → FastAPI app + endpoints
    graph.py        → lógica de montar nodes/edges + cosine similarity
    static/
      index.html    → HTML único com Sigma.js + Graphology CDN
src/cli/
  cmd_studio.py     → comando `specify studio`
```

---

## Critério de done

- `specify studio` sobe sem erro com `.specify/` inicializado
- Grafo renderiza com nós e arestas semânticas
- Filtro por tipo funciona
- Editar conteúdo de uma memória persiste no SQLite e atualiza o grafo
- Deletar memória remove o nó
- Busca semântica destaca nós relevantes

---

## Roadmap v2 — Tasks como nós

### Motivação

O banco já tem `tasks` com slug, title e status. Memórias têm `scope` que referencia o slug da task que as gerou. Com isso é possível construir uma camada de abstração acima das memórias: **tasks como nós agregadores**, conectados às memórias do mesmo escopo por arestas explícitas (scope-link), e entre si via similaridade semântica das memórias filhas.

### Comportamento esperado

- Tasks aparecem como nós maiores (tamanho diferente das memórias)
- Arestas `scope-link` conectam task → memórias do mesmo escopo (cor diferente das semânticas)
- Tasks sem memórias ainda aparecem — mostram que a task existiu mesmo sem decisões persistidas
- Click em nó de task abre sidebar com: title, status, gates passados, link para `result.md`
- Filtro por tipo inclui `task` como quarta categoria

### Dados necessários

```python
# já existentes em src/db/tasks.py
GET /api/graph  # expandir para incluir tasks
```

### Implementação

1. `graph.py`: adicionar `TaskNode` dataclass + lógica de scope-link em `build_graph()`
2. `app.py`: `GET /api/tasks/:slug` para sidebar de task
3. `index.html`: cor e tamanho distintos para nós de task, sidebar alternativo
