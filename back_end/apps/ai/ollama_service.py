import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """
    Ollama Service layer.
    The ONLY component in the backend that directly communicates with Ollama API.
    Interfaces with local GGUF models: Llama 3.2 1B and Qwen 2.5 1B.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.llama_model = settings.OLLAMA_LLAMA_MODEL
        self.qwen_model = settings.OLLAMA_QWEN_MODEL

    def list_models(self) -> list[str]:
        """Fetch list of available models from local Ollama instance."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if res.status_code == 200:
                data = res.json()
                return [m.get('name', '') for m in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available in Ollama."""
        models = self.list_models()
        return any(model_name in m or m in model_name for m in models)

    def _clean_output(self, text: str) -> str:
        """Strip raw ChatML/template tokens and system artifact prefixes from LLM reply."""
        if not text:
            return ""
        import re
        cleaned = re.sub(r'<\|[a-zA-Z0-9_=":\-\s/]+\|>', '', text)
        cleaned = re.sub(r'^(J\.A\.R\.V\.I\.S\.\s*Answer:|J\.A\.R\.V\.I\.S\.|Answer:)\s*', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def generate_chat(self, model_name: str, system_prompt: str, user_prompt: str) -> dict:
        """
        Generate chat completion from specified Ollama model with keep_alive memory persistence
        and optimized inference parameters for maximum generation speed.
        """
        options = {
            "num_ctx": 2048,
            "num_predict": 384,
            "temperature": 0.3,
            "top_p": 0.9,
            "stop": ["<|eot_id|>", "<|im_end|>", "User:", "Question:"]
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "keep_alive": "60m",
            "options": options
        }

        # Try official python `ollama` SDK first
        try:
            import ollama
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                keep_alive="60m",
                options=options
            )
            content = response.get('message', {}).get('content', '')
            if content:
                return {
                    "success": True,
                    "reply": self._clean_output(content),
                    "model": model_name,
                    "method": "ollama-sdk"
                }
        except Exception as sdk_err:
            logger.warning(f"Ollama SDK call failed ({sdk_err}), attempting direct REST API call.")

        # Fallback to direct HTTP REST call
        try:
            res = requests.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                content = data.get('message', {}).get('content', '')
                return {
                    "success": True,
                    "reply": self._clean_output(content),
                    "model": model_name,
                    "method": "ollama-http"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama HTTP error {res.status_code}: {res.text}"
                }
        except Exception as http_err:
            return {
                "success": False,
                "error": f"Failed to connect to local Ollama instance at {self.base_url}: {str(http_err)}"
            }

ollama_service = OllamaService()
