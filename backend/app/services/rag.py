from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..models.annotation import Annotation
from ..models.book import Book
from .embeddings import embedding_service

settings = get_settings()


class RAGService:
    """
    O Pipeline RAG — 5 passos:
      1. Embed a pergunta do usuário (fastembed local, sem custo)
      2. Busca anotações mais próximas (cosine distance no pgvector)
      3. Monta contexto com as anotações + metadados do livro
      4. Envia contexto + pergunta para o Llama 3 via Groq (gratuito)
      5. Retorna resposta + quais fontes foram usadas
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GENERATION_MODEL
        self.top_k = settings.RAG_TOP_K

    async def search(self, query: str, db: AsyncSession) -> list[Annotation]:
        query_embedding = await embedding_service.embed(query)
        result = await db.execute(
            select(Annotation)
            .where(Annotation.embedding.is_not(None))
            .order_by(Annotation.embedding.cosine_distance(query_embedding))
            .limit(self.top_k)
        )
        return result.scalars().all()

    async def chat(self, query: str, db: AsyncSession) -> dict:
        annotations = await self.search(query, db)

        if not annotations:
            return {
                "answer": "Ainda não encontrei anotações indexadas na sua biblioteca. Adicione alguns livros e anotações, depois clique em '⚡ Gerar Embeddings' para que o chat funcione.",
                "sources": [],
            }

        book_ids = {a.book_id for a in annotations}
        books_result = await db.execute(select(Book).where(Book.id.in_(book_ids)))
        books = {b.id: b for b in books_result.scalars().all()}

        context = self._build_context(annotations, books)

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=400,
            messages=[
                {
                    "role": "system",
                    "content": """Você é uma leitora apaixonada que leu os mesmos livros e adora conversar sobre eles.

Seu jeito de falar:
- Tom natural e acolhedor, sem formalidade acadêmica, mas seguindo as normas do português — sem gírias, expressões coloquiais ou marcadores de oralidade como "né", "cara", "é isso"
- Nunca reproduza a anotação textualmente — interprete, conecte, dê sua leitura do que está ali
- Cite o livro de passagem, como em uma conversa ("o Cal Newport fala sobre isso...", "tem uma ideia interessante no Hábitos Atômicos...")
- 2 a 3 frases no máximo. Se surgir uma pergunta genuína que aprofunde o assunto, inclua — mas só se soar natural
- Sem listas, sem bullet points, sem subtítulos. Só texto corrido.""",
                },
                {
                    "role": "user",
                    "content": f"Anotações da minha biblioteca:\n\n{context}\n\n---\n\n{query}",
                },
            ],
        )

        sources = [
            {
                "book": books[a.book_id].title,
                "author": books[a.book_id].author,
                "type": a.type,
                "content": a.content[:150] + "..." if len(a.content) > 150 else a.content,
                "chapter": a.chapter,
            }
            for a in annotations[:2]
            if a.book_id in books
        ]

        return {"answer": response.choices[0].message.content, "sources": sources}

    def _build_context(self, annotations: list[Annotation], books: dict) -> str:
        parts = []
        for ann in annotations:
            book = books.get(ann.book_id)
            if not book:
                continue
            header = f"[{book.title} — {book.author}]"
            if ann.chapter:
                header += f" ({ann.chapter})"
            parts.append(f"{header}\n{ann.content}")
        return "\n\n---\n\n".join(parts)


rag_service = RAGService()
