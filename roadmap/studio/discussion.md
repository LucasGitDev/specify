# specify studio — discussão de design

Data: 2026-06-29

---

## Origem

Revisando `FEATURES.md`, surgiu a ideia de criar uma visualização interativa das memórias do SQLite — inspirada no Obsidian como segundo cérebro, mas com a vantagem de termos embeddings vetoriais reais.

A proposta evoluiu de "export para `.md`" (já planejado em FEATURES.md) para um comando `specify studio` que sobe um servidor web local com visualização em grafo interativo.

---

## Nós naturais no modelo de dados atual

- **Memórias** — coloridas por tipo: `decision` / `pattern` / `constraint`
- **Tasks** — por slug
- **Arquivos-fonte** — campo `source` em cada memória

## Arestas que já temos dados pra calcular

- **Scope**: memória → task (quando `scope != global`)
- **Semântica**: cosine similarity entre vetores armazenados (sqlite-vec + bge-small-en-v1.5)
- **Source**: memória → arquivo de origem

---

## Comparação de stacks

| Stack | Prós | Contras |
|---|---|---|
| FastAPI + D3.js | Zero build step, full control | Frontend JS à mão |
| **FastAPI + Sigma.js** | WebGL, ForceAtlas2 (mesmo algoritmo do Obsidian/Gephi), suave com centenas de nós | JS à mão |
| Streamlit | Pure Python, prototipagem rápida | Graph viz limitado (st-link-analysis insuficiente), sem WebSocket, layout control ruim |
| Dash + Cytoscape.js | Cytoscape é bom para grafos | Dep pesada, menos flexível |
| FastAPI + React | Melhor DX de frontend | Requer Node como dev dep — ruim para CLI tool |

**Decisão**: FastAPI + uvicorn + HTML único com Sigma.js e Graphology via CDN.

Motivo do Sigma.js: ForceAtlas2 é o que faz o grafo do Obsidian "respirar". E como temos embeddings reais, podemos fazer melhor que o Obsidian — que posiciona por links explícitos.

---

## Vantagem sobre o Obsidian

Obsidian posiciona nós por *links explícitos*. O specify tem **embeddings reais** — é possível calcular PCA 2D dos vetores e posicionar por *similaridade semântica*. Memórias sobre o mesmo tema clusteram automaticamente, sem link explícito. Isso é o que o Obsidian tenta simular com backlinks; nós temos estruturalmente.

---

## Edição no studio

Editar conteúdo de uma memória pelo studio altera o SQLite — sem problema. O fluxo já existe no CLI (`mem_db.update()` + `vec_db.upsert_embedding()`). O studio chama a mesma lógica via endpoint PUT. Única atenção: editar conteúdo precisa re-embedar (~200ms com fastembed), então o endpoint de update é async. Nada impeditivo.

---

## Feature set completo (backlog)

| Feature | Prioridade |
|---|---|
| Grafo semântico com arestas de cosine similarity | MVP |
| Filtros ao vivo por tipo e scope | MVP |
| Sidebar com edição inline + re-embed | MVP |
| Busca semântica com destaque no grafo | MVP |
| PCA positioning dos vetores (posição por semântica, não força) | v2 |
| Timeline view (eixo temporal, evolução do conhecimento) | v2 |
| Cluster automático com labels (k-means nos embeddings) | v2 |
| Task orbit view alternativo | v2 |
| Source tracking (clicar → arquivo de origem) | v2 |
| Diff view (o que mudou na última semana) | v2 |
