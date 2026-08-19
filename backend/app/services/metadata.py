import httpx

from ..core.config import get_settings

settings = get_settings()

_GOOGLE_URL = "https://www.googleapis.com/books/v1/volumes"


class MetadataService:
    """Fetches book metadata (description, year) from Google Books API."""

    async def fetch(self, title: str, author: str, isbn: str | None = None) -> dict:
        """Returns dict with keys: description, year_published (both may be None)."""
        queries = []
        if isbn:
            queries.append(f"isbn:{isbn}")
        queries.append(f'intitle:"{title}" inauthor:"{author}"')
        queries.append(f"{title} {author}")

        params_base: dict = {
            "maxResults": 1,
            "printType": "books",
            "fields": "items/volumeInfo(title,authors,description,publishedDate)",
        }
        if settings.GOOGLE_BOOKS_API_KEY:
            params_base["key"] = settings.GOOGLE_BOOKS_API_KEY

        async with httpx.AsyncClient(timeout=10) as client:
            for query in queries:
                try:
                    resp = await client.get(
                        _GOOGLE_URL, params={"q": query, **params_base}
                    )
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                    if not items:
                        continue
                    info = items[0].get("volumeInfo", {})
                    # Valida que o resultado corresponde minimamente ao livro buscado
                    result_title = info.get("title", "").lower()
                    result_author = " ".join(info.get("authors", [])).lower()
                    title_match = any(w in result_title for w in title.lower().split() if len(w) > 3)
                    author_match = any(w in result_author for w in author.lower().split() if len(w) > 3)
                    if not (title_match or author_match):
                        continue
                    description = info.get("description") or None
                    published = info.get("publishedDate") or None
                    year = int(published[:4]) if published and published[:4].isdigit() else None
                    if description or year:
                        return {"description": description, "year_published": year}
                except Exception:
                    continue

        return {"description": None, "year_published": None}


metadata_service = MetadataService()
