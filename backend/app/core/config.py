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

    # Calibre-Web (Babel) — fonte de capas local
    BABEL_URL: str = "http://192.168.1.56:8083"
    BABEL_USER: str = ""
    BABAL_PASS: str = ""  # typo preservado do .env original

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
