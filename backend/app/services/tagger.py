import httpx
from groq import AsyncGroq

from ..core.config import get_settings

settings = get_settings()

_OL_SEARCH_URL = "https://openlibrary.org/search.json"

# Subjects do Open Library que são metadados, não gêneros literários
_OL_NOISE = {
    "fiction", "nonfiction", "non-fiction", "accessible book", "protected daisy",
    "in library", "large type books", "open library", "internet archive",
    "overdrive", "lending library", "english language", "juvenile fiction",
    "juvenile literature", "young adult fiction", "children", "drama",
    "biography", "autobiography", "history", "geography", "science",
    "technology", "social science", "language arts", "literature",
}


def _filter_subjects(subjects: list[str]) -> list[str]:
    result = []
    for s in subjects:
        low = s.lower().strip()
        if low in _OL_NOISE:
            continue
        if len(low) < 4 or len(low) > 60:
            continue
        # Exclui subjects com padrões de metadados
        if any(p in low for p in ["isbn", "lccn", "dewey", "oclc", "lcsh"]):
            continue
        result.append(s)
    return result


class TaggerService:
    """
    Gera tags literárias para livros.

    Estratégia:
      1. Open Library subjects — gratuito, sem API key, cobertura global
      2. LLM (Llama via Groq) como fallback — funciona para qualquer livro,
         incluindo brasileiros pouco conhecidos
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def tag(self, title: str, author: str, description: str | None = None, isbn: str | None = None) -> list[str]:
        tags = await self._from_openlibrary(title, author, isbn)
        if len(tags) >= 3:
            return tags[:8]
        return await self._from_llm(title, author, description)

    async def _from_openlibrary(self, title: str, author: str, isbn: str | None) -> list[str]:
        queries = []
        if isbn:
            queries.append({"isbn": isbn, "fields": "subject", "limit": 1})
        queries.append({"title": title, "author": author, "fields": "subject", "limit": 1})

        async with httpx.AsyncClient(timeout=10) as client:
            for params in queries:
                try:
                    resp = await client.get(_OL_SEARCH_URL, params=params)
                    resp.raise_for_status()
                    docs = resp.json().get("docs", [])
                    if not docs:
                        continue
                    subjects = docs[0].get("subject", [])
                    filtered = _filter_subjects(subjects)
                    if filtered:
                        return filtered
                except Exception:
                    continue
        return []

    async def _from_llm(self, title: str, author: str, description: str | None) -> list[str]:
        desc_ctx = f"\nSinopse: {description[:300]}" if description else ""
        prompt = (
            f'Livro: "{title}" de {author}.{desc_ctx}\n\n'
            "Liste de 6 a 8 tags literárias compactas em português (minúsculas, sem acentos obrigatórios) "
            "que descrevam: subgênero, temas principais, época/cenário, estilo narrativo e tom emocional. "
            "Responda APENAS com as tags separadas por vírgula, sem explicações nem numeração."
        )
        try:
            resp = await self.client.chat.completions.create(
                model=settings.GENERATION_MODEL,
                max_tokens=80,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.choices[0].message.content.strip()
            tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
            return [t for t in tags if 3 <= len(t) <= 50][:8]
        except Exception:
            return []


tagger_service = TaggerService()
