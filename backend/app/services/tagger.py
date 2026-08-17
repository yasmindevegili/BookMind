import httpx
from groq import AsyncGroq

from ..core.config import get_settings

settings = get_settings()

_OL_SEARCH_URL = "https://openlibrary.org/search.json"
_OL_WORKS_URL = "https://openlibrary.org"

# Subjects do Open Library que são metadados, não gêneros literários
_OL_NOISE = {
    "fiction", "nonfiction", "non-fiction", "accessible book", "protected daisy",
    "in library", "large type books", "open library", "internet archive",
    "overdrive", "lending library", "english language", "juvenile fiction",
    "juvenile literature", "young adult fiction", "children", "drama",
    "biography", "autobiography", "history", "geography", "science",
    "technology", "social science", "language arts", "literature",
}

# Padrões que indicam prêmios, coleções editoriais ou formatos — não gêneros
_OL_AWARD_PATTERNS = [
    "prêmio", "premio", "prize", "award", "winner", "finalist", "shortlist",
    "booker", "pulitzer", "nobel", "jabuti", "camões", "pen ", "hugo award",
    "nebula", "escritas por", "coleção", "colecao", "series", "classics",
    "penguin", "vintage", "everyman", "biblioteca",
]


def _is_genre_tag(s: str) -> bool:
    """Retorna True apenas se o subject parece um gênero/tema literário real."""
    low = s.lower().strip()
    if low in _OL_NOISE:
        return False
    if len(low) < 4 or len(low) > 60:
        return False
    if any(p in low for p in ["isbn", "lccn", "dewey", "oclc", "lcsh"]):
        return False
    if any(p in low for p in _OL_AWARD_PATTERNS):
        return False
    return True


def _filter_subjects(subjects: list[str]) -> list[str]:
    return [s for s in subjects if _is_genre_tag(s)]


class TaggerService:
    """
    Gera tags literárias para livros.

    Estratégia:
      1. Open Library Works API — subjects + subject_places + subject_times
         (dois passos: search para obter OLID, depois /works/{OLID}.json)
      2. LLM (Llama via Groq) como fallback — para livros sem cobertura
         suficiente, especialmente brasileiros
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def tag(self, title: str, author: str, description: str | None = None, isbn: str | None = None) -> list[str]:
        tags = await self._from_openlibrary(title, author, isbn)
        if len(tags) >= 3:
            return tags[:8]
        return await self._from_llm(title, author, description)

    async def _from_openlibrary(self, title: str, author: str, isbn: str | None) -> list[str]:
        async with httpx.AsyncClient(timeout=10) as client:
            # Passo 1: busca o OLID do livro
            olid = await self._resolve_olid(client, title, author, isbn)
            if not olid:
                return []

            # Passo 2: busca os subjects estruturados via Works API
            try:
                resp = await client.get(f"{_OL_WORKS_URL}{olid}.json")
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []

            subjects = data.get("subjects", [])
            places = data.get("subject_places", [])
            times = data.get("subject_times", [])

            all_tags = _filter_subjects(subjects + places + times)
            return all_tags

    async def _resolve_olid(
        self, client: httpx.AsyncClient, title: str, author: str, isbn: str | None
    ) -> str | None:
        """Retorna o path do works do Open Library (ex: '/works/OL12345W')."""
        queries = []
        if isbn:
            queries.append({"isbn": isbn, "fields": "key", "limit": 1})
        queries.append({"title": title, "author": author, "fields": "key,title,author_name", "limit": 1})

        for params in queries:
            try:
                resp = await client.get(_OL_SEARCH_URL, params=params)
                resp.raise_for_status()
                docs = resp.json().get("docs", [])
                if not docs:
                    continue
                doc = docs[0]

                # Valida correspondência mínima para evitar falsos positivos
                result_title = doc.get("title", "").lower()
                result_authors = " ".join(doc.get("author_name", [])).lower()
                title_match = any(w in result_title for w in title.lower().split() if len(w) > 3)
                author_match = any(w in result_authors for w in author.lower().split() if len(w) > 3)
                if not (title_match or author_match):
                    continue

                key = doc.get("key")  # ex: "/works/OL12345W"
                if key and "/works/" in key:
                    return key
            except Exception:
                continue
        return None

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
