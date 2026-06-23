---
name: specify-memory
description: "Gerencia memórias persistentes do projeto: salva decisões arquiteturais, padrões de código e restrições; busca contexto relevante antes de implementar. Use quando o usuário quiser salvar uma decisão, buscar o que já foi decidido, executar '/specify memory', ou quando perceber que uma decisão importante foi tomada e deve ser persistida."
user-invocable: true
argument-hint: "Ação: set|get|list|search|delete. Ex: 'search autenticação' ou 'set decision JWT via lestrrat-go'"
---

# specify memory

Interface para memórias persistentes do projeto. Usa busca vetorial (semântica) quando disponível, substring como fallback.

## Comandos

### Salvar memória

```bash
# Decisão arquitetural
specify memory set --type decision --content "<decisão>" [--scope global|<task-slug>]

# Padrão descoberto no codebase
specify memory set --type pattern --content "<padrão>"

# Restrição do projeto
specify memory set --type constraint --content "<restrição>"
```

Tipos:
- `decision` — decisão tomada que afeta implementações futuras ("usamos JWT", "não mockar repositório concreto")
- `pattern` — padrão observado no codebase ("handlers em api/, lógica em pkg/service/")
- `constraint` — restrição hard ("authn é módulo versionado, mudanças exigem nova tag")

### Buscar

```bash
# Busca semântica (ou substring como fallback)
specify memory search "<query>"

# Listar por tipo
specify memory list --type decision
specify memory list --type pattern
specify memory list --type constraint

# Listar por escopo de task
specify memory list --scope <task-slug>
```

### Recuperar e remover

```bash
specify memory get <id>
specify memory delete <id>
```

## Quando usar sem ser pedido

O agent deve usar `specify memory` proativamente nestas situações:

**Antes de implementar algo não trivial:**
```bash
specify memory search "<domínio do que vai implementar>"
```
Evita reinventar decisões já tomadas.

**Após qualquer decisão arquitetural tomada em conversa:**
```bash
specify memory set --type decision --content "<decisão tomada>"
```
Exemplos de quando salvar:
- "Vamos usar Redis para cache de sessões" → salvar
- "Optamos por não usar goroutines nesse handler por simplicidade" → salvar
- "Decidimos retornar 404 ao invés de 400 quando recurso não existe" → salvar

**Ao descobrir padrão relevante no codebase:**
```bash
specify memory search "padrão de <algo>"
# Se não existir:
specify memory set --type pattern --content "<padrão observado>"
```

**Ao encontrar restrição não documentada:**
```bash
specify memory set --type constraint --content "<restrição descoberta>"
```
Exemplos:
- "Módulo authn precisa de nova tag antes de ser consumido" → constraint
- "Não usar goroutines sem context.Context" → constraint

## Integração com o fluxo

| Fase | Uso típico |
|------|-----------|
| `/specify plan` | `memory search` para buscar contexto relevante |
| `/specify sdd` | `memory search` antes de implementar; `memory set` ao tomar decisão |
| `/specify review` | `memory list --type constraint` para verificar restrições |
| `/specify close` | `memory set` para persistir decisões tomadas durante a task |

## Quando NÃO usar

- Informações já documentadas no `INDEX.md` — não duplicar
- Estado temporário da sessão — memória é persistente entre sessões
- Detalhes de implementação óbvios que qualquer dev conheceria
