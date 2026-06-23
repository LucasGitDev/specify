---
name: specify.sdd
description: "Executa o loop RED→GREEN→REFACTOR de uma task com spec: escreve testes (RED), verifica falha, implementa código mínimo (GREEN), verifica pass, roda lint/fmt (REFACTOR). Integrado ao CLI specify para persistência de gates. Use quando o usuário quiser implementar uma task, executar '/specify sdd', rodar red/green/refactor, ou após '/specify plan' ser aprovado."
user-invocable: true
argument-hint: "Slug da task (ex: 'add-healthcheck')"
---

# specify sdd

Executa o loop **RED → GREEN → REFACTOR** de uma task, registrando cada gate no DB via `specify gate run`.

A spec define o que implementar. Os gates definem quando cada fase está completa. Não pule fases.

```
Ler spec → RED (testes) → gate red → GREEN (impl) → gate green → REFACTOR (lint/fmt) → gate refactor
```

## Fase 0 — Setup

```bash
# Verificar task existe e está in_progress
specify task status <slug>
```

Se status for `planned`: orientar executar `/specify plan <slug>` primeiro.  
Se status for `review` ou `closed`: avisar que task já passou dessa fase.

```bash
# Ler spec e plan
cat .specify/tasks/<slug>/spec.md
cat .specify/tasks/<slug>/plan.md 2>/dev/null || echo "(sem plan.md)"
```

Exibir resumo:
```
SDD — <slug>
  Critérios: <N> encontrados
  Linguagem: <detectada automaticamente pelo gate run>
Iniciando RED...
```

## Fase RED — Escrever testes

Para cada critério da spec, derivar:
1. **Caminho feliz** — input válido, output esperado
2. **Edge cases** — limites, zero values, strings vazias
3. **Casos de erro** — inputs inválidos, falhas esperadas

Convenções por linguagem:
- **Go**: `<arquivo>_test.go`, usar `testify/assert` e `testify/require`, nome `TestX_CenárioDescritivo`
- **Python**: `test_<modulo>.py`, usar `pytest` com fixtures
- **TypeScript**: `<arquivo>.test.ts`, usar `jest` ou `vitest`

Não implementar código de produção nesta fase. Stubs vazios apenas para compilar.

Após escrever os testes:
```bash
specify gate run --task <slug> --phase red --iteration 1
```

**Gate RED**: testes devem **falhar**. Se passarem — falso positivo. Investigar e corrigir antes de avançar.

Registrar no log:
```bash
specify gate record --task <slug> --phase red --type tests --status fail --iteration 1 \
  --output "N testes falhando (esperado)"
```

```
RED verificado:
  ✗ <N> testes falhando (esperado)
  ✓ <M> testes preexistentes passando
```

## Fase GREEN — Implementar (loop, max 3 iterações)

Implementar um critério por vez — código mínimo para fazer os testes passarem. Sem otimização, sem abstrações não pedidas pela spec.

Após cada critério:
```bash
specify gate run --task <slug> --phase green --iteration <N>
```

Se todos passarem:
```
GREEN verificado:
  ✓ <N> testes passando
  ✗ 0 falhando
```
→ Avançar para REFACTOR.

Se algum falhar e `iter < 3`: corrigir implementação e repetir.

Se `iter == 3` e ainda falhando:
```
BLOQUEADO na fase GREEN (3 iterações).

Erro:
<output completo do gate run>

Aguardando orientação.
```
Não avançar. Escalar para o humano com o output completo.

**Regras GREEN**:
- Não modificar testes para fazê-los passar — se necessário, a spec estava errada: atualizar spec primeiro
- Manter projeto compilando entre implementações
- Não mais de ~50 linhas sem rodar os testes

## Fase REFACTOR — Lint, fmt e re-verificação

```bash
# Lint
specify gate run --task <slug> --phase lint

# Formatter
specify gate run --task <slug> --phase fmt
```

Corrigir todos os erros reportados. Não desativar regras inline para passar.

Aplicar formatação:
- Go: `gofmt -w .`
- Python: `ruff format .`
- TypeScript: `prettier --write .` (se configurado)

Re-executar testes para confirmar que refactor não quebrou comportamento:
```bash
specify gate run --task <slug> --phase green --iteration final
```

**Gate REFACTOR**: lint pass + fmt pass + testes ainda passando.

```
REFACTOR:
  ✓ lint: limpo
  ✓ fmt: aplicado
  ✓ testes pós-refactor: <N> passando
```

## Resultado final

```bash
specify gate history --task <slug>
specify task update <slug> --status review
```

```
═══════════════════════════════════════════════════
  SDD concluído — <slug>
═══════════════════════════════════════════════════

  RED      ✓  <N> testes escritos
  GREEN    ✓  <N> testes passando (iter <N>)
  REFACTOR ✓  lint limpo, fmt aplicado

  Próximo passo: /specify review <slug>
═══════════════════════════════════════════════════
```

## Sinais de alerta

- Testes passam na fase RED → falso positivo, corrigir testes
- Necessidade de modificar teste para passar → spec errada, atualizar spec primeiro
- Mais de 100 linhas sem rodar gate → pare, rode `specify gate run`
- REFACTOR quebra testes → desfazer, implementar diferente
- Linter com regras desativadas inline → não fazer, corrigir o código

## Quando NÃO usar

- Task sem spec — usar `/specify plan` primeiro
- Hotfix de uma linha óbvio sem spec — overhead não justificado
- Task já em status `review` ou `closed` — ciclo já completado
