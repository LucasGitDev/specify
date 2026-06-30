# Adicionar Tasks como Nós no Grafo do Studio

## Contexto

O studio atual visualiza apenas memórias. O banco já possui a tabela `tasks` com slug, title e status, e memórias têm campo `scope` que referencia o slug da task geradora. O grafo fica incompleto sem mostrar a estrutura de tasks que originou as memórias — não é possível responder "de onde veio essa decisão?".

## Critérios de Sucesso

- Tasks aparecem no grafo como nós de tamanho e cor distintos das memórias (roxo, maior)
- Arestas `scope-link` conectam cada task aos nós de memória do mesmo scope (cor diferente das arestas semânticas)
- Tasks sem memórias aparecem no grafo (nó isolado visível)
- Clicar em um nó de task abre sidebar com: title, status, gates passados, link para `result.md`
- Filtro por tipo no toolbar inclui "task" como quarta categoria e funciona independentemente dos outros tipos
- GET `/api/graph` retorna tasks como nós e scope-links como arestas no formato existente

## Restrições

- Sem novas dependências Python além das já instaladas
- Reutilizar estrutura existente de `graph.py` (dataclasses, `build_graph()`)
- O endpoint `/api/graph` deve manter retrocompatibilidade com campos existentes de nodes e edges
- Arestas scope-link têm `kind: "scope"` (distinto de `kind: "semantic"`)

## Fora de escopo

- PCA positioning ou clustering automático de tasks
- Timeline view ou task orbit view
- Source tracking (arquivo → memória)
- Similaridade semântica entre tasks (apenas scope-link direto)
- Edição de tasks pelo studio (apenas visualização)