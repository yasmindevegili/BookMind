import asyncio
import json
import time

import httpx
from groq import AsyncGroq

from ..core.config import get_settings

settings = get_settings()

# Modelo dedicado ao tagger — sem thinking mode, retorna JSON limpo e rápido
_TAGGER_MODEL = "groq/compound-mini"

_OL_SEARCH_URL = "https://openlibrary.org/search.json"
_OL_WORKS_URL = "https://openlibrary.org"

_OL_NOISE = {
    "fiction", "nonfiction", "non-fiction", "accessible book", "protected daisy",
    "in library", "large type books", "open library", "internet archive",
    "overdrive", "lending library", "english language", "juvenile fiction",
    "juvenile literature", "young adult fiction", "children", "drama",
    "biography", "autobiography", "history", "geography", "science",
    "technology", "social science", "language arts", "literature",
}

_OL_AWARD_PATTERNS = [
    "prêmio", "premio", "prize", "award", "winner", "finalist", "shortlist",
    "booker", "pulitzer", "nobel", "jabuti", "camões", "pen ", "hugo award",
    "nebula", "escritas por", "coleção", "colecao", "series", "classics",
    "penguin", "vintage", "everyman", "biblioteca",
]


def _is_award_tag(s: str) -> bool:
    low = s.lower().strip()
    return any(p in low for p in _OL_AWARD_PATTERNS)


def _split_subjects(subjects: list[str]) -> tuple[list[str], list[str]]:
    """Separa subjects em (tags_literárias, tags_de_prêmio)."""
    genre_tags, award_tags = [], []
    for s in subjects:
        low = s.lower().strip()
        if low in _OL_NOISE or len(low) < 4 or len(low) > 60:
            continue
        if any(p in low for p in ["isbn", "lccn", "dewey", "oclc", "lcsh"]):
            continue
        if _is_award_tag(s):
            award_tags.append(s)
        else:
            genre_tags.append(s)
    return genre_tags, award_tags


