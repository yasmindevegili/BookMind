# Architecture Decisions

## Por que pgvector em vez de um banco vetorial separado (Pinecone, Weaviate)?

Para uma biblioteca pessoal com dezenas ou centenas de anotações, a sobrecarga de operar um banco vetorial separado não vale a pena. O pgvector adiciona suporte a vetores diretamente no PostgreSQL, mantendo um único sistema de armazenamento com ACID transactions, backups simples e joins nativos entre vetores e metadados.

Trade-off: para milhões de vetores, Pinecone ou pgvector com índices ANN (HNSW/IVFFlat) seriam necessários. Nessa escala, pgvector ainda funciona com `CREATE INDEX ... USING hnsw`.

## Por que cada anotação é um chunk?

A estratégia de chunking mais comum para documentos longos é dividir o texto em pedaços de 512-1024 tokens com overlap. Aqui não precisamos: o usuário já faz o chunking manual ao salvar highlights e notas individualmente. Cada anotação é semanticamente coesa por natureza.

Benefício adicional: a fonte de cada chunk é trivialmente conhecida (é a anotação em si), então a citação é exata.

## Por que embeddings em background task?

Gerar um embedding leva alguns centenas de milissegundos. Se fizéssemos isso no ciclo da requisição `POST /annotations/`, o usuário esperaria esse tempo antes de ver a confirmação. Com `BackgroundTasks` do FastAPI, a anotação é salva imediatamente e o embedding é gerado assincronamente.

Consequência: logo após salvar uma anotação, ela ainda não é buscável via chat. O campo `embedded_at` indica quando o embedding ficou pronto.

Simplificação intencional: em produção, isso seria feito via fila dedicada (Celery + Redis, ou similar) com retry automático em caso de falha. O `BackgroundTasks` do FastAPI não tem mecanismo de retry — se o processo cair durante a geração, o embedding simplesmente não é criado.

## Por que fastembed local para embeddings?

O modelo usado é `paraphrase-multilingual-MiniLM-L12-v2` via `fastembed`, rodando 100% dentro do container Docker.

Vantagens:
- Zero custo, zero dependência de API key externa
- Suporte nativo a português (modelo multilingual treinado em 50+ idiomas)
- Usa ONNX runtime — mais leve que PyTorch, sem GPU necessária
- Modelo ~90MB, carregado em memória na primeira chamada (lazy init)

Dimensionalidade: **384 dims** (menor que modelos OpenAI, mas suficiente para o volume do BookMind).

Trade-off: modelos como `text-embedding-3-small` da OpenAI (1536 dims) ou Voyage AI têm qualidade de retrieval superior, especialmente para textos longos ou domínios especializados. Para uma biblioteca pessoal, 384 dims é adequado.

## Por que Groq + Llama 3.3 70B para geração?

O Groq oferece inferência gratuita de modelos open-source com latência muito baixa (tokens gerados em hardware dedicado). O `llama-3.3-70b-versatile` tem boa qualidade de síntese em português.

Vantagens:
- Sem custo para o projeto
- Latência baixa (~1-2s para respostas curtas)
- Qualidade suficiente para síntese de anotações em português

Trade-off: rate limits generosos mas existentes. Em produção, exigiria fallback ou modelo próprio. A Anthropic recomenda Voyage AI para embeddings quando usado com Claude, mas o BookMind optou por embeddings locais para eliminar dependências externas.

## RAG Pipeline — passo a passo

```
Pergunta do usuário
    │
    ▼
Embed a pergunta (fastembed local) → vetor de 384 dimensões
    │
    ▼
cosine_distance(embedding, query_vector) no pgvector
    │
    ▼
Top-K=5 anotações mais similares
    │
    ▼
Monta contexto: [Livro — Autor]\nConteúdo da anotação
    │
    ▼
Llama 3.3 70B via Groq gera resposta em português com citações (max 400 tokens)
    │
    ▼
Retorna: { answer, sources[] }
```

Nota sobre sources: o campo `sources` retorna as 2 primeiras anotações do Top-5 (não todas as 5). As demais 3 influenciam o contexto enviado ao modelo mas não aparecem na resposta ao usuário.
