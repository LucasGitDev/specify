# Redesign visual do specify studio

## Contexto

O studio usa o tema GitHub dark sem modificações, tornando-o visualmente genérico. A toolbar mistura controles de ação com filtros de tipo sem hierarquia. A sidebar não tem identidade do produto. O canvas é um fundo sólido sem textura.

## Critérios de Sucesso

- Paleta própria: o fundo do canvas usa um azul-escuro petróleo (#0b0f1a), não o cinza do GitHub; a sidebar usa um tom ligeiramente mais claro (#0f1520); a cor de acento primária é âmbar (#e8a045), não azul
- Canvas tem dot-grid sutil (SVG background-image) que marca o espaço sem competir com os nós
- Sidebar tem wordmark "specify / studio" no topo com o type stripe (barra horizontal de 4px dividida nas 4 cores dos tipos)
- Toolbar separada em dois grupos visuais com gap entre eles: grupo Ação (Reload, Stats, Reset layout, Panel) e grupo Filtro (decision, pattern, constraint, task)
- Filter buttons exibem um dot colorido da cor do tipo ao lado do label, eliminando a legenda flutuante redundante que é removida
- Tipografia: JetBrains Mono (Google Fonts) para todos os valores de dado (slug, scope, source, timestamps, content, gate results, stats); Inter para labels de campo, botões e títulos de seção
- Stats counter (X nodes · Y edges) exibido dentro da sidebar como linha de rodapé, não flutuando sobre o grafo
- Todos os textos de interface em inglês (remover strings em português da UI: "Memórias salvas" → "Memories saved", "Buscas totais" → "Total searches", etc.)
- A aparência geral é de um instrumento técnico (terminal + diagrama de engenharia), não de um dashboard web genérico

## Restrições

- Apenas mudanças em `src/studio/static/index.html` (CSS + HTML estrutural mínimo)
- Nenhuma mudança em comportamento JavaScript, lógica de API, ou lógica de grafo
- Fontes carregadas via Google Fonts CDN (sem build step)
- Manter todas as classes e IDs existentes que o JS referencia — ajustar apenas estilos e estrutura de marcação onde necessário

## Fora de escopo

- Responsividade mobile
- Animações de entrada ou transições de nó
- Mudanças no layout geral (grafo à esquerda, sidebar à direita)
- Novos campos ou funcionalidades na sidebar