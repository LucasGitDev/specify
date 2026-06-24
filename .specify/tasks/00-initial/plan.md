# Plan: 00-initial

**Data**: 2026-06-23
**Spec**: .specify/tasks/00-initial/spec.md
**Status**: concluído

## Etapas executadas

| Etapa | Descrição | Status |
|-------|-----------|--------|
| 1 | Scaffolding e CLI base | ✓ concluído |
| 2 | Memória e contexto (sqlite-vec + fastembed) | ✓ concluído |
| 3 | Tasks, gates e gate validator | ✓ concluído |
| 4 | Skills (6 skills SKILL.md) | ✓ concluído |
| 5 | Worktree e paralelismo | ✓ concluído |
| 6 | Polimento e distribuição | ✓ concluído |

## Decisões de arquitetura

- uv ao invés de pip (pip não disponível no sistema)
- fastembed (ONNX) ao invés de sentence-transformers (PyTorch pesado)
- Hook direto em settings.json ao invés de marketplace (marketplace só aceita github)
- Skills com prefixo `specify.` ao invés de `specify-` (convenção da comunidade)
- vec0 não suporta INSERT OR REPLACE — padrão: DELETE + INSERT
- Symlinks em ~/.claude/skills/ — mesmo padrão do caveman

## Worktree

não — sessão principal
