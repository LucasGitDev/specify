---
name: specify-init
description: "Inicializa o framework specify num projeto Go: cria .specify/, banco de dados, detecta stack. Use quando o usuário quiser configurar o specify num projeto, usar '/specify init', ou começar a usar SDD num repositório Go."
user-invocable: true
---

# specify init

Inicializa o framework specify no projeto atual.

## O que faz

1. Detecta raiz do projeto (procura `go.mod`, `.git`)
2. Cria `.specify/` com estrutura de diretórios
3. Inicializa `specify.db` com schema versionado
4. Gera `.specify/INDEX.md` com stack detectada
5. Adiciona `specify.db` ao `.gitignore` local

## Como usar

```bash
specify init
specify init --force  # reinicializar
```

## Próximos passos após init

- Edite `.specify/INDEX.md` com arquitetura e restrições do projeto
- Crie specs de tarefas em `.specify/tasks/<slug>/spec.md`
- Use `/specify plan <slug>` para propor o ciclo de desenvolvimento
