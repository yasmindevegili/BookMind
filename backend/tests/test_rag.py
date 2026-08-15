"""
Testes do pipeline RAG.

Usamos mocks para não chamar APIs reais durante os testes.
Mock = objeto falso que simula o comportamento real.

Por que mockar aqui?
  - fastembed carrega um modelo de 90MB — lento em CI
  - Groq depende de internet e API key
  - Queremos testar a LÓGICA, não as APIs externas

Execute com: pytest tests/test_rag.py -v
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_rag_retorna_mensagem_quando_sem_anotacoes():
    """Sem anotações indexadas, o chat deve explicar o que fazer."""
    from app.services.rag import RAGService

    service = RAGService()
    mock_db = AsyncMock()

    with patch.object(service, "search", new=AsyncMock(return_value=[])):
        result = await service.chat("o que li sobre coragem?", mock_db)

    assert "answer" in result
    assert "sources" in result
    assert result["sources"] == []
    assert len(result["answer"]) > 10


@pytest.mark.asyncio
async def test_embedding_retorna_vetor_com_384_dimensoes():
    """EmbeddingService.embed() deve retornar lista de 384 floats."""
    from app.services.embeddings import EmbeddingService

    service = EmbeddingService()
    import numpy as np
    mock_embedding = np.array([0.1] * 384)

    mock_model = MagicMock()
    mock_model.embed.return_value = iter([mock_embedding])
    service._model = mock_model

    result = await service.embed("introversão e personalidade")

    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_context_inclui_titulo_e_autor():
    """_build_context deve formatar cada anotação com informações do livro."""
    from app.models.annotation import Annotation
    from app.models.book import Book
    from app.services.rag import RAGService

    service = RAGService()

    book = Book()
    book.id = 1
    book.title = "Silêncio"
    book.author = "Susan Cain"

    annotation = Annotation()
    annotation.book_id = 1
    annotation.content = "Introversão não é uma falha a ser corrigida."
    annotation.chapter = "Introdução"

    context = service._build_context([annotation], {1: book})

    assert "Silêncio" in context
    assert "Susan Cain" in context
    assert "Introversão não é uma falha" in context
    assert "Introdução" in context
