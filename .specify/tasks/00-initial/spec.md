# Build the specify framework from scratch

## Contexto

Construir o specify como plugin Claude Code para Spec-Driven Development (SDD) com TDD e Agentic SDLC. O projeto nasce da necessidade de um framework coeso que cubra todo o ciclo — da spec ao merge — com estado persistente por projeto, memória vetorial e suporte a worktrees.

## Critérios de Sucesso

- CLI `specify` operacional com subcomandos: init, task, gate, memory
- Plugin Claude Code com hook SessionStart que injeta contexto do projeto automaticamente
- Skills coordenadas: specify.new, specify.plan, specify.sdd, specify.review, specify.close, specify.memory
- Estado persistente via SQLite + sqlite-vec (memória vetorial com fastembed ONNX)
- Suporte a worktrees isolados para paralelismo de tasks
- Fluxo end-to-end: /specify.new → /specify.plan → /specify.sdd → /specify.review → /specify.close
- 79 testes passando (67 unit + 12 e2e)

## Restrições

- Python 3.12+ via uv (sem pip do sistema)
- Skills como SKILL.md (prompts), não código Python
- Skills instaladas via symlinks em ~/.claude/skills/, não via marketplace do Claude Code
- Hook SessionStart registrado diretamente em settings.json
