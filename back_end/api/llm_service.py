import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"

class LocalLLMService:
    """Local LLM Service interfacing directly with Ollama Qwen3:4b with performance optimizations."""

    def __init__(self, model_name=DEFAULT_MODEL, host=OLLAMA_BASE_URL):
        self.model_name = model_name
        self.host = host

    def check_availability(self):
        """Check if Ollama server is running and qwen3:4b model is available."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                has_model = any(self.model_name in m or 'qwen' in m for m in models)
                return True, has_model, models
            return False, False, []
        except Exception:
            try:
                res = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get('name', '') for m in data.get('models', [])]
                    has_model = any(self.model_name in m or 'qwen' in m for m in models)
                    return True, has_model, models
            except Exception:
                pass
            return False, False, []

    def generate_response(self, prompt, context_snippets=None, model=None):
        """
        Generate response from local Qwen3:4b model via Ollama API with keep_alive & performance tuning.
        """
        target_model = model or self.model_name

        if context_snippets and len(context_snippets) > 0:
            formatted_context = "\n---\n".join(context_snippets)
            full_prompt = (
                f"You are a helpful AI assistant. Use the following reference context to answer the user's question:\n\n"
                f"CONTEXT FROM VECTOR DATABASE:\n{formatted_context}\n\n"
                f"USER QUESTION: {prompt}"
            )
        else:
            full_prompt = prompt

        # Attempt 1: Fast Ollama Python SDK with keep_alive (keeps model in memory) & performance options
        try:
            import ollama
            response = ollama.chat(
                model=target_model,
                messages=[{"role": "user", "content": full_prompt}],
                keep_alive="60m",  # Keep qwen3:4b in RAM/VRAM memory for 60 mins to eliminate reload latency
                options={
                    "num_ctx": 4096,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )
            content = response.get('message', {}).get('content', '')
            if content:
                return {
                    "success": True,
                    "reply": content,
                    "model": target_model,
                    "method": "ollama-python-sdk"
                }
        except Exception as sdk_err:
            logger.warning(f"Ollama SDK call failed: {sdk_err}, falling back to REST HTTP API")

        # Attempt 2: Direct HTTP request to Ollama REST API with keep_alive
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": False,
            "keep_alive": "60m",
            "options": {
                "num_ctx": 4096,
                "temperature": 0.7
            }
        }

        try:
            res = requests.post(
                f"{self.host}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=120
            )
            if res.status_code == 200:
                data = res.json()
                reply = data.get('message', {}).get('content', '')
                return {
                    "success": True,
                    "reply": reply,
                    "model": target_model,
                    "method": "ollama-http-rest"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama HTTP error {res.status_code}: {res.text}"
                }
        except Exception as http_err:
            return {
                "success": False,
                "error": f"Failed to connect to local Ollama server: {str(http_err)}"
            }

    def stream_response_chunks(self, prompt, context_snippets=None, model=None):
        """
        Yield streaming text chunks from Ollama for instant real-time response rendering.
        """
        target_model = model or self.model_name

        if context_snippets and len(context_snippets) > 0:
            formatted_context = "\n---\n".join(context_snippets)
            full_prompt = (
                f"You are a helpful AI assistant. Use the following reference context to answer the user's question:\n\n"
                f"CONTEXT FROM VECTOR DATABASE:\n{formatted_context}\n\n"
                f"USER QUESTION: {prompt}"
            )
        else:
            full_prompt = prompt

        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True,
            "keep_alive": "60m",
            "options": {
                "num_ctx": 4096,
                "temperature": 0.7
            }
        }

        try:
            res = requests.post(
                f"{self.host}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                stream=True,
                timeout=120
            )

            for line in res.iter_lines():
                if line:
                    chunk_data = json.loads(line.decode('utf-8'))
                    chunk_content = chunk_data.get('message', {}).get('content', '')
                    if chunk_content:
                        yield chunk_content
        except Exception as e:
            yield f"\n[Error streaming from Qwen3: {str(e)}]"

llm_service = LocalLLMService()
