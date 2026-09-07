import json
import uuid
import logging
from pathlib import Path
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from api.models import UserProfile, IngestedDocument, AgentExecutionLog
from api.serializers import PipelineRunSerializer, UserProfileSerializer, IngestedDocumentSerializer, AgentExecutionLogSerializer
from api.services.execution import PipelineExecutionService
from api.services.user_service import UserService
from api.services.vectorstore import ChromaVectorStoreService, CHROMADB_AVAILABLE
from .llm_service import llm_service

logger = logging.getLogger(__name__)


@csrf_exempt
def pipeline_run_api(request):
    """
    POST /api/pipeline/run/
    Primary API endpoint accepting multipart/form-data:
    - name: User name
    - email: User unique email
    - section: Section/Department
    - query: User query text
    - files: Uploaded documents (PDF, DOCX, DOC, CSV, TXT)
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'code': 'METHOD_NOT_ALLOWED', 'message': 'Method not allowed'}, status=405)

    try:
        # Support multipart/form-data as well as JSON request formats
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            section = request.POST.get('section', '').strip()
            query = request.POST.get('query', '').strip()
            files_list = request.FILES.getlist('files') or request.FILES.getlist('files[]')
        else:
            try:
                body = json.loads(request.body.decode('utf-8'))
            except Exception:
                body = {}
            name = body.get('name', '').strip()
            email = body.get('email', '').strip()
            section = body.get('section', '').strip()
            query = body.get('query', '').strip()
            files_list = []

        payload = {
            'name': name,
            'email': email,
            'section': section,
            'query': query,
            'files': files_list
        }

        serializer = PipelineRunSerializer(data=payload)
        if not serializer.is_valid():
            return JsonResponse({
                'status': 'error',
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid request parameters.',
                'details': serializer.errors
            }, status=400)

        validated = serializer.validated_data
        
        # Format files into tuples of (filename, bytes)
        raw_files = []
        for f in validated.get('files', []):
            f.seek(0)
            raw_files.append((f.name, f.read()))

        execution_service = PipelineExecutionService()
        result = execution_service.run_pipeline(
            name=validated['name'],
            email=validated['email'],
            query=validated['query'],
            section=validated.get('section', ''),
            files=raw_files
        )

        status_code = 200 if result.get('status') == 'success' else 500
        return JsonResponse(result, status=status_code)

    except Exception as e:
        logger.error(f"Unhandled error in pipeline_run_api: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'code': 'INTERNAL_SERVER_ERROR',
            'message': f"An unexpected server error occurred: {str(e)}"
        }, status=500)


@csrf_exempt
def user_profile_api(request):
    """GET /api/users/profile/?email=user@example.com"""
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email parameter is required'}, status=400)

    try:
        user = UserProfile.objects.get(email=email.lower())
        serializer = UserProfileSerializer(user)
        return JsonResponse({'status': 'success', 'user': serializer.data})
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found'}, status=404)


@csrf_exempt
def user_documents_api(request):
    """GET /api/documents/list/?email=user@example.com"""
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email parameter is required'}, status=400)

    try:
        user = UserProfile.objects.get(email=email.lower())
        documents = IngestedDocument.objects.filter(user=user)
        serializer = IngestedDocumentSerializer(documents, many=True)
        return JsonResponse({'status': 'success', 'documents': serializer.data})
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'success', 'documents': []})


@csrf_exempt
def user_executions_api(request):
    """GET /api/executions/list/?email=user@example.com"""
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email parameter is required'}, status=400)

    try:
        user = UserProfile.objects.get(email=email.lower())
        logs = AgentExecutionLog.objects.filter(user=user)
        serializer = AgentExecutionLogSerializer(logs, many=True)
        return JsonResponse({'status': 'success', 'executions': serializer.data})
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'success', 'executions': []})


@csrf_exempt
def health_check(request):
    """GET /api/health/ - Full system and multi-agent backend health status."""
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    ollama_ok, qwen_ok, models = llm_service.check_availability()
    
    vector_service = ChromaVectorStoreService()
    vector_count = 0
    if CHROMADB_AVAILABLE and vector_service.collection is not None:
        try:
            vector_count = vector_service.collection.count()
        except Exception:
            vector_count = 0

    return JsonResponse({
        'status': 'healthy',
        'backend': 'Django REST Framework 5.x',
        'vectorstore': {
            'type': 'ChromaDB',
            'available': CHROMADB_AVAILABLE,
            'collection': vector_service.collection_name,
            'total_indexed_chunks': vector_count
        },
        'llm_providers': {
            'embedding_provider': getattr(settings, 'EMBEDDING_PROVIDER', 'ollama'),
            'llm_a_provider': getattr(settings, 'LLM_A_PROVIDER', 'ollama'),
            'llm_a_model': getattr(settings, 'LLM_A_MODEL', getattr(settings, 'OLLAMA_LLAMA_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')),
            'llm_b_provider': getattr(settings, 'LLM_B_PROVIDER', 'ollama'),
            'llm_b_model': getattr(settings, 'LLM_B_MODEL', getattr(settings, 'OLLAMA_QWEN_MODEL', 'hf.co/nulledinstance/Qwen2.5-1B-Instruct-Q8_0-GGUF:Q8_0')),
            'evaluator_provider': getattr(settings, 'EVALUATOR_PROVIDER', 'ollama'),
            'evaluator_model': getattr(settings, 'EVALUATOR_MODEL', getattr(settings, 'OLLAMA_LLAMA_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0')),
            'ollama_connected': ollama_ok,
            'ollama_models': models if isinstance(models, list) else [],
            'ollama_url': getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        },
        'orchestrator': 'LangGraph 8-Agent StateGraph with parallel fan-in & feedback loop',
        'max_retries': getattr(settings, 'MAX_RETRIES', 2)
    })


# Interactive Streaming Chat API Endpoint
@csrf_exempt
def chat_api(request):
    """POST /api/chat/ - Real-time word-by-word streaming AI chat endpoint in JARVIS persona."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        prompt = data.get('prompt', '').strip()
        email = data.get('email', 'anonymous@example.com')

        if not prompt:
            return JsonResponse({'error': 'Prompt cannot be empty'}, status=400)

        # Retrieve RAG context snippets from ChromaDB vector store if documents exist
        name = data.get('name', 'User')
        user = UserService.get_or_create_user(email=email, name=name)
        user_id = str(user.id)

        vector_service = ChromaVectorStoreService()
        context_snippets = []
        try:
            chunks = vector_service.search(user_id=user_id, query=prompt, top_k=3)
            context_snippets = [c['content'] for c in chunks if c.get('content')]
            if context_snippets:
                logger.info(f"Retrieved {len(context_snippets)} document context chunks for chat query from user_id={user_id}")
        except Exception as e:
            logger.error(f"RAG search error in chat_api: {e}")

        # Stream text chunks word-by-word in real time
        return StreamingHttpResponse(
            llm_service.stream_response_chunks(prompt=prompt, context_snippets=context_snippets),
            content_type='text/plain; charset=utf-8'
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
