import time
import logging
from typing import List, Dict, Any, Tuple, Optional

from django.conf import settings
from api.models import UserProfile, AgentExecutionLog
from api.services.user_service import UserService
from api.services.ingestion import DocumentIngestionService
from api.agents.graph import create_agent_graph

logger = logging.getLogger(__name__)


class PipelineExecutionService:
    def __init__(self):
        self.ingestion_service = DocumentIngestionService()
        self.graph = create_agent_graph()

    def run_pipeline(
        self,
        name: str,
        email: str,
        query: str,
        section: str = "",
        files: Optional[List[Tuple[str, bytes]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the full Multi-Agent RAG pipeline:
        1. Resolve/create UserProfile
        2. Ingest & index uploaded files into ChromaDB with user_id metadata
        3. Invoke 8-agent LangGraph workflow
        4. Record AgentExecutionLog in relational DB
        5. Return clean structured JSON contract for frontend
        """
        start_time = time.time()
        files = files or []

        # 1. User Resolution
        user = UserService.get_or_create_user(email=email, name=name, section=section)

        # 2. Document Ingestion & Dual Persistence
        ingestion_stats = {"file_count": 0, "chunks_created": 0, "failures": []}
        if files:
            try:
                ingestion_stats = self.ingestion_service.ingest_files(user=user, files=files)
            except Exception as e:
                logger.error(f"Document ingestion error for user {user.email}: {e}")
                return {
                    "status": "error",
                    "code": "DOCUMENT_INGESTION_FAILED",
                    "message": "One or more documents could not be indexed.",
                    "details": [str(e)]
                }

        # 3. Create Execution Audit Log record in PENDING state
        exec_log = AgentExecutionLog.objects.create(
            user=user,
            query=query,
            execution_status='PENDING'
        )

        max_retries = getattr(settings, 'MAX_RETRIES', 2)

        initial_state = {
            "user_id": str(user.id),
            "user_meta": {
                "name": user.name,
                "email": user.email,
                "section": user.section
            },
            "raw_input": query,
            "normalized_query": query,
            "subtasks": [],
            "retrieved_context": [],
            "risks": [],
            "solution_plan": "",
            "solver_a_output": "",
            "solver_b_output": "",
            "evaluator_audit": {},
            "evaluation_passed": False,
            "retry_count": 0,
            "max_retries": max_retries,
            "status": "INITIALIZED",
            "error_message": None,
            "actionable_critique": None,
            "final_solution": ""
        }

        # 4. Execute LangGraph Workflow
        try:
            final_state = self.graph.invoke(initial_state)
        except Exception as e:
            logger.error(f"LangGraph execution exception for log {exec_log.id}: {e}", exc_info=True)
            exec_log.execution_status = 'FAILED'
            exec_log.save()
            return {
                "status": "error",
                "code": "GRAPH_EXECUTION_FAILED",
                "message": f"Multi-agent workflow execution failed: {str(e)}",
                "details": []
            }

        duration = round(time.time() - start_time, 3)

        # 5. Extract Final Results & Dual-Write DB Audit Record
        eval_passed = final_state.get("evaluation_passed", False)
        retry_count = final_state.get("retry_count", 0)
        final_solution = final_state.get("final_solution", "")
        audit_report = final_state.get("evaluator_audit", {})
        retrieved_context = final_state.get("retrieved_context", [])

        exec_log.final_output = final_solution
        exec_log.retry_iterations = retry_count
        exec_log.evaluation_passed = eval_passed
        exec_log.hallucination_report = audit_report
        exec_log.execution_status = 'COMPLETED'
        exec_log.execution_duration = duration
        exec_log.save()

        # Format retrieved sources for frontend consumption
        retrieved_sources = []
        for ctx in retrieved_context:
            if ctx.get("content") != "NO_RELEVANT_CONTEXT_FOUND":
                retrieved_sources.append({
                    "content": ctx.get("content", "")[:200] + "...",
                    "source": ctx.get("source", "unknown"),
                    "page": ctx.get("page", 1),
                    "chunk_index": ctx.get("chunk_index", 0),
                    "score": ctx.get("score", 1.0)
                })

        return {
            "status": "success",
            "user_id": str(user.id),
            "execution_id": str(exec_log.id),
            "indexed_chunks": ingestion_stats.get("chunks_created", 0),
            "iterations_used": retry_count + 1,
            "evaluation_passed": eval_passed,
            "solution": final_solution,
            "hallucination_audit": {
                "is_valid": audit_report.get("is_valid", eval_passed),
                "confidence": audit_report.get("confidence", 1.0),
                "findings": audit_report.get("hallucination_findings", []),
                "unsupported_claims": audit_report.get("unsupported_claims", []),
                "contradictions": audit_report.get("contradictions", []),
                "missing_requirements": audit_report.get("missing_requirements", []),
                "actionable_critique": audit_report.get("actionable_critique", "")
            },
            "retrieved_sources": retrieved_sources,
            "execution_duration_seconds": duration
        }
