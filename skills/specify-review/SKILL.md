---
name: specify-review
description: "Faz review adversarial de uma implementação contra a spec: classifica findings em crítico/importante/sugestão, tenta corrigir críticos automaticamente, registra gate de review. Use quando o usuário quiser revisar uma implementação, executar '/specify review', checar spec vs código, ou após '/specify sdd' concluir."
user-invocable: true
argument-hint: "Slug da task (ex: 'add-healthcheck')"
---

# specify review

Review adversarial: tenta refutar a implementação contra a spec. Cada critério é verificado. Findings classificados por severidade.

```
Contexto → Ler diff → Verificar critérios → Classificar findings → Corrigir críticos → Gate
```

## Fase 0 — Pré-verificação

```bash
specify task status <slug>
specify gate history --task <slug>
```

Verificar que gates obrigatórios passaram antes do review:
- `green/tests` com status `pass`
- `refactor/lint` com status `pass`

Se algum estiver ausente ou `fail`:
```
Review bloqueado. Gates pendentes:
- <gate ausente>: execute /specify sdd <slug> primeiro
```

## Fase 1 — Contexto

```bash
# Spec original
cat .specify/tasks/<slug>/spec.md

# Diff da implementação
git diff main -- . 2>/dev/null || git diff HEAD~1 -- .
```

Extrair critérios da spec. Para cada critério, preparar verificação.

## Fase 2 — Review por critério

Para cada critério da spec:

**Verificar**:
1. Existe código que endereça este critério?
2. Há testes cobrindo o caminho feliz?
3. Há testes cobrindo casos de erro?
4. Edge cases identificados na spec estão cobertos?

**Classificar finding**:

| Severidade | Definição | Bloqueante? |
|-----------|-----------|-------------|
| `crítico` | Critério não coberto, comportamento errado, teste faltando para caminho feliz | Sim |
| `importante` | Edge case sem teste, erro não tratado, inconsistência com padrão da memória | Sim se > 2 |
| `sugestão` | Melhoria de legibilidade, nomenclatura, refactor opcional | Não |

Exibir findings:
```
Review — <slug>

Critério 1: <texto> ✓
Critério 2: <texto> ✗ CRÍTICO
  → Função X não trata o caso Y descrito na spec

Critério 3: <texto> ✓
  → sugestão: renomear variável Z para maior clareza

Resumo: 1 crítico, 0 importantes, 1 sugestão
```

## Fase 3 — Correção de críticos (max 2 ciclos)

Para cada `crítico` e `importante` bloqueante:
1. Corrigir código e/ou teste
2. Re-executar gate afetado:
```bash
specify gate run --task <slug> --phase green --iteration review-<N>
```

Se críticos persistirem após 2 ciclos:
```
BLOQUEADO no review (2 ciclos de correção).

Findings não resolvidos:
- <detalhe>

Aguardando orientação humana.
```

## Fase 4 — Registrar gate

Se zero críticos:
```bash
specify gate record --task <slug> --phase review --type adversarial --status pass \
  --output "0 críticos, <N> importantes resolvidos, <M> sugestões"
specify task update <slug> --status review
```

Se críticos após 2 ciclos:
```bash
specify gate record --task <slug> --phase review --type adversarial --status fail \
  --output "<lista de críticos não resolvidos>"
```

```
Review concluído — <slug>
  Críticos:   0 ✓
  Importantes: <N> resolvidos
  Sugestões:  <M> (não bloqueantes)

Próximo passo: /specify close <slug>
```

## Quando NÃO usar

- Task sem gates `green` e `refactor` passando — executar `/specify sdd` primeiro
- Task já `closed` — ciclo encerrado
