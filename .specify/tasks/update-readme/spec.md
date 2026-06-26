# Atualizar README e criar CI com badges

## Contexto

O README está desatualizado (contagens de testes incorretas, URL do repo não preenchida) e não reflete o estado real do projeto. Não há CI configurado, então informações como cobertura e status dos testes ficam obsoletas manualmente.

## Critérios de Sucesso

- GitHub Actions executa lint + testes unitários + e2e em todo push/PR para main
- README exibe badges de CI status e cobertura atualizadas automaticamente
- README não contém contagens hardcoded de testes nem URLs de placeholder
- README cobre: o que é, como instalar, fluxo de uso, referência de skills e CLI
- Seção "Contribuindo" reflete os comandos reais do Taskfile (task test, task test:e2e, etc.)
- CI passa no estado atual do repositório

## Restrições

- Python 3.12+, uv como gerenciador de pacotes
- Sem serviços externos além do GitHub Actions nativo
- Cobertura via pytest-cov com relatório XML para badge

## Fora de escopo

- Tradução do README para inglês
- Documentação de API ou arquitetura detalhada
- Changelog ou versionamento semântico automatizado