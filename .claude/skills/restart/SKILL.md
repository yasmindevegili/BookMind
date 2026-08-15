---
description: Reinicia o BookMind — para todos os containers e sobe novamente, aguardando o backend ficar pronto.
---

## Como reiniciar o BookMind

Sempre executar a partir de `/home/parallels/bookmind/`.
Usa `docker-compose` (v2 standalone, não `docker compose`).

### 1. Parar os containers

```bash
docker-compose down 2>&1 | grep -v "^time"
```

### 2. Subir novamente

```bash
docker-compose up -d 2>&1 | grep -v "^time"
```

### 3. Aguardar o backend

```bash
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
  [ "$code" = "200" ] && echo "Backend pronto (tentativa $i)" && break
  echo "Aguardando backend... ($i/20)"
  sleep 3
done
```

### 4. Smoke test

```bash
curl -s http://localhost:8000/api/books/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} livros na API')"
curl -s -o /dev/null -w "Frontend HTTP %{http_code}\n" http://localhost:3000
```

### URLs de acesso

- **Frontend:** http://localhost:3000
- **API / Swagger:** http://localhost:8000/docs

### Logs em caso de erro

```bash
docker-compose logs --tail=50 backend
docker-compose logs --tail=20 db
```
