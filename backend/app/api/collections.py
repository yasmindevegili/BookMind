import asyncio
import unicodedata
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ..core.database import get_db
from ..models.associations import collection_books
from ..models.book import Book, BookStatus
from ..models.collection import Collection
from ..schemas.book import BookResponse
from ..schemas.collection import CollectionSummary

router = APIRouter()

# ── Prêmios (coleções estáticas) ──────────────────────────────────

_AWARD_KEYWORDS: dict[str, list[str]] = {
    "Nobel de Literatura": ["nobel"],
    "Prêmio Jabuti":       ["jabuti"],
    "Booker Prize":        ["booker"],
    "Prêmio Pulitzer":     ["pulitzer"],
    "Prêmio Camões":       ["camões", "camoes"],
}

_GENRE_EXCLUDE = {"Ficção", "Geral", "Literatura"}


def _slug(name: str) -> str:
    import re
    import unicodedata
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower().strip()).strip("-")


@router.get("/", response_model=list[CollectionSummary])
async def list_collections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection, func.count(collection_books.c.book_id).label("book_count"))
        .outerjoin(collection_books, Collection.id == collection_books.c.collection_id)
        .where(Collection.type == "curadoria")
        .group_by(Collection.id)
        .order_by(Collection.name)
    )
    return [
        CollectionSummary(
            id=col.id,
            name=col.name,
            slug=col.slug,
            description=col.description,
            type=col.type,
            book_count=count,
        )
        for col, count in result.all()
    ]


@router.get("/{slug}/books", response_model=list[BookResponse])
async def get_collection_books(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book)
        .options(defer(Book.embedding))
        .join(collection_books, Book.id == collection_books.c.book_id)
        .join(Collection, Collection.id == collection_books.c.collection_id)
        .where(Collection.slug == slug)
        .order_by(Book.title)
    )
    return result.scalars().all()


@router.post("/initialize")
async def initialize_collections(db: AsyncSession = Depends(get_db)):
    """Detecta prêmios em títulos/descrições e popula coleções editoriais. Idempotente."""
    stats: dict[str, int] = {}

    for award_name, keywords in _AWARD_KEYWORDS.items():
        slug = _slug(award_name)
        col_result = await db.execute(select(Collection).where(Collection.slug == slug))
        collection = col_result.scalar_one_or_none()
        if not collection:
            collection = Collection(name=award_name, slug=slug, type="curadoria")
            db.add(collection)
            await db.flush()

        conditions = []
        for kw in keywords:
            like = f"%{kw}%"
            conditions.append(Book.title.ilike(like))
            conditions.append(Book.description.ilike(like))

        books_result = await db.execute(select(Book.id).where(or_(*conditions)))
        book_ids = [row[0] for row in books_result.all()]

        if book_ids:
            await db.execute(
                pg_insert(collection_books)
                .values([{"collection_id": collection.id, "book_id": bid} for bid in book_ids])
                .on_conflict_do_nothing()
            )

        stats[award_name] = len(book_ids)

    await db.commit()
    return {"initialized": stats}


# ── Computed / Dynamic Collections ────────────────────────────────

_COMPUTED_META = [
    {
        "slug": "em-alta",
        "name": "Em Alta no Mundo",
        "emoji": "🌍",
        "description": "Livros do seu acervo que estão em destaque global (Open Library trending)",
    },
    {
        "slug": "quero-ler",
        "name": "Quero Ler",
        "emoji": "📌",
        "description": "Livros que você marcou para ler",
    },
    {
        "slug": "ja-lidos",
        "name": "Já Lidos",
        "emoji": "✅",
        "description": "Livros que você já leu",
    },
]


@router.get("/computed")
async def list_computed():
    return _COMPUTED_META


@router.get("/computed/generos")
async def list_genres(db: AsyncSession = Depends(get_db)):
    """Top gêneros do acervo, excluindo categorias genéricas."""
    result = await db.execute(
        select(Book.genre, func.count(Book.id).label("cnt"))
        .where(Book.genre.is_not(None))
        .where(Book.genre != "")
        .group_by(Book.genre)
        .having(func.count(Book.id) >= 5)
        .order_by(func.count(Book.id).desc())
    )
    return [
        {"name": r.genre, "count": r.cnt}
        for r in result.all()
        if r.genre not in _GENRE_EXCLUDE
    ][:10]


