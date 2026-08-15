# Inspirações — BookMind

Arquivo para coletar referências de UI, UX e features para o BookMind.

---

## Roadmap — Sequência de execução

As tasks estão ordenadas por dependência: cada fase desbloqueia a próxima.
Legenda: `[ ]` = pendente · `[x]` = concluído · `[~]` = decisão em aberto

---

### Fase 1 — Base (sem isso, nada avança)

- [ ] **T01** — Adicionar campo `status` no modelo `Book` no banco: `lido | quero_ler | abandonei | nenhum`
  - _Por que primeiro:_ perfil, main page, sugestões e mapa cartesiano dependem desse campo
- [ ] **T02** — Embedding automático ao criar livro/anotação (remover botão manual do frontend)
  - _Por que segundo:_ todas as features de IA (sugestões, coleções, busca) precisam de embeddings confiáveis e automáticos

---

### Fase 2 — Quick wins visuais

- [ ] **T03** — Capas obrigatórias: fallback gerado (cor + título + autor) quando `cover_url` está vazio
  - _Depende de:_ nada · _Impacto:_ imediato em toda a biblioteca
- [ ] **T04** — Botão de favoritar no `BookCard` com toggle e persistência
  - _Depende de:_ T01 (usa o campo `status`)
- [ ] **T05** — Main page exibe apenas livros sem status (fila de descoberta); "Todos" vai para sidebar
  - _Depende de:_ T01
- [ ] **T06** — Modos de visualização na `Library`: grid masonry + ordenação (data, avaliação, tema)
  - _Depende de:_ nada · _Referência:_ Google Arts & Culture
- [ ] **T07** — Animação de abertura de livro ao hover no `BookCard`
  - _Depende de:_ nada · _Prioridade:_ baixa (estético)

---

### Fase 3 — Features de descoberta (core do produto)

- [ ] **T08** — `BookDetail` com metadados ricos (ISBN, páginas, formato) + botões de ação
  - _Depende de:_ nada · _Referência:_ Z-Library
- [ ] **T09** — Livros sugeridos na `BookDetail` abaixo das anotações (similaridade vetorial)
  - _Depende de:_ T02 (embeddings automáticos)
- [ ] **T10** — Sugestão por vibe/sensação: usuário seleciona livros, sistema sugere similares
  - _Depende de:_ T01 (para filtrar "não lidos") + T02
  - _Decisão em aberto:_ entrada por seleção manual, favoritos ou últimos N lidos?

---

### Fase 4 — Perfil e gamificação

- [ ] **T11** — Página de perfil (`Profile.jsx`): listas por status + meta anual + barra de progresso
  - _Depende de:_ T01
- [ ] **T12** — Reorganizar navegação: Coleções ficam no perfil, Curadoria na home
  - _Depende de:_ T11

---

### Fase 5 — Coleções e Curadoria

- [ ] **T13** — Seção **Curadoria** na home: listas editoriais fixas (Booker Prize, mais vendidos, etc.)
  - _Depende de:_ T12
- [ ] **T14** — **Coleções geradas por IA**: usuário digita tema → LLM sugere livros → coleção editável
  - _Depende de:_ T02 + T13 (estrutura de navegação separada)
  - _Decisão em aberto:_ livros sugeridos fora do acervo → filtrar ou buscar via Google Books API?

---

### Fase 6 — Features sociais e mapas (requer autenticação)

- [ ] **T15** — Autenticação de usuário (base para tudo nessa fase)
- [ ] **T16** — Mapa-múndi de livros por país com zoom progressivo (Leaflet.js + campo `country` no banco)
  - _Depende de:_ T15 não obrigatório, mas enriquecer modelo `Book` com `country`
- [ ] **T17** — Mapa cartesiano de usuários por gosto literário (PCA/UMAP + D3.js, eixos configuráveis)
  - _Depende de:_ T15 + múltiplos usuários com livros marcados

---

## Referências salvas

### Z-Library — detalhe de livro
- **Arquivo:** `069e835757...600.webp`
- **Ideia:** página de detalhe com metadados completos (ISBN, páginas, formato) + botões de ação + seção "Você também pode gostar"
- **Aplicar em:** `BookDetail.jsx` — metadados mais ricos + recomendações por similaridade vetorial

