import logging
from typing import Any
from apps.workflows.state import WorkflowState, RoutingDecisionState
from apps.workflows.agents.decomposer_agent import document_decomposer_agent
from apps.workflows.agents.retrieval_agent import vector_knowledge_retrieval_agent

logger = logging.getLogger(__name__)

class MasterOrchestratorSupervisor:
    """
    Master Orchestrator Supervisor (formerly FinancialSupervisor):
    Oversees financial document processing, multi-part document decomposition,
    vector knowledge retrieval decisions, and layman simplification.
    Flow: Master Orchestrator -> Document Decomposer Agent -> Vector Knowledge Retrieval Agent (if needed) -> Layman Simplifier Agent -> Communication Orchestrator
    """

    def process(self, state: WorkflowState) -> dict[str, Any]:
        """Determine next step under Master Orchestrator Supervision."""
        logger.info(f"MasterOrchestratorSupervisor: Processing workflow {state.workflow_id} (Iteration {state.iteration_count})")

        # 1. If financial insights not extracted yet, trigger DocumentDecomposerAgent
        if not state.financial_insights:
            decision = RoutingDecisionState(
                supervisor="MasterOrchestratorSupervisor",
                selected_target="DocumentDecomposerAgent",
                reason="No financial insights present; initiating multi-part document division & analysis."
            )
            analysis_result = document_decomposer_agent.decompose_and_analyze(state)
            return {
                "routing_decisions": [decision],
                "current_supervisor": "master_orchestrator",
                "current_agent": "document_decomposer",
                "iteration_count": state.iteration_count + 1,
                **analysis_result
            }

        # 2. Check if critical financial fields are missing or low confidence
        missing_critical = []
        for ins in state.financial_insights:
            if ins.field_name in ["balance_due", "invoice_number", "total_amount"] and (ins.value is None or ins.confidence < 0.70):
                missing_critical.append(ins.field_name)

        if missing_critical and state.retrieval_attempts == 0:
            decision = RoutingDecisionState(
                supervisor="MasterOrchestratorSupervisor",
                selected_target="VectorKnowledgeRetrievalAgent",
                reason=f"Missing or low-confidence fields ({', '.join(missing_critical)}); triggering vector retrieval."
            )
            retrieval_result = vector_knowledge_retrieval_agent.retrieve(state)
            return {
                "routing_decisions": [decision],
                "current_supervisor": "master_orchestrator",
                "current_agent": "vector_retrieval_agent",
                "iteration_count": state.iteration_count + 1,
                **retrieval_result
            }

        # 3. Check if simplified summary is generated
        if not state.simplified_summary:
            decision = RoutingDecisionState(
                supervisor="MasterOrchestratorSupervisor",
                selected_target="LaymanSimplifierAgent",
                reason="Financial insights complete; generating plain-English layman document summary."
            )
            from apps.workflows.agents.simplifier_agent import layman_simplifier_agent
            simplify_res = layman_simplifier_agent.simplify_document(state)
            return {
                "routing_decisions": [decision],
                "current_supervisor": "master_orchestrator",
                "current_agent": "layman_simplifier",
                "iteration_count": state.iteration_count + 1,
                **simplify_res
            }

        # 4. Master Orchestration complete -> Hand off to Communication Orchestrator Supervisor
        decision = RoutingDecisionState(
            supervisor="MasterOrchestratorSupervisor",
            selected_target="CommunicationOrchestratorSupervisor",
            reason="Master orchestration complete; handing off to Communication Orchestrator Supervisor."
        )
        return {
            "routing_decisions": [decision],
            "current_supervisor": "communication_orchestrator",
            "current_agent": "notification_drafter",
            "iteration_count": state.iteration_count + 1
        }

master_orchestrator_supervisor = MasterOrchestratorSupervisor()
# Backward compatibility alias
financial_supervisor = master_orchestrator_supervisor
