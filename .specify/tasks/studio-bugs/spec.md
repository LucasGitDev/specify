# Corrigir bugs de layout e UI no Studio

## Contexto

O Studio (Sigma.js + Graphology) apresenta dois bugs após a implementação studio-v2:
1. Nós de task aparecem distantes dos nós de memória com os quais têm edges de scope-link,
   tornando as conexões visualmente irrelevantes.
2. Ao clicar em qualquer botão de filtro no painel superior esquerdo, todos os botões e
   elementos do painel somem, deixando apenas o grafo e o painel lateral.

## Critérios de Sucesso

- Nós de task com edges de scope-link aparecem visualmente próximos das memórias conectadas
  no layout inicial do grafo
- Edges de scope-link são visivelmente distintos dos edges semânticos (cor/opacidade diferente)
- Botões de filtro permanecem visíveis e funcionais após qualquer clique de toggle
- Clicar em um filtro ativo oculta os nós daquele tipo; clicar novamente os reexibe
- Nenhum elemento do painel de controle desaparece durante a interação com filtros
- O estado ativo/inativo de cada botão é refletido visualmente (botão escurecido quando filtro inativo)

## Restrições

- IDs de task usam prefixo t:<slug> — não alterar esse esquema
- Backend /api/graph e /api/tasks/{slug} não devem ser modificados
- O fix deve funcionar com Sigma.js + Graphology já em uso; sem trocar de lib de visualização

## Fora de escopo

- Redesign visual completo do Studio
- Adição de novos tipos de filtro ou novos painéis
- Performance de grafos com >500 nós