### Google Arts & Culture — galeria com modos de organização
- **Arquivo:** `Screenshot 2026-08-14 at 11.35.14.png`
- **Ideia:** grid masonry com filtros de ordenação (popularidade / cronologia / cor)
- **Aplicar em:** `Library.jsx` — modos de visualização alternativos + ordenação por data de leitura, tema, avaliação

### Apple Books — biblioteca pessoal
- **Arquivo:** `Screenshot 2026-08-14 at 11.44.32.png`
- **Ideia:** sidebar com status de leitura (Want to Read / Finished) + coleções manuais + grid limpo de capas
- **Aplicar em:** sidebar de navegação + campo de status por livro + coleções personalizadas

---

## Novas inspirações

### Animação de abertura de livro ao hover
- **Ideia:** ao passar o mouse sobre o card de um livro, animar como se as páginas estivessem abrindo
- **Aplicar em:** `BookCard.jsx` — animação CSS/Framer Motion no hover do card

### Coleções dinâmicas
- **Ideia:** coleções que se atualizam automaticamente com base em critérios externos, ex: "Mais vendidos dessa semana da Rocco", "Lançamentos do mês"
- **Aplicar em:** seção de coleções na `Library.jsx` — integração com API de editoras ou curadoria manual com atualização periódica

### Capas obrigatórias para todos os livros
- **Ideia:** nenhum livro pode aparecer sem capa — usar fallback gerado (ex: cor + título + autor) caso a imagem não esteja disponível
- **Aplicar em:** `BookCard.jsx` + `BookDetail.jsx` — placeholder visual gerado quando `cover_url` está vazio

### Botão de favoritar no card (sem entrar na página)
- **Ideia:** ícone de favoritar/salvar para ler mais tarde diretamente no card, sem precisar acessar a página do livro
- **Aplicar em:** `BookCard.jsx` — ícone de marcador no canto superior do card, com toggle e persistência

### Livros sugeridos na página do livro
- **Ideia:** abaixo da seção de anotações, exibir livros sugeridos com base no livro atual, usando o mesmo layout de grid de cards
- **Aplicar em:** `BookDetail.jsx` — seção "Você também pode gostar" usando similaridade vetorial (já existe no pipeline RAG)

### Main page mostra apenas livros não marcados
- **Ideia:** a página principal não exibe "Todos os livros", mas sim somente os que ainda não foram marcados com nenhuma tag (não lidos, não favoritados, sem status) — funciona como uma fila de descoberta
- **Aplicar em:** `Library.jsx` — filtro padrão por livros sem tag/status; o "Todos" vira uma view separada acessível pela sidebar

### Geração de embedding gerenciada pelo backend
- **Ideia:** remover o botão de "gerar embedding" do frontend — quando o usuário adiciona um livro ou anotação, o backend decide o momento de gerar o embedding automaticamente (ex: logo após salvar, via fila ou background task)
- **Aplicar em:** `backend/app/api/` — trigger automático no `POST /books` e `POST /annotations`; remover endpoint/botão manual do frontend
- **Nota técnica:** hoje já usa `BackgroundTasks` do FastAPI, mas o gatilho ainda é manual via curl — basta mover para o fluxo de criação

### Mapa cartesiano de usuários por gosto literário
- **Ideia:** plano cartesiano com 4 quadrantes onde cada usuário é posicionado de acordo com seus livros marcados; quanto mais parecidos os gostos, mais próximos no mapa. Os eixos podem ser configuráveis (ex: X = ficção ↔ não-ficção, Y = clássico ↔ contemporâneo)
- **Aplicar em:** nova página `Map.jsx` — embeddings dos livros de cada usuário agregados em um vetor médio de perfil; redução de dimensionalidade (PCA ou UMAP) para projetar em 2D; renderização com D3.js ou Recharts
- **Nota técnica:** requer múltiplos usuários (autenticação) e cálculo de vetor de perfil por usuário — feature de médio/longo prazo

### Mapa-múndi de descoberta de livros por país
- **Ideia:** mapa interativo estilo Google Maps — conforme o usuário dá zoom em uma região/país, vão aparecendo livros daquele lugar (por origem do autor ou do contexto da obra); zoom raso mostra continentes, zoom profundo mostra cidades e autores locais
- **Aplicar em:** nova página `WorldMap.jsx` — biblioteca de mapa (Leaflet.js ou Mapbox), livros com campo `country` no banco, clustering por zoom level igual ao comportamento de markers do Google Maps
- **Nota técnica:** exige enriquecer o modelo `Book` com `country`/`region` e adicionar lógica de clustering no frontend — feature ambiciosa, mas muito diferenciadora visualmente

