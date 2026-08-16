# BookMind — Bem-vindo ao Projeto

BookMind é um sistema **RAG (Retrieval-Augmented Generation)** de biblioteca pessoal.
Você registra livros e anotações; o sistema indexa esses textos como vetores e permite
consultas em linguagem natural com respostas que citam a fonte original.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Banco | PostgreSQL + pgvector |
| Cache | Redis |
| Frontend | React + Vite + Tailwind CSS |
| LLM | Llama 3.3 70B via Groq (gratuito) |
| Embeddings | fastembed local — paraphrase-multilingual-MiniLM-L12-v2 (384 dims, sem API key) |

---

## Como subir o projeto

1. Copie `.env.example` para `.env` e preencha `GROQ_API_KEY`
2. Suba os containers:
   ```bash
   docker compose up -d
   ```
3. Ou use o skill dedicado — basta digitar no chat:
   ```
   /run
   ```

---

## Skills disponíveis

Digite `/nome` no chat para invocar qualquer skill.

| Skill | O que faz |
|---|---|
| `/run` | Sobe o projeto via Docker Compose, verifica seed e embeddings, confirma acesso ao frontend e à API |
| `/restart` | Para todos os containers e sobe novamente, aguardando o backend ficar pronto |
| `/dev` | Modo desenvolvimento — implementação de código (backend FastAPI, frontend React, testes) |
| `/git` | Modo versionamento — commits, branches, histórico, PRs |
| `/pm` | Modo produto — alinhamento de tarefas, requisitos e roadmap |
| `/professor` | Tire dúvidas sobre IA, LLMs, embeddings e RAG com explicações contextualizadas no BookMind |
| `/task-start` | Inicia a próxima task do roadmap — cria a branch correta e entra em modo dev |
| `/task-status` | Mostra a última task concluída e a próxima a ser feita |
| `/index` | Indexa arquivos no RAG do codebase — detecta novos e modificados pelo hash do conteúdo |
| `/md` | Visualiza arquivos `.md` com formatação e cores no terminal |

---

## Hooks configurados

Os hooks rodam automaticamente — você não precisa fazer nada para ativá-los.

### `PreToolUse › Bash`

| Gatilho | Comportamento |
|---|---|
| `git push` (qualquer variante) | **Bloqueado.** O comando nunca é executado — o Claude fornece o comando para você rodar manualmente. Isso evita pushes acidentais. |
| `git commit` | **Roda os testes antes de commitar.** Executa `pytest tests/ -v` dentro do container. Se algum teste falhar, o commit é bloqueado e o erro é mostrado. |

### `Stop`

Ao final de cada conversa, um agente indexa automaticamente qualquer arquivo novo ou modificado
no RAG do codebase (via MCP `bookmind-codebase`). Isso mantém o índice sempre atualizado sem
você precisar rodar `/index` manualmente.

---

## Permissões automáticas

Os comandos abaixo rodam sem pedir confirmação (configurado em `.claude/settings.json`):

`grep`, `find`, `ls`, `cat`, `head`, `tail`, `git log`, `git status`, `git diff`, `git show`,
`docker ps`, `docker logs`, `docker *`, `curl`

---

## Pipeline RAG

```
Pergunta do usuário
    → embed (fastembed local) → vetor 384 dims
    → cosine_distance no pgvector → Top-K=5 anotações mais similares
    → monta contexto: [Livro — Autor] + Conteúdo
    → Llama 3.3 70B via Groq gera resposta em português com citações
    → retorna { answer, sources[] }
```

---

## Acessos

- **Frontend:** http://localhost:3000
- **API (Swagger):** http://localhost:8000/docs
