import logging
from typing import Any
from django.conf import settings
from apps.workflows.state import WorkflowState, RoutingDecisionState
from apps.workflows.agents.texting_agent import notification_drafting_agent
from apps.workflows.agents.validation_agent import fact_verification_agent
from apps.workflows.agents.hallucination_audit_agent import hallucination_audit_agent

logger = logging.getLogger(__name__)

class CommunicationOrchestratorSupervisor:
    """
    Communication Orchestrator Supervisor (formerly CommunicationSupervisor):
    Oversees LLM model selection, balance-due draft generation, fact verification, and real-time anti-hallucination auditing.
    Flow: Communication Orchestrator -> Notification Drafting Agent -> Fact Verification Agent -> Hallucination Audit Agent
    """

    def __init__(self):
        self.max_draft_retries = settings.MAX_DRAFT_RETRIES

    def process(self, state: WorkflowState) -> dict[str, Any]:
        """Determine next step under Communication Orchestrator Supervision."""
        logger.info(f"CommunicationOrchestratorSupervisor: Processing workflow {state.workflow_id} (Attempt {state.draft_attempts})")

        # 1. Model selection (Default to Llama 3.2 1B GGUF)
        selected_model = state.selected_llm
        if not selected_model:
            selected_model = getattr(settings, 'OLLAMA_PRIMARY_MODEL', getattr(settings, 'DEFAULT_LLM', 'llama'))

        # 2. If draft not generated or rejected for retry, trigger NotificationDraftingAgent
        validation_res = state.metadata.get("validation_result")
        
        if not state.draft_text or (validation_res == "FAIL" and state.draft_attempts < self.max_draft_retries):
            decision = RoutingDecisionState(
                supervisor="CommunicationOrchestratorSupervisor",
                selected_target="ExecutiveSummaryDrafterAgent",
                reason="Draft missing or validation failed; delegating to Executive Summary Drafter Agent (Llama 3.2 1B)."
            )
            draft_res = notification_drafting_agent.generate_notification(
                state.model_copy(update={"selected_llm": selected_model})
            )
            return {
                "routing_decisions": [decision],
                "current_supervisor": "communication_orchestrator",
                "current_agent": "notification_drafter",
                "iteration_count": state.iteration_count + 1,
                **draft_res
            }

        # 3. If draft exists but pending validation, trigger FactVerificationAgent
        if state.draft_text and validation_res is None:
            decision = RoutingDecisionState(
                supervisor="CommunicationOrchestratorSupervisor",
                selected_target="FactVerificationAgent",
                reason="Validating generated executive summary draft against document facts."
            )
            val_res = fact_verification_agent.validate_draft(state)
            return {
                "routing_decisions": [decision],
                "current_supervisor": "communication_orchestrator",
                "current_agent": "fact_verifier",
                "iteration_count": state.iteration_count + 1,
                **val_res
            }

        # 4. If draft validated, trigger HallucinationAuditAgent for anti-hallucination verification
        if state.draft_text and validation_res == "PASS" and not state.metadata.get("hallucination_audited"):
            decision = RoutingDecisionState(
                supervisor="CommunicationOrchestratorSupervisor",
                selected_target="HallucinationAuditAgent",
                reason="Performing real-time NLI anti-hallucination audit on draft and summary against document context."
            )
            audit_res = hallucination_audit_agent.audit_state(state)
            # Mark as audited in metadata
            new_metadata = {**state.metadata, "hallucination_audited": True}
            return {
                "routing_decisions": [decision],
                "current_supervisor": "communication_orchestrator",
                "current_agent": "hallucination_auditor",
                "metadata": new_metadata,
                "iteration_count": state.iteration_count + 1,
                **audit_res
            }

        # 5. Draft approved and audited -> Terminate
        final_status = "COMPLETED" if state.draft_text else "FAILED"
        return {
            "workflow_status": final_status,
            "current_supervisor": "communication_orchestrator",
            "current_agent": "hallucination_auditor" if state.metadata.get("hallucination_audited") else "fact_verifier",
            "iteration_count": state.iteration_count + 1
        }

communication_orchestrator_supervisor = CommunicationOrchestratorSupervisor()
# Backward compatibility alias
communication_supervisor = communication_orchestrator_supervisor
