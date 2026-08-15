---
description: Inicia o projeto BookMind via Docker Compose, verifica seed e embeddings, e confirma acesso ao frontend e à API.
---

## Como iniciar o BookMind

O projeto usa `docker-compose` (v2 standalone, não `docker compose`).
Sempre executar a partir de `/home/parallels/bookmind/`.

### 1. Verificar containers

```bash
docker-compose ps 2>&1 | grep -v "^time"
```

Se todos os 4 serviços (`db`, `redis`, `backend`, `frontend`) já estiverem `Up`, pule para o passo 4.

### 2. Subir os containers

```bash
docker-compose up -d 2>&1 | grep -v "^time"
```

### 3. Aguardar o backend

```bash
for i in $(seq 1 15); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
  [ "$code" = "200" ] && echo "Backend pronto (tentativa $i)" && break
  echo "Aguardando... ($i/15)"
  sleep 2
done
```

### 4. Checar seed

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -t -c "SELECT COUNT(*) FROM books;" 2>/dev/null | tr -d ' '
```

Se retornar `0` ou erro de tabela, rodar o seed:

```bash
docker exec bookmind-backend-1 python seed.py
```

### 5. Checar embeddings

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -t -c "SELECT COUNT(*) FROM annotations WHERE embedded_at IS NULL;" 2>/dev/null | tr -d ' '
```

Se retornar número > 0, indexar:

```bash
curl -s -X POST http://localhost:8000/api/annotations/embed-all
```

### 6. Smoke test

```bash
curl -s http://localhost:8000/api/books/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} livros na API')"
curl -s -o /dev/null -w "Frontend HTTP %{http_code}\n" http://localhost:3000
```

### URLs de acesso

- **Frontend:** http://localhost:3000
- **API / Swagger:** http://localhost:8000/docs

### Logs em caso de erro

```bash
docker-compose logs --tail=40 backend
```