### Página de perfil do usuário com metas e gamificação
- **Ideia:** cada usuário tem uma página de perfil com: listas de livros por status (lidos / quero ler / abandonei) + metas de leitura (ex: "20 livros em 2026") + progresso visual do ano — gamifica a experiência de leitura
- **Aplicar em:** nova página `Profile.jsx` + campo `status` no modelo `Book` (lido/quero ler/abandonei) + modelo `ReadingGoal` no banco com meta anual e contagem
- **Nota técnica:** depende de autenticação para que cada usuário tenha seu próprio perfil; sem auth, pode começar como perfil único local. Barra de progresso anual é simples: `livros_lidos_no_ano / meta * 100`

### Sugestão de livros por sensação/vibe de leitura
- **Ideia:** o usuário seleciona um conjunto de livros (ou usa os favoritos) e o sistema sugere novos títulos que remetam à mesma sensação — ex: "li Harry Potter e Crônicas de Nárnia → sugestão: O Hobbit, Senhor dos Anéis"
- **Aplicar em:** nova rota `POST /api/suggestions` + nova página ou modal `Suggestions.jsx` — o usuário monta uma seleção de livros; o backend calcula o vetor médio desses livros e busca os mais próximos no espaço vetorial que ainda não foram lidos pelo usuário
- **Nota técnica:** essa é uma das aplicações mais naturais do pipeline RAG que já existe — em vez de buscar anotações similares a uma pergunta, busca livros similares a um conjunto de livros. Tecnicamente direto; o diferencial é a UX de seleção. A entrada pode ser: (a) seleção manual de qualquer livro, (b) somente favoritos, ou (c) os últimos N lidos — vale testar as três.

### Coleções geradas por IA com assistente de linguagem natural
- **Ideia:** ao criar uma coleção, o usuário digita livremente o tema desejado (ex: "histórias sobre o Japão na Segunda Guerra") e a IA gera a coleção com livros sugeridos; depois o usuário pode editar (adicionar/remover títulos) ou excluir a coleção inteira
- **Aplicar em:** `Collections.jsx` + nova rota `POST /api/collections/generate` — o backend recebe o texto do tema, usa o LLM (Groq/Llama) para sugerir títulos e cruza com o acervo disponível via similaridade vetorial; resultado vira uma coleção persistida no banco editável pelo usuário
- **Separação de seções (decisão de arquitetura de UX):**
  - **Coleções** → seção pessoal, criadas por intenção do usuário via IA ou manualmente; dinâmicas e editáveis
  - **Curadoria** (novo nome para o que era "coleções de premiados") → seção editorial separada com listas fixas ou atualizadas periodicamente: "Vencedores do Booker Prize", "Mais vendidos da Rocco essa semana", etc. — sem edição pelo usuário
- **Por que separar:** as duas têm naturezas opostas — Coleções são expressão do gosto pessoal, Curadoria é referência externa. Misturar dilui as duas. UX mais limpa e semântica mais clara.
- **Nota técnica:** a geração via LLM pode sugerir livros que não estão no banco — precisa de uma etapa de reconciliação. **Decisão em aberto:** filtrar apenas o que existe no acervo, ou oferecer botão "adicionar ao acervo" com busca de metadados externos (ex: Google Books API)? A segunda opção é mais poderosa mas adiciona dependência externa. A decidir.

### Curadoria — seção editorial separada de Coleções
- **Ideia:** renomear e mover as "coleções de premiados/mais vendidos" para uma seção chamada **Curadoria**, distinta das Coleções pessoais; aparece na home como descoberta ("o que está em alta") e não é editável pelo usuário
- **Por que separar:** Coleções são expressão pessoal (editáveis, subjetivas); Curadoria é referência externa (fixa, objetiva). Misturar gera confusão sobre o que pode ser editado
- **Aplicar em:** seção dedicada na `Library.jsx` ou componente `Curadoria.jsx` na home — listas atualizadas periodicamente (Booker Prize, Mais Vendidos da Rocco, etc.)

### Coleções ficam no perfil, Curadoria na home
- **Ideia:** posicionamento das duas seções na navegação — Coleções como extensão da biblioteca pessoal (dentro do perfil ou sidebar do usuário); Curadoria como vitrine de descoberta na home
- **Aplicar em:** estrutura de navegação geral — reorganizar sidebar/rotas para refletir essa separação semântica

