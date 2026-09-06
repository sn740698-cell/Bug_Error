import logging
from typing import Any

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generates embeddings for document chunks using lightweight SentenceTransformers or default Chroma embedding."""

    def __init__(self):
        self._embedding_fn = None

    def get_embedding_function(self):
        """Lazy load ChromaDB default embedding function."""
        if self._embedding_fn is not None:
            return self._embedding_fn

        try:
            from chromadb.utils import embedding_functions
            self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
            logger.warning(f"Default embedding function initialization warning ({e}). Using standard Chroma embedding.")
            self._embedding_fn = None
        return self._embedding_fn

embedding_service = EmbeddingService()
