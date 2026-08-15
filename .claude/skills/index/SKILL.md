---
description: Indexa arquivos do projeto no RAG do codebase — detecta novos e modificados pelo hash do conteúdo, sem re-indexar tudo.
---

## Como indexar o codebase do BookMind

Este skill atualiza o índice vetorial do `mcp_codebase` usado pelo Claude para
buscar código semanticamente. Indexa apenas o que mudou desde a última execução.

### 1. Verificar o estado atual do índice

Use a ferramenta MCP `search_codebase` para confirmar se o índice existe:

```
search_codebase("teste")
```

Se retornar `"Nenhum resultado encontrado"`, o índice está vazio — use o passo 2B.
Se retornar resultados, verifique se são recentes e passe para o passo 2A.

### 2A. Indexação incremental (arquivos novos ou modificados)

Use a ferramenta MCP `index_new_files`:

```
index_new_files()
```

Ela compara o hash MD5 de cada arquivo com o que está no Chroma.
Só re-indexa arquivos cujo conteúdo mudou ou que não existem no índice.

A saída informa:
- Quantos arquivos foram processados
- Quantos chunks foram adicionados
- Quais arquivos foram ignorados (sem mudança)

### 2B. Re-indexação completa (quando o índice está corrompido ou vazio)

Use a ferramenta MCP `index_codebase`:

```
index_codebase()
```

Apaga a coleção existente e reconstrói do zero. Mais lento, mas garante consistência.

### 3. Confirmar o resultado

Após indexar, faça uma busca de validação:

```
search_codebase("embeddings fastembed")
```

Deve retornar trechos de `backend/app/services/embeddings.py` com similaridade > 0.7.

### Arquivos cobertos

O indexador processa automaticamente:

| Extensão | Exemplos |
|---|---|
| `.py` | backend, serviços, modelos, testes, seeds |
| `.jsx` / `.js` | frontend React, Vite config |
| `.md` | CLAUDE.md, ARCHITECTURE.md, skills |
| `.yml` / `.yaml` | docker-compose.yml |

Exclui: `__pycache__`, `node_modules`, `.venv`, `.git`, `dist`, `build`, `alembic/versions`.

### Quando usar este skill

- Depois de criar ou editar arquivos `.py` ou `.jsx`
- Ao iniciar uma sessão e querer garantir que o índice está atualizado
- Quando o `search_codebase` retornar resultados desatualizados ou não encontrar algo que existe

### O que acontece por baixo

1. Lista todos os arquivos elegíveis com `rglob`
2. Para cada arquivo: calcula MD5 do conteúdo inteiro
3. Compara com o hash armazenado nos metadados do Chroma
4. Arquivos novos ou com hash diferente: deleta chunks antigos, re-chunka (60 linhas, 10 de overlap), gera embeddings via fastembed local
5. Salva no ChromaDB persistido em `mcp-codebase/.chroma/`

**Simplificação intencional:** chunking fixo por linhas, não por AST.
Em produção, chunks respeitariam limites de funções/classes para contexto mais preciso.
