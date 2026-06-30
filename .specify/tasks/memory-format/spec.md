# Reformar Formato de Memórias para Padrão Prescritivo

## Contexto

Memórias persistidas como fatos históricos ("go build passa sem erros") são ignoradas pelo
agent durante implementação — processadas como observação passada, não como regra ativa.
Memórias com verbo de ação e prefixo por tipo ("ALWAYS: run go build ./... before gating")
são semanticamente distinguíveis como instruções e têm maior probabilidade de serem seguidas.
O problema não é de infraestrutura de busca — é de qualidade do sinal armazenado.

## Critérios de Sucesso

- Ao executar `specify memory set --type constraint "..."`, o output inclui sugestão de
  reformatação com prefixo adequado ao tipo (ALWAYS:/NEVER:/CHECK:) caso o conteúdo não
  comece com prefixo reconhecido
- Ao executar `specify memory set --type pattern "..."`, o output sugere estrutura
  WHEN ... DO ... caso ausente
- Ao executar `specify memory set --type decision "..."`, o output sugere prefixo DECIDED:
  caso ausente
- A sugestão é não-bloqueante: memória é salva independentemente do formato
- `specify memory reformat [--id <id>] [--dry-run]` exibe versão reformatada de memórias
  sem prefixo; sem `--dry-run` atualiza o conteúdo no banco
- `specify memory reformat` sem `--id` processa todas as memórias sem prefixo reconhecido
- `specify memory list` exibe prefixo com destaque visual distinto do restante do conteúdo
- Memórias já com prefixo reconhecido não recebem sugestão no `memory set`

## Restrições

- Não bloquear `memory set` por ausência de prefixo — sugestão apenas
- Não alterar schema do banco (sem nova coluna); prefixo é parte do campo `content`
- `reformat` sem `--dry-run` deve confirmar antes de modificar mais de 5 registros
- Prefixos reconhecidos: `ALWAYS:`, `NEVER:`, `CHECK:`, `WHEN`, `DECIDED:`, `AVOID:`
- Reformat não usa LLM externo — reformula via regra determinística por tipo + conteúdo
  existente; sem dependência de rede

## Fora de escopo

- Validação obrigatória de formato (bloqueio no save)
- Novos tipos de memória além dos existentes (decision, pattern, constraint)
- Alteração no formato de busca semântica ou embeddings
- Interface visual no studio para reformat