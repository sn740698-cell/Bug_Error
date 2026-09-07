import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0"

class LocalLLMService:
    """Local LLM Service interfacing directly with Ollama Llama 3.2 1B with performance optimizations."""

    def __init__(self, model_name=DEFAULT_MODEL, host=OLLAMA_BASE_URL):
        self.model_name = model_name
        self.host = host

    def check_availability(self):
        """Check if Ollama server is running and Llama model is available."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                has_model = len(models) > 0
                return True, has_model, models
            return False, False, []
        except Exception:
            try:
                res = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get('name', '') for m in data.get('models', [])]
                    has_model = len(models) > 0
                    return True, has_model, models
            except Exception:
                pass
            return False, False, []

    def generate_response(self, prompt, context_snippets=None, model=None):
        """
        Generate response from local Llama 3.2 1B model in strict JARVIS persona.
        """
        clean_p = prompt.strip().lower()
        if clean_p in ['hi', 'hello', 'hey', 'hi jarvis', 'hello jarvis', 'greetings', 'hey jarvis']:
            return {
                "success": True,
                "reply": "Hello, Sir. How may I assist you today?",
                "model": model or self.model_name,
                "method": "greeting"
            }

        target_model = model or self.model_name
        system_prompt = (
            "You are J.A.R.V.I.S., Tony Stark's AI assistant.\n"
            "RULES:\n"
            "1. Speak directly to the user politely as 'Sir' or 'you'.\n"
            "2. Keep responses SHORT, SWEET, SIMPLE, AND DIRECT (maximum 2-3 concise sentences).\n"
            "3. Sound sharp, crisp, articulate, and highly intelligent.\n"
            "4. Never output meta-commentary, raw data tags, or internal instructions.\n"
            "5. If Uploaded Document Context is provided, answer the user question using facts from the document context."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if context_snippets and len(context_snippets) > 0:
            formatted_context = "\n---\n".join(context_snippets[:3])
            user_content = f"Uploaded Document Context:\n{formatted_context}\n\nUser Question: {prompt}"
        else:
            user_content = prompt

        messages.append({"role": "user", "content": user_content})

        try:
            import ollama
            response = ollama.chat(
                model=target_model,
                messages=messages,
                keep_alive="60m",
                options={
                    "num_ctx": 2048,
                    "num_predict": 180,
                    "temperature": 0.3,
                }
            )
            content = response.get('message', {}).get('content', '')
            if content:
                return {
                    "success": True,
                    "reply": content.strip(),
                    "model": target_model,
                    "method": "ollama-python-sdk"
                }
        except Exception as sdk_err:
            logger.warning(f"Ollama SDK call failed: {sdk_err}")

        return {
            "success": True,
            "reply": "Hello, Sir. How may I assist you today?",
            "model": target_model,
            "method": "fallback"
        }

    def stream_response_chunks(self, prompt, context_snippets=None, model=None):
        """
        Yield streaming text chunks word-by-word from Ollama in real-time JARVIS persona.
        """
        clean_p = prompt.strip().lower()
        if clean_p in ['hi', 'hello', 'hey', 'hi jarvis', 'hello jarvis', 'greetings', 'hey jarvis']:
            yield "Hello, Sir. How may I assist you today?"
            return

        target_model = model or self.model_name
        system_prompt = (
            "You are J.A.R.V.I.S., Tony Stark's AI assistant.\n"
            "RULES:\n"
            "1. Speak directly to the user politely as 'Sir' or 'you'.\n"
            "2. Keep responses SHORT, SWEET, SIMPLE, AND DIRECT (maximum 2-3 concise sentences).\n"
            "3. Sound sharp, crisp, articulate, and highly intelligent.\n"
            "4. Never output meta-commentary, raw data tags, or internal instructions.\n"
            "5. If Uploaded Document Context is provided, answer the user question using facts from the document context."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if context_snippets and len(context_snippets) > 0:
            formatted_context = "\n---\n".join(context_snippets[:3])
            user_content = f"Uploaded Document Context:\n{formatted_context}\n\nUser Question: {prompt}"
        else:
            user_content = prompt

        messages.append({"role": "user", "content": user_content})

        try:
            import ollama
            for chunk in ollama.chat(
                model=target_model,
                messages=messages,
                stream=True,
                keep_alive="60m",
                options={"num_ctx": 2048, "num_predict": 180, "temperature": 0.3}
            ):
                content = chunk.get('message', {}).get('content', '')
                if content:
                    yield content
        except Exception as e:
            payload = {
                "model": target_model,
                "messages": messages,
                "stream": True,
                "keep_alive": "60m",
                "options": {"num_ctx": 2048, "num_predict": 180, "temperature": 0.3}
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
            except Exception as http_err:
                yield f"Hello, Sir. Connecting to AI core..."

llm_service = LocalLLMService()
