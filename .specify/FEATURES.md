# Features — specify

Tracking de features existentes, planejadas e descartadas.

---

## ✅ Implementadas

### Core CLI
- `specify init` — inicializa `.specify/` com DB, INDEX.md, gitignore
- `specify task create/list/update/close/worktree-info` — gerenciamento de tasks
- `specify gate run/record/history/last` — execução e registro de gates de validação
- `specify memory set/get/list/search/delete/stats` — memória persistente com busca vetorial e métricas de uso
- `specify memory harvest` — extração retroativa de memórias de artefatos de tasks (spec.md, plan.md, result.md)
- `specify studio` — servidor local (FastAPI + uvicorn) com visualização de grafo de memórias

### Plugin Claude Code
- Hook `SessionStart` — injeta contexto do projeto (INDEX.md + tasks + memórias) automaticamente
- Skills: `specify.init`, `specify.new`, `specify.plan`, `specify.sdd`, `specify.review`, `specify.close`, `specify.memory`
- Prompts de memória em gatilhos obrigatórios: pós-GREEN (sdd), pré-gate (review), pré-close, ao criar spec (new)

### Persistência
- SQLite com schema versionado (PRAGMA user_version, 4 migrações)
- sqlite-vec + fastembed ONNX (bge-small-en-v1.5, 384 dims) para busca semântica
- Fallback para busca por substring quando fastembed indisponível
- Tabela `memory_searches` — log de cada busca (query, results_count, source, timestamp)

### Studio
- Grafo interativo com Sigma.js 2.4.0 + Graphology (UMD via CDN)
- Nós = memórias; arestas = similaridade coseno > 0,7; layout force-directed inline (sem deps externas)
- Sidebar: edição e deleção de memórias via PUT/DELETE `/api/memories/{id}`
- Painel Stats: buscas por origem, queries frequentes, buscas sem resultado

### Worktrees
- `specify task create --worktree` — cria branch `specify/<slug>` em `.claude/worktrees/<slug>/`
- `.worktreeinclude` template para copiar `specify.db` para worktrees
- `specify init` adiciona `.claude/worktrees/` ao `.gitignore` local

### Fluxo SDD
- Ciclo: `specify.new → specify.plan → specify.sdd → specify.review → specify.close`
- Commits atômicos ao longo do ciclo (RED/GREEN/REFACTOR/REVIEW/CLOSE)
- Estratégia de commits definida em `plan.md` (automático/controlado/manual)
- Artefatos por task: `spec.md`, `plan.md`, `sdd.log`, `review.md`, `result.md`

### Infraestrutura
- `install.sh` — instala uv, venv, symlinks, gitignore global
- `dev/symlink.sh` — dev mode: skill symlinks + hook em settings.json
- `Taskfile.yml` — task runner (test, test:e2e, lint, dev:install)
- 108 testes unitários + 12 e2e

---

## 🔄 Planejadas

### Próximas (alta prioridade)
- [ ] `specify context` — comando CLI que dumpa contexto completo do projeto (INDEX.md + tasks + memórias) para o agent (além do hook automático)
- [ ] `specify memory export` — exporta memórias para `.specify/memory/decisions.md`, `.specify/memory/patterns.md` (legível por humano, versionável)
- [ ] Busca cross-scope — `specify memory search` que busca em memórias de outras tasks além do scope global

### Qualidade
- [ ] Testes de integração do fluxo completo com worktree
- [ ] Cobertura de testes para `src/cli/` (hoje zero — coberto só por e2e)
- [ ] `specify gate run --phase adversarial` com sub-agent real (requer Workflow/Agent tool)

### UX / Ergonomia
- [ ] `specify status` — visão geral do projeto (tasks ativas, gates pendentes, memórias recentes)
- [ ] Output colorido no CLI (rich ou click.style)
- [ ] `specify task show <slug>` — exibe todos os artefatos de uma task (spec + plan + sdd.log + review + result)

### Distribuição
- [ ] `install.sh` compatível com macOS (homebrew path)
- [ ] `specify init` copia `.worktreeinclude` automaticamente (hoje é manual)
- [ ] Publicação pública do repo (após maturidade)

---

## ❌ Descartadas

| Feature | Razão |
|---------|-------|
| Plugin via marketplace Claude Code | Marketplace só aceita `source: github`; hook direto em settings.json é mais simples e robusto |
| sentence-transformers para embeddings | PyTorch ~1.5 GB; fastembed ONNX ~90 MB resolve o mesmo problema |
| ChromaDB / pgvector | Zero infra necessária com sqlite-vec co-localizado no projeto |
| `specify context` como comando exclusivo do SessionStart | Hook já injeta automaticamente; comando explícito é redundante para o fluxo normal |
| Multi-agent Workflow para review adversarial | Complexidade alta; review manual do agent é suficiente para o ciclo atual |
| Sincronização automática de DB entre worktrees | Intencional não sincronizar — worktree copia estado no momento de criação |
