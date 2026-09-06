import logging
from typing import Any
from django.conf import settings
from .chroma_service import chroma_service
from apps.ai.distilbert_service import distilbert_service

logger = logging.getLogger(__name__)

class VectorRetrievalService:
    """
    Two-stage retrieval pipeline:
    Stage 1: ChromaDB initial vector candidate retrieval (Top 10)
    Stage 2: DistilBERT semantic scoring & threshold filtering (Threshold >= 0.70, return Top 5)
    """

    def __init__(self):
        self.top_k = settings.TOP_K
        self.threshold = settings.SIMILARITY_THRESHOLD

    def retrieve_financial_context(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None,
        filter_metadata: dict = None
    ) -> list[dict[str, Any]]:
        """
        Execute two-stage vector retrieval and DistilBERT semantic filtering.
        """
        k = top_k or self.top_k
        thresh = threshold if threshold is not None else self.threshold

        # Stage 1: ChromaDB retrieval (fetch 2x top_k candidate pool)
        initial_candidates = chroma_service.query(
            query_text=query,
            top_k=max(10, k * 2),
            filter_metadata=filter_metadata
        )

        if not initial_candidates:
            logger.info("ChromaDB returned 0 candidates.")
            return []

        # Stage 2: DistilBERT semantic filtering and scoring
        filtered_candidates = distilbert_service.filter_and_rank_candidates(
            query=query,
            candidates=initial_candidates,
            similarity_threshold=thresh,
            top_k=k
        )

        # Fallback to top ChromaDB candidates if threshold filtered everything out
        if not filtered_candidates and initial_candidates:
            logger.info("DistilBERT threshold filtered out candidates, returning top raw ChromaDB candidates as fallback.")
            filtered_candidates = initial_candidates[:k]

        logger.info(f"Retrieval complete: {len(initial_candidates)} raw candidates -> {len(filtered_candidates)} returned chunks.")
        return filtered_candidates

vector_retrieval_service = VectorRetrievalService()
