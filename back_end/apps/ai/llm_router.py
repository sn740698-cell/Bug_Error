import logging
from django.conf import settings
from .ollama_service import ollama_service

logger = logging.getLogger(__name__)

class LLMRouter:
    """
    LLM Router delegating requests to Qwen 2.5 1B or Llama 3.2 1B GGUF models via Ollama.
    Implements model selection strategy with explicit fallback tracking.
    """

    def __init__(self):
        self.qwen_model = settings.OLLAMA_QWEN_MODEL
        self.llama_model = settings.OLLAMA_LLAMA_MODEL
        self.default_llm = settings.DEFAULT_LLM.lower()

    def get_model_name(self, model_key: str) -> str:
        """Resolve short key ('qwen' or 'llama') to full Ollama model name. Defaults to Llama 3.2 1B."""
        if model_key and 'qwen' in model_key.lower():
            return self.qwen_model
        return self.llama_model

    def generate(self, model: str = None, system_prompt: str = "", user_prompt: str = "") -> dict:
        """
        Execute generation with primary model and automatic fallback to secondary model if primary fails.
        """
        primary_key = (model or self.default_llm).lower()
        primary_model = self.get_model_name(primary_key)

        # Secondary fallback model
        if 'llama' in primary_key:
            fallback_key = 'qwen'
            fallback_model = self.qwen_model
        else:
            fallback_key = 'llama'
            fallback_model = self.llama_model

        logger.info(f"LLM Router: Attempting primary model execution ({primary_key} -> {primary_model})")

        # Attempt 1: Primary Model
        res = ollama_service.generate_chat(primary_model, system_prompt, user_prompt)
        if res.get('success'):
            return {
                "success": True,
                "reply": res.get('reply'),
                "selected_llm": primary_model,
                "model_key": primary_key,
                "fallback_used": False,
                "failure_reason": None
            }

        # Primary failed, log and attempt fallback
        primary_error = res.get('error', 'Primary model execution failed')
        logger.warning(f"Primary LLM ({primary_model}) failed: {primary_error}. Attempting fallback to {fallback_model}.")

        # Attempt 2: Fallback Model
        fallback_res = ollama_service.generate_chat(fallback_model, system_prompt, user_prompt)
        if fallback_res.get('success'):
            return {
                "success": True,
                "reply": fallback_res.get('reply'),
                "selected_llm": fallback_model,
                "model_key": fallback_key,
                "fallback_used": True,
                "failure_reason": f"Primary model ({primary_model}) error: {primary_error}"
            }

        # Both failed: Return controlled workflow failure
        final_error = f"Both primary ({primary_model}) and fallback ({fallback_model}) LLMs failed. Last error: {fallback_res.get('error')}"
        logger.error(final_error)
        return {
            "success": False,
            "error": final_error,
            "selected_llm": None,
            "fallback_used": True,
            "failure_reason": final_error
        }

llm_router = LLMRouter()
