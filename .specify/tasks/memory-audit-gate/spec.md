# Adicionar Fase memory-audit ao Gate Pipeline

## Contexto

Ignorar uma memória relevante durante implementação não tem consequência mensurável hoje —
nenhum gate falha por isso. Sem loop de feedback, instrução e injeção contextual (Specs A e B)
são necessárias mas insuficientes: o agent pode processar as memórias injetadas e ainda assim
não agir sobre elas. A fase `memory-audit` cria a consequência ausente: se uma constraint de
alta confiança era aplicável e não foi endereçada, o gate falha com diagnóstico claro e ação
requerida.

## Critérios de Sucesso

- `specify gate run --task <slug> --phase memory-audit` executa semantic search das memórias
  do tipo `constraint` contra o conteúdo de spec.md + arquivos modificados na task; retorna
  PASS ou FAIL com diagnóstico
- Gate falha (FAIL) quando pelo menos uma constraint com similaridade >= 0.75 não tem
  evidência de endereçamento nos arquivos modificados da task
- Evidência de endereçamento: conteúdo da constraint (ou termos-chave) aparece em ao menos
  um arquivo modificado, no plano da task, ou em uma entrada `memory link --kind not-applicable`
- Output de FAIL lista cada constraint não endereçada com: ID, conteúdo, fonte original,
  e o comando exato para marcar como not-applicable
- `specify memory link --kind not-applicable --memory <id> --task <slug> --note "<razão>"`
  persiste exceção explícita; gate subsequente aceita essa constraint como endereçada
- `specify gate history --task <slug>` exibe resultado de memory-audit junto com tests e lint
- Gate `memory-audit` é executado automaticamente antes da fase `tests` quando `gate run`
  roda sem `--phase` (pipeline completo)
- Quando nenhuma constraint atinge similaridade >= 0.75, gate retorna PASS sem ruído
- `specify memory link --kind not-applicable` sem `--note` é rejeitado — nota é obrigatória

## Restrições

- Depende de Spec B (contextual-injection) — sem injeção, o agent não sabe das constraints
  antes de implementar, tornando o audit punitivo em vez de preventivo
- Depende de `memory_edges` table (Spec D phase 1) para persistir not-applicable links
- Similaridade calculada sobre embeddings existentes — sem novo modelo
- Falso positivo (constraint flagrada indevidamente) deve ser resolvível via not-applicable
  sem fricção — o comando deve ter autocomplete de IDs disponíveis
- `gate run --skip-memory-audit` disponível para escape hatch explícito (auditável no histórico)
- Tempo total da fase memory-audit <= 5 segundos para tasks com até 50 memórias

## Fora de escopo

- Audit de memórias do tipo `pattern` ou `decision` (apenas `constraint` nesta spec)
- Sugestão automática de qual arquivo corrigir para endereçar a constraint
- Integração com CI/CD (gate roda localmente via CLI)
- Interface visual de audit no studio