class TaggerService:
    """
    Gera tags literárias para livros.

    Estratégia:
      1. LLM retorna title_en (título original em inglês) + tags de fallback em uma única chamada JSON
      2. Open Library Works API buscado com title_en — subjects são mais ricos e precisos
         (dois passos: search para obter OLID, depois /works/{OLID}.json)
      3. Se Open Library retornar ≥3 genre_tags, substitui as tags do LLM
      4. title_en é persistido no banco como cache — re-tagueações futuras pulam o LLM
    """

    # Semáforos em nível de instância evitam bloqueio residual após cancelamento de tasks
    # (ex: restart do backend cancela tasks em voo, deixando semáforos de classe travados)
    _llm_last: float = 0.0

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._ol_sem = asyncio.Semaphore(10)
        self._llm_sem = asyncio.Semaphore(1)

    async def tag(
        self,
        title: str,
        author: str,
        description: str | None = None,
        isbn: str | None = None,
        title_en: str | None = None,
    ) -> tuple[list[str], list[str], str | None]:
        """Retorna (tags_literárias, tags_de_prêmio, title_en_resolvido)."""
        llm_tags: list[str] = []
        resolved_title_en = title_en

        if not title_en:
            resolved_title_en, llm_tags = await self._from_llm_combined(title, author, description)

        search_title = resolved_title_en or title
        ol_genre_tags, award_tags = await self._from_openlibrary(search_title, author, isbn)

        if len(ol_genre_tags) >= 3:
            return ol_genre_tags[:8], award_tags, resolved_title_en

        # Open Library não teve cobertura suficiente — usa tags do LLM
        if not llm_tags:
            # title_en já era conhecido, mas OL falhou; pede só tags ao LLM
            llm_tags = await self._from_llm_tags_only(title, author, description)

        return llm_tags, award_tags, resolved_title_en

    async def _from_llm_combined(
        self, title: str, author: str, description: str | None
    ) -> tuple[str | None, list[str]]:
        """Chama o LLM uma única vez para obter title_en + tags de fallback em JSON."""
        async with self._llm_sem:
            wait = 2.1 - (time.monotonic() - self.__class__._llm_last)
            if wait > 0:
                await asyncio.sleep(wait)
            self.__class__._llm_last = time.monotonic()

            desc_ctx = f"\nSinopse: {description[:300]}" if description else ""
            prompt = (
                f'Livro: "{title}" de {author}.{desc_ctx}\n\n'
                'Responda APENAS com JSON válido, sem markdown, sem explicações:\n'
                '{\n'
                '  "title_en": "<título original em inglês, ou mesmo título se já for inglês ou autor brasileiro>",\n'
                '  "tags": ["<tag1>", "<tag2>", ...]\n'
                '}\n\n'
                'Para tags: liste de 6 a 8 tags literárias em português (minúsculas) '
                'descrevendo subgênero, temas, época/cenário, estilo narrativo e tom emocional.'
            )
            try:
                resp = await self.client.chat.completions.create(
                    model=_TAGGER_MODEL,
                    max_tokens=300,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.choices[0].message.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
                title_en = data.get("title_en") or None
                raw_tags = data.get("tags", [])
                tags = [t.strip().lower() for t in raw_tags if isinstance(t, str) and t.strip()]
                tags = [t for t in tags if 3 <= len(t) <= 50][:8]
                return title_en, tags
            except Exception:
                return None, []

    async def _from_llm_tags_only(
        self, title: str, author: str, description: str | None
    ) -> list[str]:
        """Fallback de tags apenas (quando title_en já era conhecido mas OL falhou)."""
        async with self._llm_sem:
            wait = 2.1 - (time.monotonic() - self.__class__._llm_last)
            if wait > 0:
                await asyncio.sleep(wait)
            self.__class__._llm_last = time.monotonic()

            desc_ctx = f"\nSinopse: {description[:300]}" if description else ""
            prompt = (
                f'Livro: "{title}" de {author}.{desc_ctx}\n\n'
                "Liste de 6 a 8 tags literárias compactas em português (minúsculas) "
                "que descrevam: subgênero, temas principais, época/cenário, estilo narrativo e tom emocional. "
                "Responda APENAS com as tags separadas por vírgula, sem explicações nem numeração."
            )
            try:
                resp = await self.client.chat.completions.create(
                    model=_TAGGER_MODEL,
                    max_tokens=150,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.choices[0].message.content.strip()
                tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
                return [t for t in tags if 3 <= len(t) <= 50][:8]
            except Exception:
                return []

    async def _from_openlibrary(
        self, title: str, author: str, isbn: str | None
    ) -> tuple[list[str], list[str]]:
        async with self._ol_sem:
            async with httpx.AsyncClient(timeout=10, verify=False) as client:
                olid = await self._resolve_olid(client, title, author, isbn)
                if not olid:
                    return [], []

                try:
                    resp = await client.get(f"{_OL_WORKS_URL}{olid}.json")
                    resp.raise_for_status()
                    data = resp.json()
                except Exception:
                    return [], []

                all_subjects = (
                    data.get("subjects", [])
                    + data.get("subject_places", [])
                    + data.get("subject_times", [])
                )
                return _split_subjects(all_subjects)

    async def _resolve_olid(
        self, client: httpx.AsyncClient, title: str, author: str, isbn: str | None
    ) -> str | None:
        """Retorna o path do works do Open Library (ex: '/works/OL12345W').

        Ordem de tentativas: ISBN → title (já deve ser title_en) + author.
        """
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

                result_title = doc.get("title", "").lower()
                result_authors = " ".join(doc.get("author_name", [])).lower()
                title_match = any(w in result_title for w in title.lower().split() if len(w) > 3)
                author_match = any(w in result_authors for w in author.lower().split() if len(w) > 3)
                if not (title_match or author_match):
                    continue

                key = doc.get("key")
                if key and "/works/" in key:
                    return key
            except Exception:
                continue
        return None


tagger_service = TaggerService()
