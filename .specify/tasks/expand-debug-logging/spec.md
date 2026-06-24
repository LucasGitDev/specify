# Expandir Logs de Debug para Observabilidade do Framework

## Contexto

O debug mode (SPECIFY_DEBUG=1) foi implementado mas captura pouco: só o início do comando CLI e entradas do session_start. Para melhorar o framework é necessário ter visibilidade completa de tudo que acontece numa sessão — cada operação do CLI com seus argumentos e resultados, e cada ação do agente (tool calls) com input/output — de forma que o log seja uma trilha auditável usável para detectar onde o fluxo quebra.

## Critérios de Sucesso

- artifact save loga: path de destino + primeiros 200 chars do content salvo
- gate run loga: comando executado, duração, status (pass/fail) e output completo
- gate record loga: task/phase/type/status registrados
- task create/update/close loga: slug + mudança de status
- memory search loga: query + número de resultados retornados
- session_start loga: lista de tasks ativas e tipos de memória carregados injetados na sessão
- Um hook PostToolUse em settings.json appenda em specify.log cada tool call do agente (Bash, Read, Write, Edit) com: ferramenta, input resumido (primeiros 300 chars), status de saída — quando SPECIFY_DEBUG=1
- O comando specify log tail exibe as últimas N linhas do log (padrão: 50) para inspeção rápida
- O comando specify log clear apaga o arquivo de log

## Restrições

- Sem dependências externas — apenas stdlib Python
- Log path fixo: ~/.claude/specify.log (mesma convenção)
- Hook PostToolUse é bash puro em settings.json — sem Python extra
- Não alterar comportamento existente quando SPECIFY_DEBUG ausente

## Fora de escopo

- Log de queries SQL internas
- Rotação / tamanho máximo de log
- Log de tool calls de outros plugins
- Parsing/análise dos logs (apenas geração)