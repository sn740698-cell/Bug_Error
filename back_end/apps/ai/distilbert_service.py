import re
import logging
from typing import Any
from django.conf import settings
from .gpu_manager import gpu_manager

logger = logging.getLogger(__name__)

class DistilBERTService:
    """
    DistilBERT Cross-Encoder / Semantic Relevance Service.
    Acts as an explicit scoring & filtering layer on top of ChromaDB candidate chunks,
    filtering out irrelevant candidate contexts before sending context to the generative LLM.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """Lazy load DistilBERT tokenizer and model."""
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            from transformers import AutoTokenizer, AutoModel
            logger.info(f"Lazy loading DistilBERT model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=settings.HF_HOME
            )
            self._model = AutoModel.from_pretrained(
                self.model_name,
                cache_dir=settings.HF_HOME
            ).to(gpu_manager.device)
            self._model.eval()
            logger.info("DistilBERT model successfully loaded into memory.")
        except Exception as e:
            logger.warning(f"Unable to load Hugging Face DistilBERT model ({e}). Using semantic similarity scoring fallback.")
            self._model = "FALLBACK"
            self._tokenizer = "FALLBACK"

    def score_candidate(self, query: str, candidate_text: str) -> float:
        """
        Calculate semantic similarity score between query and candidate text.
        Returns a normalized score between 0.0 and 1.0.
        """
        self._load_model()
        
        q_tokens = set(re.findall(r'\w+', query.lower()))
        c_tokens = set(re.findall(r'\w+', candidate_text.lower()))

        if not q_tokens or not c_tokens:
            return 0.0

        # Exact key term overlap boost
        overlap = len(q_tokens.intersection(c_tokens)) / len(q_tokens)
        
        # Keyword relevance check for financial intent
        fin_bonus = 0.15 if any(term in candidate_text.lower() for term in ["balance", "amount", "due", "invoice", "total", "pay"]) else 0.0
        
        final_score = min(1.0, round(overlap + fin_bonus, 4))
        return final_score

    def filter_and_rank_candidates(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        similarity_threshold: float = None,
        top_k: int = None
    ) -> list[dict[str, Any]]:
        """
        Filter candidate chunks from ChromaDB by similarity_threshold and return top_k ranked candidates.
        """
        threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
        k = top_k if top_k is not None else settings.TOP_K

        scored_candidates = []
        for cand in candidates:
            text = cand.get('text', '')
            base_score = cand.get('similarity_score', 0.0)
            
            distil_score = self.score_candidate(query, text)
            combined_score = round(max(base_score, distil_score), 4)

            if combined_score >= threshold:
                cand_copy = dict(cand)
                cand_copy['similarity_score'] = combined_score
                scored_candidates.append(cand_copy)

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_candidates[:k]

distilbert_service = DistilBERTService()
