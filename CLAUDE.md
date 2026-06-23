# specify — instruções para o agent

## Fluxo padrão

Para qualquer feature nova ou bug com spec definida:

```
/specify plan <slug>    → planejar antes de qualquer código
/specify sdd <slug>     → RED→GREEN→REFACTOR
/specify review <slug>  → verificar spec vs implementação
/specify close <slug>   → gate final, commit, MR
```

Não pular etapas. Sem spec → usar `/specify plan` para criar.

## Memória — usar proativamente

Antes de implementar algo não trivial:
```bash
specify memory search "<domínio do que vai implementar>"
```

Após qualquer decisão arquitetural tomada em conversa:
```bash
specify memory set --type decision --content "<decisão>"
```

Ao descobrir padrão no codebase:
```bash
specify memory set --type pattern --content "<padrão>"
```

Ao encontrar restrição não documentada:
```bash
specify memory set --type constraint --content "<restrição>"
```

## Regras de gate

- **GREEN falhou 3 iterações** → escalar para humano com output completo do último gate
- **REVIEW com críticos após 2 ciclos** → escalar para humano com lista de críticos
- Nunca modificar testes para fazê-los passar — se necessário, a spec estava errada: atualizar spec primeiro
- Nunca pular fase REFACTOR (lint + fmt + re-run tests)

## Comandos de referência rápida

```bash
specify task list                                # tasks ativas
specify task create --slug <slug> --title "..."  # nova task
specify task create --slug <slug> --worktree     # com isolamento
specify gate run --task <slug> --phase tests     # executar gate
specify gate history --task <slug>               # histórico de gates
specify memory search "<query>"                  # busca semântica
specify memory list --type decision              # listar decisões
```

## Contexto automático

O hook `SessionStart` injeta automaticamente no início de cada sessão:
- Stack do projeto (de `.specify/INDEX.md`)
- Tasks ativas
- Memórias recentes (últimas 5 por tipo)

Se o contexto não aparecer: verificar que `.specify/` existe (`specify init`).
