import logging
from django.conf import settings
from apps.workflows.state import WorkflowState

logger = logging.getLogger(__name__)

def route_next_step(state: WorkflowState) -> str:
    """
    Conditional router function for LangGraph graph execution.
    Determines next node or END based on WorkflowState, supervisor choices, and iteration safeguards.
    """
    # Safeguard 1: Prevent infinite loops
    if state.iteration_count >= settings.MAX_WORKFLOW_ITERATIONS:
        logger.warning(f"Workflow {state.workflow_id}: Reached MAX_WORKFLOW_ITERATIONS ({settings.MAX_WORKFLOW_ITERATIONS}). Terminating graph.")
        return "end_node"

    if state.workflow_status in ["COMPLETED", "FAILED"]:
        return "end_node"

    current_sup = state.current_supervisor
    val_result = state.metadata.get("validation_result")

    if current_sup in ["master_orchestrator", "financial_supervisor"]:
        # Check if financial insights are present
        if not state.financial_insights:
            return "master_orchestrator"

        # Check if critical fields missing and retrieval needed
        missing_critical = [
            ins.field_name for ins in state.financial_insights
            if ins.field_name in ["balance_due", "invoice_number", "total_amount"] and (ins.value is None or ins.confidence < 0.70)
        ]

        if missing_critical and state.retrieval_attempts < settings.MAX_RETRIEVAL_RETRIES:
            return "vector_retrieval_agent"

        # Hand off to communication supervisor
        return "communication_orchestrator"

    elif current_sup in ["communication_orchestrator", "communication_supervisor"]:
        if not state.draft_text or val_result == "FAIL":
            if state.draft_attempts < settings.MAX_DRAFT_RETRIES:
                return "communication_orchestrator"
            else:
                return "end_node"

        if val_result in ["PASS", "PASS_WITH_WARNINGS"]:
            return "end_node"

        return "communication_orchestrator"

    return "end_node"
