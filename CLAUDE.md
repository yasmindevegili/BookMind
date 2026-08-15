# BookMind — Contexto do Projeto

Este arquivo é lido automaticamente pelo Claude Code no início de cada sessão.
Aqui está tudo que você precisa saber para trabalhar neste projeto sem explicações repetidas.

## O que é este projeto

BookMind é um sistema RAG (Retrieval-Augmented Generation) de biblioteca pessoal.
O usuário registra livros e anotações; o sistema indexa esses textos como vetores e
permite consultas em linguagem natural com respostas que citam a fonte original.

Stack: FastAPI (Python 3.11) + PostgreSQL + pgvector + Redis + React + Vite + Tailwind CSS.
IA: Llama 3.3 70B via Groq (gratuito) para geração, fastembed local para embeddings (384 dims, sem API key).
Modelo de embeddings: paraphrase-multilingual-MiniLM-L12-v2 (suporte a português, roda no container).

## Localização

Projeto em: `/home/parallels/bookmind/`

```
backend/
  app/
    api/         # rotas FastAPI (books, annotations, chat, profile)
    core/        # config.py, database.py
    models/      # Book, Annotation (com campo Vector(384))
    schemas/     # Pydantic (BookCreate/Response, AnnotationCreate/Response, ChatRequest/Response)
    services/    # embeddings.py (fastembed local), rag.py (pipeline completo)
  seed.py        # popula o banco com 8 livros reais + ~40 anotações
  tests/
frontend/
  src/
    pages/       # Library.jsx, Chat.jsx, BookDetail.jsx
    components/  # BookCard, ChatMessage, AddBookModal
    services/    # api.js (fetch wrapper)
docker-compose.yml
.env.example
ARCHITECTURE.md
```

## Pipeline RAG — como funciona

```
Pergunta do usuário
    → embed (fastembed local) → vetor 384 dims
    → cosine_distance no pgvector → Top-K=5 anotações mais similares
    → monta contexto: [Livro — Autor]\nConteúdo
    → Claude gera resposta em português com citações
    → retorna { answer, sources[] }
```

Embeddings são gerados em background task (FastAPI BackgroundTasks) quando uma
anotação é salva. O campo `embedded_at` indica se já foi indexada.

## Comandos principais

```bash
# Subir tudo
docker compose up -d

# Popular banco com livros reais
docker compose exec backend python seed.py

# Indexar anotações para o chat funcionar (embeddings locais, sem API key extra)
curl -X POST http://localhost:8000/api/annotations/embed-all

# Logs do backend
docker logs bookmind-backend-1 -f

# Acessar
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

## Regras do projeto

- **Idioma de todas as anotações, notas, citações e reflexões: PORTUGUÊS.**
  Citações originalmente em inglês devem ser traduzidas para o português.
  O seed.py e qualquer novo conteúdo deve ter 100% do texto em português.

- **Livros para o seed/exemplos:** preferir livros amplamente lidos no Brasil —
  best-sellers internacionais traduzidos para o português, autores brasileiros,
  ou livros de desenvolvimento pessoal/psicologia/filosofia populares no mercado editorial brasileiro.

- **Nunca** pedir permissão para comandos de leitura (grep, find, ls, cat, git log, git status, git diff, docker ps, docker logs). Já configurado em settings.json.

- **Nunca** executar `git push` nem qualquer variante (push --force, push --tags, etc.). Sempre fornecer o comando para a Yasmin rodar manualmente.

- **Respostas sempre em português** quando trabalhando neste projeto.

- **Não criar arquivos de documentação extras** (.md) além dos que já existem,
  a menos que explicitamente pedido.

## Status atual

- Scaffold completo criado (agosto 2025)
- Seed com 8 livros reais: Deep Work, Atomic Habits, Quiet, The 5 Love Languages,
  Thinking Fast and Slow, Man's Search for Meaning, Daring Greatly, Mindset
- Todas as anotações já estão em português (fase 1 de limpeza concluída em agosto 2026)
- Para rodar: precisa apenas de GROQ_API_KEY no .env (embeddings são locais via fastembed)

## Papel de professor

Este projeto é também um ambiente de aprendizagem sobre como usar IA de forma eficiente.
Quando surgir uma boa oportunidade — ao perceber que um hook, skill, configuração do Claude Code,
ou qualquer recurso da ferramenta poderia ajudar no fluxo de trabalho — **proponha e explique**:

- O que é o recurso
- Por que seria útil neste momento específico
- Como configurar ou usar
- O que acontece por baixo dos panos

Não espere ser perguntado. Se identificar uma oportunidade de ensino relevante, traga à tona.

## Postura do Claude neste projeto

Este projeto é um veículo de **aprendizagem real** — não apenas um portfólio ou demo.
O objetivo da Yasmin é entender como sistemas de IA são construídos e melhorar como desenvolvedora.

**Regras de postura:**

- **Honestidade sempre.** Se uma implementação está simplificada demais para produção, diz isso.
  Se uma abordagem tem limitações sérias, aponta — mesmo que funcione para o escopo atual.

- **Comparar com o mercado real.** Quando relevante, explicar como sistemas robustos resolvem
  o mesmo problema (ex: "em produção, embeddings costumam ser gerados de forma assíncrona com
  retry e fila dedicada, não com BackgroundTasks do FastAPI"). Isso é mais valioso do que validar
  o que já existe.

- **Sem elogios vazios.** Não dizer "ótima abordagem!" se não for verdade. Feedback direto
  e construtivo é mais respeitoso com o processo de aprendizagem.

- **Explicar o porquê das escolhas de IA/ML.** Sempre que implementar algo relacionado a
  embeddings, RAG, modelos ou infraestrutura de IA, explicar a decisão técnica:
  por que esse modelo? por que esse threshold? o que muda se escalar?

- **Apontar dívidas técnicas explicitamente.** Se algo foi feito de forma simplificada por ser
  um projeto de aprendizagem, marcar claramente como "simplificação intencional" e indicar
  o que seria diferente num sistema de produção.

## Roadmap e tasks

As tasks do projeto estão definidas em `/home/parallels/bookmind/inspo/INSPIRACOES.md`.
Quando a Yasmin mencionar "tasks", "T01", "próxima task" ou qualquer referência a features planejadas,
ler esse arquivo primeiro para entender o contexto e a ordem de execução.

O arquivo contém: fases de desenvolvimento (1–6), dependências entre tasks, referências visuais
e decisões de arquitetura em aberto.

## Próximas features planejadas (não implementadas)

- Exportação de resenha (Goodreads, Instagram, blog)
- Recomendações baseadas no histórico
- Perfil de leitora com análise de padrões
- CI/CD com GitHub Actions
- Autenticação de usuário
