# BookMind

Biblioteca pessoal com RAG — registre livros e anotações, converse com seu acervo em linguagem natural.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

![Claude Code](https://img.shields.io/badge/Claude_Code-Onboarding-D97706?style=flat-square&logo=anthropic&logoColor=white)

---

## O que é

BookMind é um sistema **RAG (Retrieval-Augmented Generation)** de biblioteca pessoal. Você registra livros e anotações — highlights, reflexões, citações — e o sistema indexa esses textos como vetores. Depois, você faz perguntas em português e recebe respostas fundamentadas no seu próprio acervo, com citação da fonte exata.

Diferente de um LLM genérico, o BookMind responde **com base no que você leu**, não no que o modelo sabe.

---

## Como funciona

```
Sua pergunta
    │
    ▼
fastembed (local) → vetor de 384 dimensões
    │
    ▼
cosine_distance no pgvector → Top-5 anotações mais similares
    │
    ▼
Contexto: [Livro — Autor] + conteúdo da anotação
    │
    ▼
Llama 3.3 70B via Groq → resposta em português com citações
    │
    ▼
{ answer, sources[] }
```

**Embeddings são locais** — rodam no container via `fastembed`, sem API key extra, com suporte nativo a português (`paraphrase-multilingual-MiniLM-L12-v2`). A única chave necessária é a do Groq para geração de texto, que tem plano gratuito.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + Python 3.11 + SQLAlchemy async |
| Banco | PostgreSQL 16 + pgvector (busca vetorial) |
| Cache | Redis 7 |
| Embeddings | fastembed (local, 384 dims, suporte a PT) |
| Geração | Groq — Llama 3.3 70B (gratuito) |
| Frontend | React + Vite + Tailwind CSS |
| Infra | Docker Compose |
| Migrações | Alembic |

---

## Rodando localmente

### Pré-requisitos

- Docker e Docker Compose
- Chave gratuita do [Groq](https://console.groq.com)

### Setup

```bash
# 1. Clone o repositório
git clone https://github.com/yasmindevegili/bookmind.git
cd bookmind

# 2. Configure o ambiente
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY

# 3. Suba os containers (backend, frontend, postgres, redis)
docker compose up -d

# 4. Popule o banco com 8 livros e ~40 anotações em português
docker compose exec backend python seed.py

# 5. Gere os embeddings (roda localmente, sem API key extra)
curl -X POST http://localhost:8000/api/annotations/embed-all
```

### Acesso

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API / Swagger | http://localhost:8000/docs |

---

## Funcionalidades

- **Biblioteca** — cadastro de livros com capa, autor, status de leitura e gênero
- **Anotações** — highlights, citações e reflexões vinculadas a cada livro
- **Chat RAG** — perguntas em linguagem natural com respostas citadas do seu acervo
- **Seed** — 8 livros reais populares no Brasil com anotações prontas para explorar

---

## Estrutura do projeto

```
bookmind/
├── backend/
│   ├── app/
│   │   ├── api/          # rotas (books, annotations, chat, profile)
│   │   ├── core/         # config, database
│   │   ├── models/       # SQLAlchemy (Book, Annotation + Vector)
│   │   ├── schemas/      # Pydantic
│   │   └── services/     # embeddings.py, rag.py
│   ├── alembic/          # migrações de banco
│   ├── seed.py           # dados iniciais
│   └── tests/
├── frontend/
│   └── src/
│       ├── pages/        # Library, Chat, BookDetail
│       ├── components/   # BookCard, ChatMessage, AddBookModal
│       └── services/     # api.js
└── docker-compose.yml
```

---

## Decisões de arquitetura

Ver [`ARCHITECTURE.md`](./ARCHITECTURE.md) para as decisões técnicas documentadas: por que pgvector em vez de um banco vetorial dedicado, por que embeddings locais, estratégia de chunking e o pipeline RAG completo.

---

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave da API Groq (obrigatória) |
| `DATABASE_URL` | Gerada automaticamente pelo Docker Compose |
| `REDIS_URL` | Gerada automaticamente pelo Docker Compose |

---

*Projeto de aprendizagem sobre sistemas RAG e aplicações de IA generativa.*
