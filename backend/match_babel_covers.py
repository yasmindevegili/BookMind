"""
Cruza livros do BookMind com o Calibre-Web (Babel) e atualiza cover_url
para /api/covers/babel/{babel_id}.

Estratégia de matching (em ordem de prioridade):
  1. ISBN exato (apenas dígitos)
  2. ISBN parcial (últimos 10 dígitos — ISBN-10 vs ISBN-13)
  3. Título normalizado + autor normalizado

Execução:
  docker compose exec backend python match_babel_covers.py
"""

import asyncio
import re
import unicodedata

import httpx
from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.book import Book


def _digits(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", text).strip()


async def _fetch_babel_books() -> list[dict]:
    s = get_settings()
    timeout = httpx.Timeout(connect=15, read=120, write=30, pool=10)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # Login
        resp = await client.get(f"{s.BABEL_URL}/login")
        match = re.search(r'csrf_token"\s+value="([^"]+)"', resp.text)
        if not match:
            raise RuntimeError("CSRF token não encontrado no Babel")
        csrf = match.group(1)
        await client.post(
            f"{s.BABEL_URL}/login",
            data={"username": s.BABEL_USER, "password": s.BABAL_PASS, "next": "/", "csrf_token": csrf},
        )
        # Busca paginada em blocos de 500 para evitar timeout
        all_books: list[dict] = []
        page_size = 500
        offset = 0
        while True:
            resp = await client.get(
                f"{s.BABEL_URL}/ajax/listbooks",
                params={"limit": page_size, "offset": offset},
            )
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("rows", [])
            all_books.extend(rows)
            total = data.get("total", 0)
            offset += page_size
            print(f"  página: {offset}/{total} livros baixados", end="\r")
            if offset >= total or not rows:
                break
        print()
        return all_books


async def main() -> None:
    print("Buscando livros do Babel...")
    babel_books = await _fetch_babel_books()
    print(f"  {len(babel_books)} livros encontrados no Babel")

    # Indexa Babel por ISBN e por título+autor normalizado
    isbn_index: dict[str, int] = {}      # isbn_digits → babel_id
    isbn10_index: dict[str, int] = {}    # últimos 10 dígitos → babel_id
    title_index: dict[str, int] = {}     # "titulo autor" → babel_id

    for b in babel_books:
        bid = b["id"]
        raw_isbn = _digits(b.get("isbn", ""))
        if raw_isbn:
            isbn_index[raw_isbn] = bid
            isbn10_index[raw_isbn[-10:]] = bid

        title_key = _normalize(b.get("sort", b.get("title", ""))) + " " + _normalize(b.get("authors", ""))
        title_index[title_key] = bid

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Book))
        books = result.scalars().all()
        print(f"  {len(books)} livros no BookMind")

        matched = 0
        no_match = 0

        for book in books:
            babel_id: int | None = None
            isbn_digits = _digits(book.isbn)

            # 1. ISBN exato
            if isbn_digits and isbn_digits in isbn_index:
                babel_id = isbn_index[isbn_digits]

            # 2. ISBN-10 (últimos 10 dígitos)
            if not babel_id and isbn_digits and isbn_digits[-10:] in isbn10_index:
                babel_id = isbn10_index[isbn_digits[-10:]]

            # 3. Título + autor normalizado
            if not babel_id:
                key = _normalize(book.title) + " " + _normalize(book.author)
                babel_id = title_index.get(key)

            if babel_id:
                await db.execute(
                    update(Book)
                    .where(Book.id == book.id)
                    .values(cover_url=f"/api/covers/babel/{babel_id}")
                )
                matched += 1
            else:
                no_match += 1

        await db.commit()

    print(f"\nResultado:")
    print(f"  ✓ {matched} livros com capa do Babel")
    print(f"  ✗ {no_match} livros sem match (cover_url mantida)")


if __name__ == "__main__":
    asyncio.run(main())
