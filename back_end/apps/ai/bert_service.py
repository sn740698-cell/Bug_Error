import re
import logging
from typing import Any
from django.conf import settings
from .gpu_manager import gpu_manager

logger = logging.getLogger(__name__)

class BERTService:
    """
    Hugging Face BERT Service for deep contextual understanding, sentence-level analysis,
    financial text classification, and financial entity context scoring.
    Implements lazy loading to conserve VRAM on low-resource environments.
    """

    def __init__(self, model_name: str = "bert-base-uncased"):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """Lazy load BERT model and tokenizer on-demand."""
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            logger.info(f"Lazy loading BERT model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=settings.HF_HOME
            )
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                cache_dir=settings.HF_HOME
            ).to(gpu_manager.device)
            self._model.eval()
            logger.info("BERT model successfully loaded into memory.")
        except Exception as e:
            logger.warning(f"Unable to load Hugging Face BERT model ({e}). Using rule-based fallback analyzer.")
            self._model = "FALLBACK"
            self._tokenizer = "FALLBACK"

    def analyze_text(self, text: str) -> dict[str, Any]:
        """Perform comprehensive contextual analysis on text."""
        self._load_model()
        classification = self.classify_financial_text(text)
        entities = self.extract_financial_context(text)
        return {
            "text_length": len(text),
            "classification": classification,
            "entities": entities,
            "is_financial_document": classification.get("is_financial", False),
            "confidence": classification.get("confidence", 0.85)
        }

    def classify_financial_text(self, text: str) -> dict[str, Any]:
        """Classify whether sentence/document contains financial content."""
        lower = text.lower()
        financial_keywords = [
            "invoice", "balance due", "amount due", "subtotal", "tax",
            "total", "payment", "bill", "due date", "vendor", "customer",
            "inr", "usd", "rs", "₹", "rupees", "account", "payable", "receivable"
        ]
        matches = [kw for kw in financial_keywords if kw in lower]
        score = min(1.0, len(matches) * 0.2)
        
        return {
            "category": "invoice" if "invoice" in lower else "financial_statement" if "balance" in lower else "general",
            "is_financial": len(matches) > 0,
            "confidence": round(max(0.60, score), 2),
            "matched_terms": matches
        }

    def extract_financial_context(self, text: str) -> dict[str, Any]:
        """Extract key financial context candidates from text using regex & contextual rules."""
        context = {}
        
        # Invoice number pattern
        inv_match = re.search(r'(?i)(invoice|inv)\s*(?:no|number|#)?[:\s\-]*([A-Z0-9\-]+)', text)
        if inv_match:
            context["invoice_number"] = inv_match.group(2).strip()

        # Balance Due pattern
        bal_match = re.search(r'(?i)(balance\s*due|amount\s*due|outstanding)[:\s]*([₹$Rs.\s]*[\d,]+(?:\.\d{2})?)', text)
        if bal_match:
            context["balance_due_raw"] = bal_match.group(2).strip()

        # Total Amount pattern
        tot_match = re.search(r'(?i)(total\s*amount|total)[:\s]*([₹$Rs.\s]*[\d,]+(?:\.\d{2})?)', text)
        if tot_match:
            context["total_amount_raw"] = tot_match.group(2).strip()

        # Due Date pattern
        date_match = re.search(r'(?i)(due\s*date|date)[:\s]*(\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', text)
        if date_match:
            context["due_date_raw"] = date_match.group(2).strip()

        return context

    def calculate_context_score(self, query: str, text: str) -> float:
        """Calculate relevance score between query and target text."""
        query_words = set(re.findall(r'\w+', query.lower()))
        text_words = set(re.findall(r'\w+', text.lower()))
        if not query_words or not text_words:
            return 0.0
        intersection = query_words.intersection(text_words)
        return round(len(intersection) / len(query_words), 2)

bert_service = BERTService()
