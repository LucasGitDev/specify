---
name: specify.init
description: "Inicializa o framework specify num projeto: verifica CLI, cria .specify/, detecta stack Go/Python/TS/Rust, gera INDEX.md. Use quando o usuário quiser configurar specify, inicializar SDD num projeto, usar '/specify init', ou começar a usar spec-driven development num repositório."
user-invocable: true
argument-hint: "Opcional: caminho do projeto (padrão: diretório atual)"
---

# specify init

Configura o framework specify no projeto atual.

## Fase 0 — Verificar CLI

```bash
specify --help 2>/dev/null && echo "ok" || echo "not found"
```

Se não encontrado, orientar instalação:

```bash
# Dev mode (repo clonado)
cd ~/projects/specify && bash dev/symlink.sh

# Ou via uv
cd ~/projects/specify && uv pip install -e .
```

Verificar que `~/.local/bin` está no PATH. Se não estiver, orientar:
```bash
export PATH="$HOME/.local/bin:$PATH"
# adicionar ao ~/.zshrc ou ~/.bashrc para persistir
```

## Fase 1 — Inicializar

```bash
specify init
# Se já existir:
specify init --force
```

Output esperado:
```
specify inicializado em .specify/
  linguagem: go
  teste:     go test ./...
  lint:      go vet ./...
```

Se linguagem não detectada: orientar edição manual de `.specify/INDEX.md`.

## Fase 2 — Personalizar INDEX.md

Abrir `.specify/INDEX.md` e orientar o usuário a preencher:

```markdown
## Architecture
<!-- Descreva a estrutura de pastas, separação de camadas -->

## Constraints  
<!-- Regras específicas: sem mocks de repositório concreto, cobertura mínima, etc. -->
```

Para projetos wm-users (Go + Echo + Tsuru), sugerir preencher com base no `.spelunk/scan.md` se existir.

## Fase 3 — Próximos passos

```
specify inicializado. Próximos passos:

1. Edite .specify/INDEX.md com arquitetura e restrições do projeto
2. Crie a spec da primeira task:
   mkdir -p .specify/tasks/<slug>
   # escreva .specify/tasks/<slug>/spec.md
3. Execute /specify plan <slug> para propor o ciclo de desenvolvimento
```

## Quando NÃO usar

- Projeto já tem `.specify/` inicializado — use `specify init --force` apenas se quiser resetar
