import logging
from datetime import datetime
from config.celery import app as celery_app
from .models import Workflow, FinancialInsight, RoutingDecision, GeneratedDraft
from apps.documents.models import Document, DocumentChunk
from apps.workflows.state import WorkflowState, ProcessedDocument, Message
from apps.workflows.graph import workflow_graph

logger = logging.getLogger(__name__)

def execute_langgraph_workflow(workflow_id: str):
    """Execute LangGraph multi-supervisor workflow and persist results to database."""
    try:
        workflow_db = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        logger.error(f"Workflow {workflow_id} not found.")
        return

    workflow_db.status = 'PROCESSING'
    workflow_db.save()

    doc_db = workflow_db.document
    chunks_db = DocumentChunk.objects.filter(document=doc_db)
    full_text = "\n\n".join([chk.chunk_text for chk in chunks_db])

    # Construct initial Pydantic WorkflowState
    processed_doc = ProcessedDocument(
        document_id=str(doc_db.id),
        filename=doc_db.filename,
        file_type=doc_db.file_type,
        file_size=doc_db.file_size,
        text_content=full_text,
        chunk_count=chunks_db.count()
    )

    initial_state = WorkflowState(
        workflow_id=str(workflow_db.id),
        user_id=str(workflow_db.user.id) if workflow_db.user else None,
        processed_documents=[processed_doc],
        messages=[Message(sender="System", content=f"Workflow initialized for document {doc_db.filename}")],
        workflow_status="PROCESSING"
    )

    logger.info(f"Executing LangGraph state graph for workflow {workflow_id}...")

    try:
        # Run LangGraph Graph
        final_state = workflow_graph.invoke(initial_state)
        
        # If final_state is a dict, parse into WorkflowState or access keys
        if isinstance(final_state, dict):
            status_val = final_state.get('workflow_status', 'COMPLETED')
            insights = final_state.get('financial_insights', [])
            routing_decisions = final_state.get('routing_decisions', [])
            draft_text = final_state.get('draft_text')
            simplified_summary = final_state.get('simplified_summary')
            document_sections = final_state.get('document_sections', {})
            selected_llm = final_state.get('selected_llm')
            fallback_used = final_state.get('fallback_used', False)
            failure_reason = final_state.get('failure_reason')
            current_sup = final_state.get('current_supervisor', 'communication_orchestrator')
            current_agt = final_state.get('current_agent', 'fact_verifier')
        else:
            status_val = final_state.workflow_status
            insights = final_state.financial_insights
            routing_decisions = final_state.routing_decisions
            draft_text = final_state.draft_text
            simplified_summary = getattr(final_state, 'simplified_summary', None)
            document_sections = getattr(final_state, 'document_sections', {})
            selected_llm = final_state.selected_llm
            fallback_used = final_state.fallback_used
            failure_reason = final_state.failure_reason
            current_sup = final_state.current_supervisor
            current_agt = final_state.current_agent

        # Persist extracted Financial Insights to Database
        FinancialInsight.objects.filter(workflow=workflow_db).delete()
        for ins in insights:
            if isinstance(ins, dict):
                field_name = ins.get('field_name')
                value = ins.get('value')
                confidence = ins.get('confidence', 0.0)
                source = ins.get('source', 'DocumentDecomposer')
            else:
                field_name = getattr(ins, 'field_name', None)
                value = getattr(ins, 'value', None)
                confidence = getattr(ins, 'confidence', 0.0)
                source = getattr(ins, 'source', 'DocumentDecomposer')

            FinancialInsight.objects.create(
                workflow=workflow_db,
                field_name=field_name,
                field_value=value,
                confidence=confidence,
                source=source
            )

        # Persist Routing Decisions to Database
        for route in routing_decisions:
            if isinstance(route, dict):
                supervisor = route.get('supervisor', '')
                selected_target = route.get('selected_target', '')
                reason = route.get('reason', '')
            else:
                supervisor = getattr(route, 'supervisor', '')
                selected_target = getattr(route, 'selected_target', '')
                reason = getattr(route, 'reason', '')

            RoutingDecision.objects.create(
                workflow=workflow_db,
                supervisor=supervisor,
                selected_target=selected_target,
                reason=reason
            )

        # Persist Generated Draft if available
        if draft_text:
            GeneratedDraft.objects.create(
                workflow=workflow_db,
                draft_text=draft_text,
                llm_model=selected_llm or "qwen",
                generation_attempt=1,
                validation_status="PASS"
            )

        workflow_db.status = 'COMPLETED' if draft_text else 'FAILED'
        workflow_db.document_sections = document_sections or {}
        workflow_db.simplified_summary = simplified_summary
        workflow_db.current_supervisor = current_sup
        workflow_db.current_agent = current_agt
        workflow_db.selected_llm = selected_llm
        workflow_db.fallback_used = fallback_used
        workflow_db.failure_reason = failure_reason
        workflow_db.completed_at = datetime.utcnow()
        workflow_db.save()

        logger.info(f"Workflow {workflow_id} execution finished with status {workflow_db.status}")

    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        workflow_db.status = 'FAILED'
        workflow_db.failure_reason = str(e)
        workflow_db.completed_at = datetime.utcnow()
        workflow_db.save()


@celery_app.task(name="tasks.run_langgraph_workflow")
def run_langgraph_workflow_task(workflow_id: str):
    """Celery task wrapper for running LangGraph workflow in background."""
    execute_langgraph_workflow(workflow_id)