@router.get("/computed/genero/{genre}", response_model=list[BookResponse])
async def genre_books(genre: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book)
        .options(defer(Book.embedding))
        .where(func.lower(Book.genre) == func.lower(genre))
        .order_by(Book.title)
        .limit(50)
    )
    return result.scalars().all()


@router.get("/computed/{slug}/books", response_model=list[BookResponse])
async def computed_books(slug: str, db: AsyncSession = Depends(get_db)):
    if slug == "em-alta":
        return await _em_alta(db)
    if slug == "quero-ler":
        result = await db.execute(
            select(Book)
            .options(defer(Book.embedding))
            .where(Book.status == BookStatus.want_to_read)
            .order_by(Book.title)
            .limit(50)
        )
        return result.scalars().all()
    if slug == "ja-lidos":
        result = await db.execute(
            select(Book)
            .options(defer(Book.embedding))
            .where(Book.status == BookStatus.read)
            .order_by(Book.title)
            .limit(50)
        )
        return result.scalars().all()
    return []


def _surname(name: str) -> str | None:
    """Extrai o sobrenome (última palavra com 4+ chars) de um nome de autor."""
    words = [w for w in name.split() if len(w) >= 4 and w.isalpha()]
    return words[-1].lower() if words else None


async def _em_alta(db: AsyncSession) -> list:
    try:
        async with httpx.AsyncClient(timeout=8, verify=False) as client:
            resp = await client.get("https://openlibrary.org/trending/daily.json")
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    works = data.get("works", [])

    # Tenta 1: cruzar pelo título original (quando title_en está populado)
    ol_titles = {w["title"].strip().lower() for w in works if w.get("title")}

    # Tenta 2: cruzar por sobrenome de autor (idioma-agnóstico)
    surnames: set[str] = set()
    for w in works:
        for author in w.get("author_name", []):
            s = _surname(author)
            if s:
                surnames.add(s)

    if not ol_titles and not surnames:
        return []

    conditions = [func.lower(Book.title_en).in_(ol_titles)] if ol_titles else []
    for surname in list(surnames)[:30]:
        conditions.append(Book.author.ilike(f"%{surname}%"))

    result = await db.execute(
        select(Book)
        .options(defer(Book.embedding))
        .where(or_(*conditions))
        .order_by(Book.title)
        .limit(50)
    )
    return result.scalars().all()


# ── Trending Externos (Google Books + NYT) ────────────────────────

import time
from dataclasses import dataclass
from ..core.config import get_settings

# Cache em memória para resultados de APIs externas — evita esgotar quota em testes
# (simplificação intencional: em produção, usaria Redis com TTL distribuído)
_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 60 * 60 * 6  # 6 horas


def _cache_get(key: str) -> object | None:
    entry = _CACHE.get(key)
    if entry and time.monotonic() - entry[0] < _CACHE_TTL:
        return entry[1]
    _CACHE.pop(key, None)
    return None


def _cache_set(key: str, value: object) -> None:
    _CACHE[key] = (time.monotonic(), value)


@dataclass
class _RawBook:
    title: str
    authors: list[str]
    isbn: str | None
    cover_url: str | None
    description: str | None
    source: str


async def _cross_reference(raw_books: list[_RawBook], db: AsyncSession):
    """Cruza livros externos com o acervo pelo ISBN."""
    isbns = [b.isbn for b in raw_books if b.isbn]
    matched_map: dict[str, Book] = {}
    if isbns:
        res = await db.execute(
            select(Book).options(defer(Book.embedding)).where(Book.isbn.in_(isbns))
        )
        for book in res.scalars().all():
            if book.isbn:
                matched_map[book.isbn] = book

    matched, discover = [], []
    for raw in raw_books:
        if raw.isbn and raw.isbn in matched_map:
            matched.append(matched_map[raw.isbn])
        else:
            discover.append(raw)
    return matched, discover


async def _cross_reference_by_title(raw_books: list[_RawBook], db: AsyncSession):
    """Cruza livros externos com o acervo por título (para fontes sem ISBN)."""
    titles = [b.title for b in raw_books if b.title]
    matched_map: dict[str, Book] = {}
    for title in titles:
        res = await db.execute(
            select(Book).options(defer(Book.embedding))
            .where(Book.title.ilike(f"%{title}%"))
            .limit(1)
        )
        book = res.scalar_one_or_none()
        if book:
            matched_map[title.lower()] = book

    matched, discover = [], []
    for raw in raw_books:
        key = raw.title.lower()
        if key in matched_map:
            matched.append(matched_map[key])
        else:
            discover.append(raw)
    return matched, discover


