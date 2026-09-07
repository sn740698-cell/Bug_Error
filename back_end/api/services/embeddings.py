import os
import hashlib
import logging
from typing import List
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingProviderInterface:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProviderInterface):
    """
    Deterministic 384-dimensional mock embedding provider for testing and offline execution.
    Does not require external network or API keys.
    """
    DIMENSION = 384

    def _generate_vector(self, text: str) -> List[float]:
        hash_digest = hashlib.sha256(text.encode('utf-8')).digest()
        # Produce normalized floating point values in [-1.0, 1.0]
        raw_vector = [(b / 127.5) - 1.0 for b in hash_digest]
        # Repeat to reach DIMENSION
        vector = (raw_vector * (self.DIMENSION // len(raw_vector) + 1))[:self.DIMENSION]
        norm = sum(x * x for x in vector) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)


class OpenAIEmbeddingProvider(EmbeddingProviderInterface):
    def __init__(self, model: str = "text-embedding-3-small"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing for OpenAI embedding provider.")
        from langchain_openai import OpenAIEmbeddings
        self.embeddings = OpenAIEmbeddings(model=model, api_key=api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class HuggingFaceEmbeddingProvider(EmbeddingProviderInterface):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class OllamaEmbeddingProvider(EmbeddingProviderInterface):
    def __init__(self, model_name: str = "nomic-embed-text"):
        base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        from langchain_community.embeddings import OllamaEmbeddings
        self.embeddings = OllamaEmbeddings(base_url=base_url, model=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


class EmbeddingFactory:
    @staticmethod
    def get_embedding_provider() -> EmbeddingProviderInterface:
        provider = getattr(settings, 'EMBEDDING_PROVIDER', 'mock').lower().strip()
        model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

        if provider == 'mock':
            return MockEmbeddingProvider()
        elif provider == 'openai':
            return OpenAIEmbeddingProvider(model=model_name)
        elif provider in ('huggingface', 'sentence-transformers'):
            return HuggingFaceEmbeddingProvider(model_name=model_name)
        elif provider == 'ollama':
            return OllamaEmbeddingProvider(model_name=model_name)
        else:
            logger.warning(f"Unknown embedding provider '{provider}'. Falling back to MockEmbeddingProvider.")
            return MockEmbeddingProvider()
