# specify — instruções para o agent

## Fluxo padrão

Para qualquer feature nova ou bug:

```
/specify.new <slug>     → criar spec do zero (entrevista guiada)
/specify.plan <slug>    → planejar antes de qualquer código
/specify.sdd <slug>     → RED→GREEN→REFACTOR
/specify.review <slug>  → verificar spec vs implementação
/specify.close <slug>   → gate final, commit, MR
```

Não pular etapas. Se spec já existe, começar pelo `/specify.plan`.

## Memória — usar proativamente

**Quando buscar:**
- Antes de qualquer implementação não trivial — `specify memory search "<domínio>"`
- Antes de propor uma abordagem — verificar se já foi decidido antes
- Resultado da busca encontrado → incorporar na spec/plano sem perguntar ao usuário o que ele já decidiu

**Quando persistir** (sem esperar o usuário pedir):
```bash
# Decisão técnica tomada em conversa ou implementação
specify memory set --type decision --content "<decisão>" --source "<slug>/sdd"

# Padrão descoberto ou confirmado no codebase
specify memory set --type pattern --content "<padrão>" --source "<slug>/sdd"

# Restrição encontrada que não está documentada
specify memory set --type constraint --content "<restrição>" --source "<slug>/sdd"
```

**Gatilhos obrigatórios no ciclo:**
- Pós-GREEN: uma decisão de implementação não óbvia → `memory set`
- Pós-review: constraint descoberta → `memory set`
- Pré-close: `memory search` para checar se ficou algo para trás
- Fora do ciclo: qualquer decisão tomada em conversa que afeta futuras tasks → `memory set` imediatamente

**O que NÃO persistir:** informação que já está na spec, no INDEX.md, ou que é óbvia da stack.

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
