# Injetar Memórias nos Momentos de Transição de Fase

## Contexto

O hook `session_start` injeta memórias uma vez no início da sessão, antes do agent saber o
que vai implementar. Por recency bias, o conteúdo injetado no início fica centenas de tokens
atrás no momento da decisão real. A instrução em CLAUDE.md para rodar `specify memory search`
antes de implementar não é seguida consistentemente porque não há gatilho no momento certo.
A solução é mover a injeção para os comandos de transição de fase — onde o contexto relevante
é conhecido e a resposta do comando é processada ativamente pelo agent.

## Critérios de Sucesso

- `specify task create <slug> --title "..."` executa semantic search contra o título e
  retorna seção "Relevant prior knowledge" no output antes de confirmar a criação, listando
  até 5 memórias relevantes com prefixo de tipo
- Quando nenhuma memória relevante é encontrada (similaridade < 0.5), a seção é omitida
  (sem ruído de "nenhuma memória encontrada")
- `specify plan <slug>` inclui seção "Known constraints" no template de plano gerado,
  populada com constraints e decisions relevantes à task (semantic search contra spec.md)
- Seção "Known constraints" é gerada mesmo se spec.md não existir — usa título da task
- `specify gate run --task <slug> --phase tests` imprime checklist de constraints da task
  imediatamente antes de rodar o gate; cada item é a constraint formatada como pergunta
  verificável
- Checklist pré-gate não bloqueia execução — é output informativo antes do resultado
- Se task não tem constraints relevantes (< 0.4 similaridade), checklist é omitido
- Semantic search em `task create` e `gate run` completa em menos de 2 segundos

## Restrições

- Depende de Spec A (memory-format) para que o conteúdo injetado seja prescritivo
- Não modificar comportamento atual de `session_start` — injeção contextual é adicional,
  não substituta
- Semantic search usa embeddings já existentes (vec_memories) — sem novo modelo ou índice
- Task create com `--no-search` suprime a busca (para scripts e automações)
- Output de "Relevant prior knowledge" não deve exceder 15 linhas para não dominar o output
  do comando

## Fora de escopo

- Modificar o template do plano além da seção "Known constraints"
- Injeção em `specify sdd` ou outros subcomandos além dos três especificados
- Ranking por confiança de memórias (isso é Spec C / graph-edges)
- Checklist interativo (checkbox que o agent marca) — apenas output textual