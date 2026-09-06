import threading
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Workflow, FinancialInsight, GeneratedDraft
from .serializers import WorkflowSerializer, FinancialInsightSerializer, GeneratedDraftSerializer
from apps.documents.models import Document
from .tasks import execute_langgraph_workflow, run_langgraph_workflow_task

logger = logging.getLogger(__name__)

class WorkflowAnalyzeView(APIView):
    """
    POST /api/workflows/analyze/
    Initiates multi-supervisor LangGraph analysis workflow for an uploaded document.
    """
    def post(self, request, *args, **kwargs):
        document_id = request.data.get('document_id')
        if not document_id:
            return Response({'error': 'document_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({'error': f'Document {document_id} not found'}, status=status.HTTP_404_NOT_FOUND)

        workflow = Workflow.objects.create(
            user=request.user if request.user.is_authenticated else None,
            document=document,
            status='PENDING'
        )

        # Trigger background execution in thread for instant REST response
        t = threading.Thread(target=execute_langgraph_workflow, args=(str(workflow.id),))
        t.daemon = True
        t.start()

        return Response({
            'message': 'Workflow analysis initiated',
            'workflow_id': str(workflow.id),
            'status': workflow.status
        }, status=status.HTTP_202_ACCEPTED)


class WorkflowStatusView(APIView):
    """
    GET /api/workflows/{workflow_id}/
    Returns current status, progress %, active supervisor, and active agent.
    """
    def get(self, request, workflow_id, *args, **kwargs):
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            serializer = WorkflowSerializer(workflow)
            return Response(serializer.data)
        except Workflow.DoesNotExist:
            return Response({'error': f'Workflow {workflow_id} not found'}, status=status.HTTP_404_NOT_FOUND)


class WorkflowInsightsView(APIView):
    """
    GET /api/workflows/{workflow_id}/insights/
    Returns extracted structured financial insights.
    """
    def get(self, request, workflow_id, *args, **kwargs):
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            insights = FinancialInsight.objects.filter(workflow=workflow)
            serializer = FinancialInsightSerializer(insights, many=True)
            return Response({
                'workflow_id': str(workflow.id),
                'insights': serializer.data,
                'count': insights.count()
            })
        except Workflow.DoesNotExist:
            return Response({'error': f'Workflow {workflow_id} not found'}, status=status.HTTP_404_NOT_FOUND)


class WorkflowDraftView(APIView):
    """
    GET /api/workflows/{workflow_id}/draft/
    Returns validated balance-due notification draft.
    """
    def get(self, request, workflow_id, *args, **kwargs):
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            draft = GeneratedDraft.objects.filter(workflow=workflow).order_by('-created_at').first()
            if not draft:
                return Response({'message': 'No draft generated yet', 'workflow_id': str(workflow.id)}, status=status.HTTP_404_NOT_FOUND)

            serializer = GeneratedDraftSerializer(draft)
            return Response({
                'workflow_id': str(workflow.id),
                'draft': serializer.data
            })
        except Workflow.DoesNotExist:
            return Response({'error': f'Workflow {workflow_id} not found'}, status=status.HTTP_404_NOT_FOUND)


class WorkflowRegenerateView(APIView):
    """
    POST /api/workflows/{workflow_id}/regenerate/
    Forces regeneration of the balance-due notification draft.
    """
    def post(self, request, workflow_id, *args, **kwargs):
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            workflow.status = 'PENDING'
            workflow.save()

            # Trigger background execution in thread for instant REST response
            t = threading.Thread(target=execute_langgraph_workflow, args=(str(workflow.id),))
            t.daemon = True
            t.start()

            return Response({
                'message': 'Regeneration initiated',
                'workflow_id': str(workflow.id),
                'status': 'PENDING'
            }, status=status.HTTP_202_ACCEPTED)
        except Workflow.DoesNotExist:
            return Response({'error': f'Workflow {workflow_id} not found'}, status=status.HTTP_404_NOT_FOUND)


class WorkflowChatView(APIView):
    """
    POST /api/workflows/{workflow_id}/chat/
    Interactive RAG Chatbot Endpoint. Answers questions about the document
    using ChromaDB vector retrieval, extracted facts, and local LLMRouter.
    """
    def post(self, request, workflow_id, *args, **kwargs):
        question = request.data.get('question')
        if not question:
            return Response({'error': 'question parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fast path for simple conversational greetings
        clean_q = question.strip().lower()
        if clean_q in ["hi", "hello", "hey", "hi buddy", "hey buddy", "hi jarvis", "hello jarvis", "hi there", "sup"]:
            return Response({
                'workflow_id': workflow_id,
                'question': question,
                'answer': "Hello! I am J.A.R.V.I.S., your autonomous AI assistant. How may I assist you today?",
                'llm_model': 'llama',
                'hallucination_verified': True,
                'sources': []
            })

        workflow = None
        doc_id = None
        context_text = "No document attached."
        facts_summary = "None"
        sections_text = "None"
        simplified_summary = "None"
        selected_llm = "llama"

        if workflow_id and workflow_id != 'general':
            try:
                workflow = Workflow.objects.get(id=workflow_id)
                doc_id = str(workflow.document.id)
                selected_llm = workflow.selected_llm or "llama"
                simplified_summary = workflow.simplified_summary or "None"

                from apps.vectorstore.retrieval import vector_retrieval_service
                retrieved_chunks = vector_retrieval_service.retrieve_financial_context(
                    query=question,
                    filter_metadata={"document_id": doc_id},
                    top_k=5,
                    threshold=0.10
                )
                if retrieved_chunks:
                    context_text = "\n\n".join([chk["text"] for chk in retrieved_chunks])
                else:
                    context_text = "Refer to extracted facts."

                insights = FinancialInsight.objects.filter(workflow=workflow)
                if insights.exists():
                    facts_summary = "\n".join([f"- {ins.field_name}: {ins.field_value}" for ins in insights if ins.field_value is not None])
                else:
                    facts_summary = "None"

                if workflow.document_sections and isinstance(workflow.document_sections, dict):
                    sections_text = "\n".join([f"[{sec.upper()}]: {val}" for sec, val in workflow.document_sections.items() if val])

            except (Workflow.DoesNotExist, Exception) as e:
                logger.info(f"WorkflowChatView: General prompt mode for workflow_id='{workflow_id}'. Error: {e}")
                retrieved_chunks = []
        else:
            retrieved_chunks = []

        from apps.ai.llm_router import llm_router

        # 3. Construct J.A.R.V.I.S. All-Capable System Prompt
        system_prompt = (
            "You are J.A.R.V.I.S., an advanced autonomous AI assistant equipped with deep multi-agent intelligence, "
            "general knowledge, real-world problem solving, science, technology, coding, and document analysis capabilities.\n"
            "Instructions:\n"
            "1. Answer the question accurately, clearly, and directly.\n"
            "2. If document context or extracted facts are provided, answer using those exact factual figures and information.\n"
            "3. If no document context is provided, use your general knowledge to provide a helpful, accurate, and detailed answer.\n"
            "4. Never refuse to answer general queries or claim you are restricted to reading documents.\n"
            "5. Be sharp, intelligent, professional, and concise."
        )

        if workflow:
            user_prompt = (
                f"EXTRACTED DOCUMENT FACTS:\n{facts_summary}\n\n"
                f"DOCUMENT CONTEXT:\n{context_text}\n\n"
                f"USER QUESTION: {question}\n\n"
                f"Answer:"
            )
        else:
            user_prompt = (
                f"USER QUESTION: {question}\n\n"
                f"Answer:"
            )

        # 4. Generate response using LLMRouter (Llama 3.2 1B Primary GGUF)
        res = llm_router.generate(
            model=selected_llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        raw_answer = res.get("reply", "I am J.A.R.V.I.S. How may I assist you further?").strip()

        # 5. Anti-Hallucination Audit Guardrail
        if workflow:
            from apps.workflows.agents.hallucination_audit_agent import hallucination_audit_agent
            audit_res = hallucination_audit_agent.audit_response(
                response_text=raw_answer,
                context_text=context_text,
                insights=list(insights)
            )
            final_answer = audit_res.get("answer", raw_answer)
            hallucination_verified = audit_res.get('hallucination_verified', True)
        else:
            final_answer = raw_answer
            hallucination_verified = True

        return Response({
            'workflow_id': workflow_id,
            'question': question,
            'answer': final_answer,
            'llm_model': res.get('selected_llm', 'llama'),
            'hallucination_verified': hallucination_verified,
            'sources': [chk['chunk_id'] for chk in retrieved_chunks] if retrieved_chunks else []
        })
