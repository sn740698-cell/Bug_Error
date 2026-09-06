import json
import uuid
import logging
from pathlib import Path
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .llm_service import llm_service

logger = logging.getLogger(__name__)

# Initialize ChromaDB persistent vector database
CHROMA_DATA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
CHROMA_DATA_PATH.mkdir(parents=True, exist_ok=True)

try:
    import chromadb
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))
    collection = chroma_client.get_or_create_collection(name="local_knowledge_base")
    CHROMADB_AVAILABLE = True
except Exception as e:
    logger.error(f"Error initializing ChromaDB: {e}")
    chroma_client = None
    collection = None
    CHROMADB_AVAILABLE = False


@csrf_exempt
def health_check(request):
    """GET /api/health/ - Backend & local service health status."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    ollama_ok, qwen_ok, models = llm_service.check_availability()
    
    vector_count = 0
    if CHROMADB_AVAILABLE and collection is not None:
        try:
            vector_count = collection.count()
        except Exception:
            vector_count = 0

    return JsonResponse({
        'status': 'online',
        'backend': 'django',
        'ollama_connected': ollama_ok,
        'qwen3_available': qwen_ok,
        'target_model': 'qwen3:4b',
        'available_models': models if isinstance(models, list) else [],
        'vectordb_active': CHROMADB_AVAILABLE,
        'vectordb_type': 'ChromaDB',
        'indexed_documents_count': vector_count
    })


@csrf_exempt
def chat_api(request):
    """POST /api/chat/ - Query Qwen3:4b LLM with optional VectorDB RAG context."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        user_prompt = data.get('prompt', '').strip()
        use_rag = data.get('use_rag', False)
        model_name = data.get('model', 'qwen3:4b')

        if not user_prompt:
            return JsonResponse({'error': 'Prompt cannot be empty'}, status=400)

        context_snippets = []
        if use_rag and CHROMADB_AVAILABLE and collection is not None:
            try:
                doc_count = collection.count()
                if doc_count > 0:
                    results = collection.query(
                        query_texts=[user_prompt],
                        n_results=min(3, doc_count)
                    )
                    if results and 'documents' in results and results['documents']:
                        docs = results['documents'][0]
                        for idx, doc in enumerate(docs):
                            context_snippets.append(f"Snippet {idx+1}: {doc}")
            except Exception as e:
                logger.warning(f"RAG search error: {e}")

        # Call Local LLM Service (Qwen3:4b with keep_alive memory optimization)
        res = llm_service.generate_response(
            prompt=user_prompt,
            context_snippets=context_snippets if use_rag else None,
            model=model_name
        )

        if res.get('success'):
            return JsonResponse({
                'reply': res.get('reply'),
                'model': res.get('model'),
                'used_rag': bool(context_snippets and use_rag),
                'context_snippets': context_snippets
            })
        else:
            return JsonResponse({'error': res.get('error')}, status=500)

    except Exception as e:
        return JsonResponse({'error': f"Invalid request format: {str(e)}"}, status=400)


