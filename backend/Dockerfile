FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pré-baixa o modelo de embeddings (~90MB) durante o build
# Assim a primeira requisição não demora — o modelo já está no cache
RUN python -c "\
from fastembed import TextEmbedding; \
print('Baixando modelo de embeddings multilingual...'); \
TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); \
print('Modelo pronto!')"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