async def _fetch_google_books(api_key: str | None) -> list[_RawBook]:
    """Busca bestsellers no Google Books (funciona sem key, com rate limit suave)."""
    params: dict = {"q": "bestseller", "maxResults": 40, "orderBy": "relevance", "printType": "books"}
    if api_key:
        params["key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.get("https://www.googleapis.com/books/v1/volumes", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    books = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        title = info.get("title", "").strip()
        authors = info.get("authors", [])
        if not title or not authors:
            continue

        isbn = None
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13":
                isbn = ident["identifier"]
                break

        thumb = info.get("imageLinks", {}).get("thumbnail", "")
        cover = thumb.replace("http://", "https://").replace("zoom=1", "zoom=2") if thumb else None
        desc = info.get("description", "")[:500] if info.get("description") else None

        books.append(_RawBook(title=title, authors=authors, isbn=isbn,
                              cover_url=cover, description=desc, source="google_books"))
    return books


async def _fetch_tag_livros(collection: str = "best-sellers") -> list[_RawBook]:
    """Busca curadoria Tag Livros via Shopify JSON API (sem key, já em português)."""
    url = f"https://livraria.taglivros.com/collections/{collection}/products.json"
    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.get(url, params={"limit": 30})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    books = []
    for p in data.get("products", []):
        raw_title: str = p.get("title", "").strip()
        # Remove prefixo "Kit " ou "Livro " que a Tag usa nos produtos
        title = raw_title.removeprefix("Kit ").removeprefix("Livro ").strip()
        if not title:
            continue

        # Autor vem nas tags do produto Shopify (ex: ['best-seller', 'Maya Angelou'])
        skip_tags = {"best-seller", "2024", "2025", "2026", "kit", "livro"}
        authors = [t.title() for t in p.get("tags", []) if t.lower() not in skip_tags]

        imgs = p.get("images", [])
        cover = imgs[0].get("src") if imgs else None

        body_html: str = p.get("body_html") or ""
        # Remove HTML para extrair texto da descrição
        import re as _re
        desc = _re.sub(r"<[^>]+>", " ", body_html).strip()[:400] or None

        books.append(_RawBook(
            title=title,
            authors=authors if authors else ["Tag Livros"],
            isbn=None,
            cover_url=cover,
            description=desc or None,
            source="tag_livros",
        ))
    return books


async def _find_portuguese_edition(
    client: httpx.AsyncClient,
    title: str,
    author: str,
    gb_key: str | None,
) -> "_RawBook | None":
    """Busca edição em português de um livro originalmente em inglês via Google Books.

    Estratégia: busca o título original como palavra-chave + autor com langRestrict=pt.
    Edições PT no Google Books costumam mencionar o título original em inglês na descrição
    (ex: "Tradução de 'Onyx Storm'"), então a busca de texto livre acha a tradução certa
    mesmo que o título PT seja completamente diferente.
    """
    author_last = author.split()[-1]
    params = {
        "q": f'"{title}" "{author_last}"',
        "maxResults": 5,
        "langRestrict": "pt",
        "printType": "books",
    }
    if gb_key:
        params["key"] = gb_key
    try:
        resp = await client.get("https://www.googleapis.com/books/v1/volumes", params=params)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception:
        return None

    for item in items:
        info = item.get("volumeInfo", {})

        # Rejeita se o idioma do livro não for português — langRestrict=pt pode
        # retornar livros em inglês disponíveis no mercado PT/BR
        if info.get("language", "en") not in ("pt", "pt-BR", "pt-PT"):
            continue

        pt_title = (info.get("title") or "").strip()
        pt_authors = info.get("authors", [])
        if not pt_title or not pt_authors:
            continue

        # Rejeita se o título PT for idêntico ao inglês (não é tradução real)
        def _norm(s: str) -> str:
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
        if _norm(pt_title) == _norm(title):
            continue

        # Valida: pelo menos uma palavra do sobrenome do autor original deve aparecer
        author_last = author.split()[-1].lower()
        if not any(author_last in a.lower() for a in pt_authors):
            continue

        isbn = None
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13":
                isbn = ident["identifier"]
                break

        thumb = info.get("imageLinks", {}).get("thumbnail", "")
        cover = thumb.replace("http://", "https://").replace("zoom=1", "zoom=2") if thumb else None

        return _RawBook(
            title=pt_title,
            authors=pt_authors,
            isbn=isbn,
            cover_url=cover,
            description=(info.get("description") or "")[:500] or None,
            source="nyt_pt",
        )
    return None


def _nyt_target_date() -> str:
    """Retorna uma data ~12 meses atrás — tempo suficiente para traduções PT existirem."""
    from datetime import date, timedelta
    target = date.today().replace(day=1) - timedelta(days=365)
    return target.strftime("%Y-%m-%d")


async def _fetch_nyt(api_key: str, list_name: str, gb_key: str | None = None) -> list[_RawBook]:
    """Busca lista NYT de ~12 meses atrás e substitui por edições em português via Google Books."""
    date_str = _nyt_target_date()
    url = f"https://api.nytimes.com/svc/books/v3/lists/{date_str}/{list_name}.json"
    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.get(url, params={"api-key": api_key})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    en_books: list[_RawBook] = []
    for b in data.get("results", {}).get("books", []):
        isbn = b.get("primary_isbn13") or b.get("primary_isbn10") or None
        en_books.append(_RawBook(
            title=b.get("title", "").title(),
            authors=[b.get("author", "")],
            isbn=isbn,
            cover_url=b.get("book_image") or None,
            description=b.get("description") or None,
            source="nyt",
        ))

    if not en_books:
        return []

    # Busca edições em PT em paralelo para todos os livros
    async with httpx.AsyncClient(timeout=10, verify=False) as client:
        pt_results = await asyncio.gather(
            *[_find_portuguese_edition(client, b.title, b.authors[0], gb_key) for b in en_books],
            return_exceptions=True,
        )

    books = []
    for en, pt in zip(en_books, pt_results):
        if isinstance(pt, _RawBook):
            books.append(pt)
        else:
            books.append(en)
    return books


def _raw_to_dict(r: _RawBook) -> dict:
    return {"title": r.title, "author": ", ".join(r.authors), "isbn": r.isbn,
            "cover_url": r.cover_url, "description": r.description, "source": r.source}


@router.get("/computed/google-books")
async def google_books_trending(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    cache_key = "google_books_trending"
    raw = _cache_get(cache_key)
    if raw is None:
        raw = await _fetch_google_books(settings.GOOGLE_BOOKS_API_KEY or None)
        _cache_set(cache_key, raw)
    matched, discover = await _cross_reference(raw, db)
    return {
        "source": "google_books",
        "name": "Google Books Destaques",
        "matched": [BookResponse.model_validate(b) for b in matched],
        "discover": [_raw_to_dict(r) for r in discover[:20]],
        "configured": True,
    }


@router.get("/computed/tag-livros")
async def tag_livros_trending(collection: str = "best-sellers", db: AsyncSession = Depends(get_db)):
    cache_key = f"tag_livros_{collection}"
    raw = _cache_get(cache_key)
    if raw is None:
        raw = await _fetch_tag_livros(collection)
        _cache_set(cache_key, raw)
    matched, discover = await _cross_reference_by_title(raw, db)
    label_map = {"best-sellers": "Best-Sellers", "kits-curadoria": "Curadoria Editorial"}
    label = label_map.get(collection, collection.replace("-", " ").title())
    return {
        "source": "tag_livros",
        "name": f"Tag Livros — {label}",
        "matched": [BookResponse.model_validate(b) for b in matched],
        "discover": [_raw_to_dict(r) for r in discover[:20]],
        "configured": True,
    }


_PUBLISHERS_BR = [
    "Companhia das Letras",
    "Intrínseca",
    "Record",
    "Rocco",
    "Sextante",
    "Planeta",
    "Darkside",
    "Aleph",
    "Objetiva",
    "Bertrand Brasil",
]


async def _fetch_lancamentos_publisher(
    client: httpx.AsyncClient, publisher: str, api_key: str | None
) -> list[dict]:
    """Busca lançamentos recentes de uma editora no Google Books."""
    from datetime import date
    min_year = date.today().year - 2  # últimos 2 anos
    params = {
        "q": f'inpublisher:"{publisher}"',
        "maxResults": 8,
        "orderBy": "newest",
        "printType": "books",
        "langRestrict": "pt",
    }
    if api_key:
        params["key"] = api_key
    try:
        resp = await client.get("https://www.googleapis.com/books/v1/volumes", params=params)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception:
        return []

    results = []
    for item in items:
        info = item.get("volumeInfo", {})
        if info.get("language") not in ("pt", "pt-BR", "pt-PT", None):
            continue
        pub_date = info.get("publishedDate", "")
        try:
            pub_year = int(pub_date[:4])
        except (ValueError, TypeError):
            pub_year = 0
        if pub_year and pub_year < min_year:
            continue

        title = (info.get("title") or "").strip()
        # Google Books às vezes retorna títulos em ALL CAPS
        if title == title.upper() and len(title) > 3:
            title = title.title()
        authors = info.get("authors") or []
        if not title or not authors:
            continue

        isbn = None
        for ident in info.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13":
                isbn = ident["identifier"]
                break

        thumb = info.get("imageLinks", {}).get("thumbnail", "")
        cover = thumb.replace("http://", "https://").replace("zoom=1", "zoom=2") if thumb else None
        rating = info.get("averageRating")

        results.append({
            "title": title,
            "author": ", ".join(authors),
            "isbn": isbn,
            "cover_url": cover,
            "description": (info.get("description") or "")[:400] or None,
            "publisher": info.get("publisher") or publisher,
            "published_date": pub_date,
            "rating": rating,
            "source": "google_books",
        })
    return results


@router.get("/computed/lancamentos")
async def lancamentos(db: AsyncSession = Depends(get_db)):
    cache_key = "lancamentos"
    cached = _cache_get(cache_key)
    if cached is not None:
        books_raw = cached
    else:
        settings = get_settings()
        api_key = settings.GOOGLE_BOOKS_API_KEY or None
        async with httpx.AsyncClient(timeout=12, verify=False) as client:
            results = await asyncio.gather(
                *[_fetch_lancamentos_publisher(client, pub, api_key) for pub in _PUBLISHERS_BR],
                return_exceptions=True,
            )
        # Agrupa, deduplica por ISBN e ordena por data de publicação
        seen_isbns: set[str] = set()
        seen_titles: set[str] = set()
        books_raw = []
        for batch in results:
            if isinstance(batch, list):
                for b in batch:
                    key = b["isbn"] if b["isbn"] else b["title"].lower()
                    if key in seen_isbns or b["title"].lower() in seen_titles:
                        continue
                    seen_isbns.add(key)
                    seen_titles.add(b["title"].lower())
                    books_raw.append(b)
        books_raw.sort(key=lambda b: b.get("published_date") or "", reverse=True)
        _cache_set(cache_key, books_raw)

    # Cruza com acervo por ISBN (defer não se aplica a select de colunas individuais)
    isbns = [b["isbn"] for b in books_raw if b.get("isbn")]
    acervo_map: dict[str, int] = {}
    title_acervo_map: dict[str, int] = {}
    if isbns:
        res = await db.execute(select(Book.id, Book.isbn).where(Book.isbn.in_(isbns)))
        for book_id, book_isbn in res.all():
            if book_isbn:
                acervo_map[book_isbn] = book_id
    # fallback por título
    for b in books_raw:
        if b.get("isbn") and b["isbn"] in acervo_map:
            continue
        res = await db.execute(
            select(Book.id).where(Book.title.ilike(b["title"])).limit(1)
        )
        row = res.scalar_one_or_none()
        if row:
            title_acervo_map[b["title"].lower()] = row

    books_out = []
    for b in books_raw:
        acervo_id = acervo_map.get(b.get("isbn") or "") or title_acervo_map.get(b["title"].lower())
        books_out.append({**b, "in_acervo": bool(acervo_id), "acervo_id": acervo_id})

    return {"books": books_out[:50]}


@router.get("/computed/nyt")
async def nyt_trending(list_name: str = "hardcover-fiction", db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    if not settings.NYT_API_KEY:
        return {"source": "nyt", "name": "NYT Bestsellers", "matched": [], "discover": [], "configured": False}
    cache_key = f"nyt_{list_name}"
    raw = _cache_get(cache_key)
    if raw is None:
        raw = await _fetch_nyt(settings.NYT_API_KEY, list_name, settings.GOOGLE_BOOKS_API_KEY or None)
        _cache_set(cache_key, raw)
    matched, discover = await _cross_reference(raw, db)
    label = "Ficção" if "fiction" in list_name else "Não-Ficção"
    year = _nyt_target_date()[:4]
    return {
        "source": "nyt",
        "name": f"NYT Bestsellers {year} — {label}",
        "matched": [BookResponse.model_validate(b) for b in matched],
        "discover": [_raw_to_dict(r) for r in discover[:15]],
        "configured": True,
    }
