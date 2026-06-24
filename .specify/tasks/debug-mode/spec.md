# Adicionar Debug Mode via SPECIFY_DEBUG

## Contexto

Quando o plugin falha — hook silencioso, artifact save ignorado, gate com comportamento inesperado — não há rastro do que aconteceu. `session_start.py` swallows exceções com `sys.exit(0)`. O CLI não registra operações. Diagnosticar problemas exige adivinhar.

## Critérios de Sucesso

- Quando `SPECIFY_DEBUG=1` está definido, o CLI escreve em `~/.claude/specify.log` cada operação executada: comando, projeto root detectado, DB path, resultado
- Quando `SPECIFY_DEBUG=1` está definido, `session_start.py` escreve no mesmo log em vez de `sys.exit(0)` silencioso em exceções — incluindo traceback completo
- O log usa formato `[ISO timestamp] [nível] mensagem` e faz append (não sobrescreve)
- Quando `SPECIFY_DEBUG=1` não está definido, nenhum arquivo de log é criado e o comportamento atual é preservado integralmente
- Se o arquivo de log não puder ser escrito (permissão, disco cheio), o comando continua normalmente sem erro — debug nunca bloqueia operação

## Restrições

- Sem dependências externas — apenas stdlib Python (`logging`, `os`, `pathlib`)
- Log path fixo: `~/.claude/specify.log`
- Não alterar interface dos comandos Click existentes

## Fora de escopo

- Flag `--debug` no CLI
- Rotação de log / tamanho máximo
- Log de queries SQL internas