# Specify — Project Index

## Stack
- Language: python
- Test: `pytest`
- Lint: `ruff check .`
- Format: `ruff format --check .`

## Architecture

```
src/cli/        ← comandos Click (cmd_init, cmd_task, cmd_gate, cmd_memory)
src/db/         ← CRUD SQLite (tasks, gates, memory, vectors)
src/core/       ← lógica pura (lang_detector, gate_validator, spec_reader, worktree, project)
src/embeddings/ ← provider fastembed + NullProvider
src/hooks/      ← session_start.py (SessionStart hook do Claude Code)
skills/         ← SKILL.md por skill (specify.init, .new, .plan, .sdd, .review, .close, .memory)
templates/      ← index_md.template, worktreeinclude
tests/unit/     ← testes unitários (pytest)
tests/e2e/      ← smoke tests end-to-end
```

## Constraints

- Skills são prompts (SKILL.md), não código — não testar com pytest
- CLI Python com Click — sem scripts bash de lógica
- DB via SQLite + sqlite-vec (sem ORM); schema versionado por PRAGMA user_version
- vec0 não suporta INSERT OR REPLACE — usar DELETE + INSERT
- Testes unitários não dependem de fastembed — vetores hardcoded
- Conventional commits: inglês, imperativo, 1 linha, sem longer description
- Symlinks em ~/.claude/skills/specify.* — não usar sistema de marketplace do Claude Code
