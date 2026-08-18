---
description: Tagueia 100% dos livros do BookMind — re-tagueia inclusive os já tagueados, em lotes de 500, com progresso e coleções de curadoria.
---

## O que esta skill faz

Executa o tagging literário completo da biblioteca: todos os livros recebem tags
via Open Library Works API (subjects + subject_places + subject_times) e LLM
(Llama via Groq) como fallback. Livros já tagueados são re-tagueados com o tagger
atual (mais preciso). Prêmios e coleções editoriais detectados alimentam a tabela
`collections` automaticamente.

Ao final, normaliza todas as tags para português com acentuação correta.

---

## Passo 1 — Verificar estado inicial

```bash
docker exec bookmind-db-1 psql -U bookmind -d bookmind -c "
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE cardinality(tags) > 0) as com_tags,
  COUNT(*) FILTER (WHERE cardinality(tags) = 0 OR tags IS NULL) as sem_tags
FROM books;"
```

Anote o total. Com `force=true`, **todos** os livros serão re-tagueados — inclusive
os 247 que já têm tags, pois podem estar mal-tagueados.

---

## Passo 2 — Garantir que o backend está rodando

```bash
curl -s -o /dev/null -w "Backend: HTTP %{http_code}\n" http://localhost:8000/docs
```

Se não retornar 200, rodar `/restart` antes de continuar.

---

## Passo 3 — Loop automático de tagging

Este script dispara lotes de 500 e aguarda cada um concluir antes de disparar o
próximo. Roda até `sem_tags = 0` (100% tagueado) ou travar por 3 checagens sem
progresso (sinal de erro no backend).

```bash
python3 - <<'EOF'
import subprocess, time, json, urllib.request

TOTAL_URL = "http://localhost:8000/api/books/tag-all?limit=500&force=true"
DB_CMD = [
    "docker", "exec", "bookmind-db-1", "psql", "-U", "bookmind", "-d", "bookmind",
    "-t", "-c",
    "SELECT COUNT(*) FILTER (WHERE cardinality(tags) = 0 OR tags IS NULL) FROM books;"
]

def sem_tags():
    r = subprocess.run(DB_CMD, capture_output=True, text=True)
    return int(r.stdout.strip())

def fire_batch():
    req = urllib.request.Request(TOTAL_URL, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

lote = 0
while True:
    restantes = sem_tags()
    if restantes == 0:
        print("100% tagueado! Todos os livros têm tags.")
        break

    lote += 1
    resp = fire_batch()
    queued = resp.get("queued", 0)
    print(f"\n[Lote {lote}] {queued} livros enfileirados — {restantes} ainda sem tags")

    sem_progresso = 0
    anterior = restantes
    while True:
        time.sleep(60)
        atual = sem_tags()
        delta = anterior - atual
        print(f"  Progresso: {atual} sem tags (−{delta} no último minuto)")
        if delta > 0:
            sem_progresso = 0
            anterior = atual
        else:
            sem_progresso += 1
            if sem_progresso >= 3:
                print("  Lote concluído (sem progresso por 3 min).")
                break
        if atual == 0:
            break
EOF
```

### Ritmo esperado
- ~5–10 livros/min (Open Library rápido, LLM mais lento)
- Total estimado para 5.587 livros: 8–16 horas em ~12 lotes de 500
- O processo roda em background — não trava o sistema nem o terminal

---

## Passo 4 — Normalizar tags para português

Quando o script acima concluir com "100% tagueado!", rodar:

```bash
curl -s -X POST "http://localhost:8000/api/books/normalize-tags"
```

Este endpoint:
1. Coleta todas as tags distintas do banco
2. Envia em lotes de 60 ao LLM para traduzir para português
3. Atualiza todos os livros com as tags normalizadas
4. Regenera embeddings dos livros alterados em background

A resposta mostra quantos livros foram atualizados e uma amostra das traduções.

---

## Passo 5 — Verificar coleções criadas

```bash
curl -s http://localhost:8000/api/collections/ | python3 -c "
import sys, json
cols = json.load(sys.stdin)
print(f'{len(cols)} coleções criadas:')
for c in cols[:10]:
    print(f'  {c[\"name\"]}')
"
```

---

## Regras desta skill

- Sempre usar `force=true` para garantir que livros mal-tagueados sejam corrigidos
- O loop aguarda cada lote antes de disparar o próximo — não disparar manualmente em paralelo
- Não rodar `normalize-tags` antes de todos os livros terem tags
- Em caso de erro no backend, verificar logs: `docker logs bookmind-backend-1 --tail=30`