@csrf_exempt
def chat_stream_api(request):
    """POST /api/chat/stream/ - Streaming real-time response endpoint for fast token rendering."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        user_prompt = data.get('prompt', '').strip()
        use_rag = data.get('use_rag', False)
        model_name = data.get('model', 'qwen3:4b')

        if not user_prompt:
            return JsonResponse({'error': 'Prompt cannot be empty'}, status=400)

        context_snippets = []
        if use_rag and CHROMADB_AVAILABLE and collection is not None:
            try:
                doc_count = collection.count()
                if doc_count > 0:
                    results = collection.query(
                        query_texts=[user_prompt],
                        n_results=min(3, doc_count)
                    )
                    if results and 'documents' in results and results['documents']:
                        docs = results['documents'][0]
                        for idx, doc in enumerate(docs):
                            context_snippets.append(f"Snippet {idx+1}: {doc}")
            except Exception as e:
                logger.warning(f"RAG search error: {e}")

        def stream_generator():
            # First send JSON metadata chunk
            meta = {
                "type": "meta",
                "used_rag": bool(context_snippets and use_rag),
                "snippets": context_snippets
            }
            yield f"data: {json.dumps(meta)}\n\n"

            # Stream tokens
            for token in llm_service.stream_response_chunks(
                prompt=user_prompt,
                context_snippets=context_snippets if use_rag else None,
                model=model_name
            ):
                chunk_obj = {"type": "content", "token": token}
                yield f"data: {json.dumps(chunk_obj)}\n\n"

            yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except Exception as e:
        return JsonResponse({'error': f"Streaming request failed: {str(e)}"}, status=400)


@csrf_exempt
def vector_add_api(request):
    """POST /api/vector/add/ - Add text document into ChromaDB vector database."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not CHROMADB_AVAILABLE or collection is None:
        return JsonResponse({'error': 'Vector database (ChromaDB) is not available'}, status=503)

    try:
        data = json.loads(request.body.decode('utf-8'))
        text = data.get('text', '').strip()
        title = data.get('title', 'Document')

        if not text:
            return JsonResponse({'error': 'Document text cannot be empty'}, status=400)

        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        collection.add(
            documents=[text],
            metadatas=[{"title": title, "length": len(text)}],
            ids=[doc_id]
        )

        return JsonResponse({
            'success': True,
            'id': doc_id,
            'title': title,
            'message': 'Document successfully added to ChromaDB vector store',
            'total_count': collection.count()
        })
    except Exception as e:
        return JsonResponse({'error': f"Failed to store document in ChromaDB: {str(e)}"}, status=500)


@csrf_exempt
def vector_search_api(request):
    """POST /api/vector/search/ - Search vector database for matching snippets."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not CHROMADB_AVAILABLE or collection is None:
        return JsonResponse({'error': 'Vector database (ChromaDB) is not available'}, status=503)

    try:
        data = json.loads(request.body.decode('utf-8'))
        query = data.get('query', '').strip()
        top_k = int(data.get('top_k', 3))

        if not query:
            return JsonResponse({'error': 'Query string cannot be empty'}, status=400)

        if collection.count() == 0:
            return JsonResponse({'query': query, 'matches': [], 'message': 'Vector DB is currently empty.'})

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count())
        )

        matches = []
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            ids = results['ids'][0] if 'ids' in results else []
            metas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else []
            distances = results['distances'][0] if 'distances' in results and results['distances'] else []

            for i in range(len(docs)):
                matches.append({
                    'id': ids[i] if i < len(ids) else f"doc_{i}",
                    'text': docs[i],
                    'metadata': metas[i] if i < len(metas) else {},
                    'distance': distances[i] if i < len(distances) else None
                })

        return JsonResponse({
            'query': query,
            'matches': matches,
            'total_indexed': collection.count()
        })
    except Exception as e:
        return JsonResponse({'error': f"Search failed: {str(e)}"}, status=500)


@csrf_exempt
def vector_documents_api(request):
    """GET /api/vector/documents/ - Retrieve list of indexed knowledge items."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not CHROMADB_AVAILABLE or collection is None:
        return JsonResponse({'error': 'Vector DB not available'}, status=503)

    try:
        items = collection.get()
        documents = []
        if items and 'ids' in items:
            ids = items.get('ids', [])
            docs = items.get('documents', [])
            metas = items.get('metadatas', [])

            for i in range(len(ids)):
                documents.append({
                    'id': ids[i],
                    'text': docs[i] if i < len(docs) else '',
                    'metadata': metas[i] if metas and i < len(metas) else {}
                })

        return JsonResponse({
            'documents': documents,
            'count': len(documents)
        })
    except Exception as e:
        return JsonResponse({'error': f"Failed to retrieve documents: {str(e)}"}, status=500)
