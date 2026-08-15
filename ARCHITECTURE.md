# Architecture Decisions

## Por que pgvector em vez de um banco vetorial separado (Pinecone, Weaviate)?

Para uma biblioteca pessoal com dezenas ou centenas de anotações, a sobrecarga de operar um banco vetorial separado não vale a pena. O pgvector adiciona suporte a vetores diretamente no PostgreSQL, mantendo um único sistema de armazenamento com ACID transactions, backups simples e joins nativos entre vetores e metadados.

Trade-off: para milhões de vetores, Pinecone ou pgvector com índices ANN (HNSW/IVFFlat) seriam necessários. Nessa escala, pgvector ainda funciona com `CREATE INDEX ... USING hnsw`.

## Por que cada anotação é um chunk?

A estratégia de chunking mais comum para documentos longos é dividir o texto em pedaços de 512-1024 tokens com overlap. Aqui não precisamos: o usuário já faz o chunking manual ao salvar highlights e notas individualmente. Cada anotação é semanticamente coesa por natureza.

Benefício adicional: a fonte de cada chunk é trivialmente conhecida (é a anotação em si), então a citação é exata.

## Por que embeddings em background task?

Gerar um embedding via OpenAI leva ~200ms. Se fizéssemos isso no ciclo da requisição POST /annotations/, o usuário esperaria esse tempo antes de ver a confirmação. Com `BackgroundTasks` do FastAPI, a anotação é salva imediatamente e o embedding é gerado assincronamente.

Consequência: logo após salvar uma anotação, ela ainda não é buscável via chat. O campo `embedded_at` indica quando o embedding ficou pronto.

## Por que Claude para geração e OpenAI para embeddings?

A Anthropic não oferece API de embeddings própria (agosto de 2025). OpenAI `text-embedding-3-small` tem boa relação qualidade/custo e 1536 dimensões. Para geração, Claude é escolhido pela qualidade de síntese e raciocínio, especialmente em português.

Alternativa futura: Voyage AI (recomendado pela Anthropic para uso com Claude) para embeddings.

## RAG Pipeline — passo a passo

```
Pergunta do usuário
    │
    ▼
Embed a pergunta (OpenAI) → vetor de 1536 dimensões
    │
    ▼
cosine_distance(embedding, query_vector) no pgvector
    │
    ▼
Top-K anotações mais similares (default K=5)
    │
    ▼
Monta contexto: [Livro — Autor]\nConteúdo da anotação
    │
    ▼
Claude (claude-haiku-4-5) gera resposta em português com citações
    │
    ▼
Retorna: { answer, sources[] }
```
