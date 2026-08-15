import asyncio

from fastembed import TextEmbedding

from ..core.config import get_settings

settings = get_settings()


class EmbeddingService:
    """
    Converte texto em vetores numéricos usando um modelo local (sem API key).

    Por que fastembed?
      - Roda 100% local no container Docker — zero custo, zero dependência externa
      - Modelo multilingual: funciona bem com português
      - Usa ONNX (não precisa de PyTorch), imagem Docker mais leve

    Como funciona:
      "Introversão é uma força" → [0.12, -0.34, 0.09, ...] (384 números)
      "Introvertidos são poderosos" → [0.11, -0.31, 0.10, ...] (similar!)
      Quando você pergunta "o que li sobre introversão?", encontramos os dois.
    """

    def __init__(self):
        # Lazy init: o modelo (~90MB) é carregado na primeira chamada
        self._model: TextEmbedding | None = None

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(settings.EMBEDDING_MODEL)
        return self._model

    async def embed(self, text: str) -> list[float]:
        clean = text.replace("\n", " ").strip()
        loop = asyncio.get_event_loop()
        # fastembed é síncrono — executamos em thread pool para não bloquear o servidor
        result = await loop.run_in_executor(
            None,
            lambda: list(self.model.embed([clean]))[0]
        )
        return result.tolist()

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        clean = [t.replace("\n", " ").strip() for t in texts]
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: [emb.tolist() for emb in self.model.embed(clean)]
        )
        return results


embedding_service = EmbeddingService()
