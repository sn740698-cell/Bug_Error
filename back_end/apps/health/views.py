from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.ai.gpu_manager import gpu_manager
from apps.ai.ollama_service import ollama_service
from apps.vectorstore.chroma_service import chroma_service

class HealthCheckView(APIView):
    """
    GET /api/health/
    System Health Check endpoint reporting status of Django API, Ollama LLMs, ChromaDB, and GPU/VRAM.
    """
    def get(self, request, *args, **kwargs):
        vram_info = gpu_manager.get_vram_usage()
        ollama_models = ollama_service.list_models()
        ollama_connected = len(ollama_models) > 0 or ollama_service.is_model_available(ollama_service.qwen_model)

        chroma_count = chroma_service.get_count()

        return Response({
            'status': 'healthy',
            'backend': 'Django REST Framework',
            'ollama': {
                'connected': ollama_connected,
                'qwen_model': ollama_service.qwen_model,
                'llama_model': ollama_service.llama_model,
                'available_models': ollama_models
            },
            'vectorstore': {
                'type': 'ChromaDB',
                'indexed_chunks': chroma_count,
                'persist_dir': str(chroma_service.persist_dir)
            },
            'gpu': vram_info
        }, status=status.HTTP_200_OK)
