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

from dataclasses import dataclass
from ..core.config import get_settings


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


async def _fetch_nyt(api_key: str, list_name: str) -> list[_RawBook]:
    """Busca uma lista específica do NYT Bestsellers."""
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json"
    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.get(url, params={"api-key": api_key})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    books = []
    for b in data.get("results", {}).get("books", []):
        isbn = b.get("primary_isbn13") or b.get("primary_isbn10") or None
        books.append(_RawBook(
            title=b.get("title", "").title(),
            authors=[b.get("author", "")],
            isbn=isbn,
            cover_url=b.get("book_image") or None,
            description=b.get("description") or None,
            source="nyt",
        ))
    return books


def _raw_to_dict(r: _RawBook) -> dict:
    return {"title": r.title, "author": ", ".join(r.authors), "isbn": r.isbn,
            "cover_url": r.cover_url, "description": r.description, "source": r.source}


@router.get("/computed/google-books")
async def google_books_trending(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    raw = await _fetch_google_books(settings.GOOGLE_BOOKS_API_KEY or None)
    matched, discover = await _cross_reference(raw, db)
    return {
        "source": "google_books",
        "name": "Google Books Destaques",
        "matched": [BookResponse.model_validate(b) for b in matched],
        "discover": [_raw_to_dict(r) for r in discover[:20]],
        "configured": True,
    }


@router.get("/computed/nyt")
async def nyt_trending(list_name: str = "hardcover-fiction", db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    if not settings.NYT_API_KEY:
        return {"source": "nyt", "name": "NYT Bestsellers", "matched": [], "discover": [], "configured": False}
    raw = await _fetch_nyt(settings.NYT_API_KEY, list_name)
    matched, discover = await _cross_reference(raw, db)
    label = "Ficção" if "fiction" in list_name else "Não-Ficção"
    return {
        "source": "nyt",
        "name": f"NYT Bestsellers — {label}",
        "matched": [BookResponse.model_validate(b) for b in matched],
        "discover": [_raw_to_dict(r) for r in discover[:15]],
        "configured": True,
    }
