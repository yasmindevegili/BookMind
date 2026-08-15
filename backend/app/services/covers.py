import httpx

from ..core.config import get_settings

settings = get_settings()

_GOOGLE_URL = "https://www.googleapis.com/books/v1/volumes"
_OPENLIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
_OPENLIBRARY_COVER_URL = "https://covers.openlibrary.org/b"


class CoverService:
    """
    Fetches book cover images from external sources.

    Strategy (in order):
      1. Google Books API  — highest quality, requires API key
      2. Open Library      — free, no key, broad catalog

    Both calls are async and non-blocking. If both fail, returns None
    so the caller can fall back to a generated placeholder on the frontend.
    """

    async def fetch(self, title: str, author: str, isbn: str | None = None) -> str | None:
        cover = await self._from_google(title, author)
        if cover:
            return cover
        return await self._from_openlibrary(title, author, isbn)

    async def _from_google(self, title: str, author: str) -> str | None:
        # Two passes: strict operators first, then keyword fallback for translated titles
        queries = [
            f'intitle:"{title}" inauthor:"{author}"',
            f'{title} {author}',
        ]
        if settings.GOOGLE_BOOKS_API_KEY:
            key = settings.GOOGLE_BOOKS_API_KEY
        else:
            key = None

        async with httpx.AsyncClient(timeout=10) as client:
            for query in queries:
                params: dict = {
                    "q": query,
                    "maxResults": 1,
                    "printType": "books",
                    "fields": "items/volumeInfo/imageLinks",
                }
                if key:
                    params["key"] = key
                try:
                    resp = await client.get(_GOOGLE_URL, params=params)
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                    if not items:
                        continue
                    links = items[0].get("volumeInfo", {}).get("imageLinks", {})
                    raw = (
                        links.get("extraLarge")
                        or links.get("large")
                        or links.get("medium")
                        or links.get("thumbnail")
                    )
                    if raw:
                        return (
                            raw.replace("http://", "https://")
                            .replace("&edge=curl", "")
                            .replace("zoom=1", "zoom=0")
                        )
                except Exception:
                    continue
        return None

    async def _from_openlibrary(
        self, title: str, author: str, isbn: str | None
    ) -> str | None:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    _OPENLIBRARY_SEARCH_URL,
                    params={"title": title, "author": author, "limit": 1, "fields": "cover_i,isbn"},
                )
                resp.raise_for_status()
                docs = resp.json().get("docs", [])
                if not docs:
                    return None

                cover_id = docs[0].get("cover_i")
                if cover_id:
                    return f"{_OPENLIBRARY_COVER_URL}/id/{cover_id}-L.jpg"

                isbns = docs[0].get("isbn", [])
                if isbns:
                    return f"{_OPENLIBRARY_COVER_URL}/isbn/{isbns[0]}-L.jpg"

                if isbn:
                    return f"{_OPENLIBRARY_COVER_URL}/isbn/{isbn}-L.jpg"
            except Exception:
                pass
        return None


cover_service = CoverService()
