from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://bookmind:bookmind@localhost:5432/bookmind"
    REDIS_URL: str = "redis://localhost:6379"

    GROQ_API_KEY: str = ""
    GOOGLE_BOOKS_API_KEY: str = ""

    # Modelo de embeddings local (fastembed, sem API key, suporte a português)
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSIONS: int = 384  # dimensões do modelo multilingual

    # Modelo de geração via Groq (gratuito)
    GENERATION_MODEL: str = "llama-3.3-70b-versatile"

    RAG_TOP_K: int = 5

    # Modo debug: limita livros retornados na listagem (0 = desativado)
    DEBUG_BOOK_LIMIT: int = 0

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
