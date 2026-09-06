from django.test import TestCase
from apps.ai.llm_router import llm_router
from apps.ai.ollama_service import ollama_service

class OllamaRouterTestCase(TestCase):
    def test_model_name_resolution(self):
        self.assertIn("Llama", llm_router.get_model_name("llama"))
        self.assertIn("Qwen", llm_router.get_model_name("qwen"))

    def test_ollama_service_instance(self):
        self.assertIsNotNone(ollama_service.base_url)
