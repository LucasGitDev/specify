---
name: specify.new
description: "Cria uma nova spec de task de forma guiada: define slug, entrevista o usuário sobre o problema, escreve spec.md estruturada com critérios de sucesso, e prepara para /specify.plan. Use quando o usuário quiser criar uma nova task, especificar um requisito, dizer 'quero implementar X', 'nova feature', 'novo endpoint', 'preciso de uma spec', ou usar '/specify.new'."
user-invocable: true
argument-hint: "Descrição livre do que precisa ser feito (ex: 'endpoint de healthcheck' ou 'cache de sessões com Redis')"
---

# specify new

Cria uma spec de task do zero de forma guiada. O resultado é um `spec.md` válido — com título, contexto, critérios de sucesso e edge cases — pronto para `/specify.plan`.

```
Definir slug → Entrevistar → Buscar contexto → Escrever spec → GATE: aprovação → Criar task
```

## Fase 0 — Verificar specify inicializado

```bash
ls .specify/INDEX.md 2>/dev/null && echo "ok" || echo "missing"
```

Se ausente: orientar `specify init` antes de continuar.

## Fase 1 — Definir slug

Se o usuário não forneceu argumento, perguntar:

> "Descreva em uma frase o que precisa ser implementado."

A partir da resposta, propor um slug em kebab-case (`add-healthcheck`, `cache-session-redis`, `fix-auth-token-expiry`). Confirmar com o usuário antes de continuar.

Verificar se já existe:
```bash
ls .specify/tasks/<slug>/spec.md 2>/dev/null && echo "existe" || echo "novo"
```

Se já existe: perguntar se quer sobrescrever ou usar slug diferente.

## Fase 2 — Buscar contexto do projeto

```bash
cat .specify/INDEX.md
specify memory search "<palavras-chave do problema>"
specify task list --status in_progress
```

Usar o contexto para:
- Entender a stack e convenções já estabelecidas
- Identificar decisões anteriores que impactam esta task
- Detectar tasks em andamento que possam conflitar

## Fase 3 — Entrevistar (perguntas uma por vez)

Fazer as perguntas necessárias para escrever uma spec completa. **Uma pergunta por vez.** Parar quando tiver informação suficiente para cobrir:

1. **O problema** — O que está faltando ou quebrando? Qual a dor?
2. **O comportamento esperado** — O que o sistema deve fazer após a mudança?
3. **Quem usa** — Qual serviço, usuário ou sistema consome isso?
4. **Casos de erro** — O que acontece quando algo dá errado? (input inválido, dependência fora, timeout)
5. **Edge cases** — Limites, concorrência, performance, idempotência?
6. **Restrições** — Algo que não pode mudar, prazo, dependência bloqueante?

Não fazer todas de uma vez. Se a resposta a uma pergunta já responde a próxima, pular.

Se o contexto do INDEX.md ou da memória já responder alguma pergunta, não perguntar — usar o contexto.

## Fase 4 — Escrever a spec

Criar o arquivo:
```bash
mkdir -p .specify/tasks/<slug>
```

Escrever `.specify/tasks/<slug>/spec.md` seguindo o template:

```markdown
# <Título claro e imperativo>

## Contexto

<O problema atual e por que precisa ser resolvido. 2-4 frases.>

## Critérios de Sucesso

- <comportamento observável e testável — caminho feliz>
- <comportamento observável e testável — caminho feliz 2>
- <comportamento em caso de erro>
- <edge case relevante>

## Restrições

- <o que não pode mudar>
- <dependência, prazo, ou constraint técnico>

## Fora de escopo

- <o que explicitamente não será feito nesta task>
```

**Regras da spec:**
- Critérios devem ser testáveis — se não dá para escrever um teste, o critério é vago
- Linguagem de domínio, não jargão técnico de implementação
- Sem mencionar como implementar — só o que deve acontecer
- Mínimo 2 critérios de caminho feliz + 1 critério de erro

## Fase 5 — Exibir e aguardar aprovação

Exibir a spec completa formatada e perguntar:

> "A spec está correta? Posso prosseguir para `/specify.plan <slug>`?"

Se o usuário pedir ajustes: aplicar e exibir novamente. Repetir até aprovação.

Se aprovado: confirmar

```
Spec criada: .specify/tasks/<slug>/spec.md
Próximo passo: /specify.plan <slug>
```

## Quando NÃO usar

- Spec já existe e só precisa de planejamento — usar `/specify.plan` diretamente
- Bug óbvio de uma linha sem necessidade de spec — usar `/specify.sdd` com spec mínima inline
- Exploração/prototipagem descartável — specify é para código que vai para produção
