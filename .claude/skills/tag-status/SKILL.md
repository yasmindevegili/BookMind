---
description: Mostra o progresso do tagging — quantos livros foram tagueados, quantos faltam e uma amostra das tags geradas.
---

## O que fazer ao ser invocado

Executar os comandos abaixo em sequência e exibir o resultado formatado.

### 1. Progresso geral

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -c "
SELECT
  COUNT(*)                                                        AS total,
  COUNT(*) FILTER (WHERE cardinality(tags) > 0)                  AS com_tags,
  COUNT(*) FILTER (WHERE cardinality(tags) = 0 OR tags IS NULL)  AS sem_tags,
  ROUND(COUNT(*) FILTER (WHERE cardinality(tags) > 0) * 100.0 / COUNT(*), 1) AS pct_concluido,
  COUNT(*) FILTER (WHERE title_en IS NOT NULL)                   AS com_title_en
FROM books;"
```

### 2. Amostra de livros recém-tagueados (últimos 5)

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -c "
SELECT title, title_en, array_to_string(tags, ', ') AS tags
FROM books
WHERE cardinality(tags) > 0
ORDER BY id DESC
LIMIT 5;"
```

### 3. Coleções de curadoria criadas até agora

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -c "
SELECT name, (SELECT COUNT(*) FROM collection_books cb WHERE cb.collection_id = c.id) AS livros
FROM collections c
ORDER BY livros DESC
LIMIT 10;"
```

### 4. Exibir resultado

Mostre as três consultas formatadas assim:

```
## Status do tagging

**Progresso:** X/5587 livros tagueados (X%) — Y com title_en

**Últimos tagueados:**
- "Título" → title_en: "..." | tags: ...
- ...

**Coleções criadas:** N
- Nome da coleção (X livros)
- ...
```

Se `pct_concluido = 100`, adicionar: `✓ Tagging completo! Rode /normalize-tags para normalizar as tags.`

## Regras

- Não implementar nada — só leitura
- Responder sempre em português
- Executar direto, sem pedir confirmação
