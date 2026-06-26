# Como o specify funciona

**specify** é um plugin Claude Code que transforma uma sessão de chat em um ciclo de desenvolvimento estruturado — da spec ao merge, com estado persistente entre sessões.

## O problema que resolve

Sem estrutura, um agente de IA faz isso:

```
você: "implementa autenticação JWT"

agente: [escreve 300 linhas de código]
        [passa nos testes que ele mesmo criou]
        [não cobre revogação de token]
        [não trata expiração corretamente]
        [você descobre 3 dias depois no code review]
```

O agente não é burro — ele é rápido demais. Pula a parte onde você define o que "implementa autenticação JWT" **realmente significa**.

## O que o specify faz diferente

Força o fluxo correto antes de qualquer código:

```
/specify.new add-jwt-auth     ← entrevista guiada vira spec estruturada
/specify.plan add-jwt-auth    ← valida critérios, propõe ciclo, aguarda sua aprovação
/specify.sdd add-jwt-auth     ← RED → GREEN → REFACTOR com gates automáticos
/specify.review add-jwt-auth  ← tenta refutar a implementação contra a spec
/specify.close add-jwt-auth   ← gates verificados, commit, MR
```

Cada fase tem um **gate** — uma verificação que precisa passar antes de avançar. O agente não avança por conta própria.

## Como o estado persiste

Cada projeto tem um `.specify/` local:

```
.specify/
├── INDEX.md        ← você escreve aqui: stack, arquitetura, restrições
├── specify.db      ← SQLite com tasks, gates, histórico (gitignored)
└── tasks/
    └── add-jwt-auth/
        ├── spec.md    ← fonte de verdade da intenção
        ├── plan.md    ← ciclo aprovado por você
        ├── gates.md   ← histórico de iterações RED/GREEN/REFACTOR
        └── result.md  ← resumo final gerado no close
```

O **hook `SessionStart`** lê o `.specify/` e injeta automaticamente no contexto do Claude:
- Stack do projeto (do `INDEX.md`)
- Tasks abertas e seus status
- Últimas memórias (decisões, padrões, restrições)

Você abre uma nova sessão e o agente já sabe onde parou.

## O ciclo SDD em detalhe

### RED — testes primeiro

O agente lê a spec e escreve testes para cada critério **antes de escrever código**. Os testes precisam falhar — se passarem, são falsos positivos.

```bash
specify gate run --task add-jwt-auth --phase red
# ✗ 12 testes falhando (esperado)
```

### GREEN — implementação mínima

Código mínimo para fazer os testes passarem. O agente tem até 3 iterações antes de escalar para você.

```bash
specify gate run --task add-jwt-auth --phase green
# ✓ 12/12 testes passando
```

### REFACTOR — lint + fmt + re-run

Sem novas funcionalidades. Só limpeza.

```bash
specify gate run --task add-jwt-auth --phase refactor
# ✓ lint clean, fmt clean, 12/12 ainda passando
```

### REVIEW — adversarial

O agente tenta **refutar** a implementação contra a spec. Classifica achados em crítico / importante / sugestão. Zero críticos para avançar.

### CLOSE — gate final

Verifica todos os gates, gera `result.md`, faz commit e abre MR.

## Memória semântica

O specify mantém uma memória por projeto — decisões arquiteturais, padrões encontrados, restrições descobertas:

```bash
specify memory set --type decision --content "usar refresh token com rotação, não stateless puro"
specify memory search "autenticação"
# → retorna memórias relevantes por similaridade semântica
```

Usa [fastembed](https://github.com/qdrant/fastembed) localmente (ONNX, ~90MB, sem API key).

---

**Próximo passo:** [instalação e primeiro uso](../README.md#instalação).
