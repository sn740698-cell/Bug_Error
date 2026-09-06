import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from apps.workflows.state import WorkflowState
from apps.workflows.supervisors.financial_supervisor import master_orchestrator_supervisor
from apps.workflows.supervisors.communication_supervisor import communication_orchestrator_supervisor
from apps.workflows.agents.decomposer_agent import document_decomposer_agent
from apps.workflows.agents.retrieval_agent import vector_knowledge_retrieval_agent
from apps.workflows.agents.simplifier_agent import layman_simplifier_agent
from apps.workflows.agents.texting_agent import notification_drafting_agent
from apps.workflows.agents.validation_agent import fact_verification_agent
from apps.workflows.agents.hallucination_audit_agent import hallucination_audit_agent
from apps.workflows.routers import route_next_step

logger = logging.getLogger(__name__)

def node_master_orchestrator(state: WorkflowState) -> dict[str, Any]:
    return master_orchestrator_supervisor.process(state)

def node_document_decomposer(state: WorkflowState) -> dict[str, Any]:
    return document_decomposer_agent.decompose_and_analyze(state)

def node_vector_retrieval(state: WorkflowState) -> dict[str, Any]:
    return vector_knowledge_retrieval_agent.retrieve(state)

def node_layman_simplifier(state: WorkflowState) -> dict[str, Any]:
    return layman_simplifier_agent.simplify_document(state)

def node_communication_orchestrator(state: WorkflowState) -> dict[str, Any]:
    return communication_orchestrator_supervisor.process(state)

def node_notification_drafter(state: WorkflowState) -> dict[str, Any]:
    return notification_drafting_agent.generate_notification(state)

def node_fact_verifier(state: WorkflowState) -> dict[str, Any]:
    return fact_verification_agent.validate_draft(state)

def node_hallucination_auditor(state: WorkflowState) -> dict[str, Any]:
    return hallucination_audit_agent.audit_state(state)

def node_end(state: WorkflowState) -> dict[str, Any]:
    status = "COMPLETED" if state.draft_text else "FAILED"
    return {"workflow_status": status}

def build_workflow_graph() -> StateGraph:
    """Build and compile the Agentic Framework multi-supervisor LangGraph state graph."""
    builder = StateGraph(WorkflowState)

    # Add Supervisor and Agent Nodes
    builder.add_node("master_orchestrator", node_master_orchestrator)
    builder.add_node("financial_supervisor", node_master_orchestrator) # Alias
    builder.add_node("document_decomposer", node_document_decomposer)
    builder.add_node("data_analyzer", node_document_decomposer) # Alias
    builder.add_node("vector_retrieval_agent", node_vector_retrieval)
    builder.add_node("retrieval_agent", node_vector_retrieval) # Alias
    builder.add_node("layman_simplifier", node_layman_simplifier)
    builder.add_node("communication_orchestrator", node_communication_orchestrator)
    builder.add_node("communication_supervisor", node_communication_orchestrator) # Alias
    builder.add_node("notification_drafter", node_notification_drafter)
    builder.add_node("texting_agent", node_notification_drafter) # Alias
    builder.add_node("fact_verifier", node_fact_verifier)
    builder.add_node("validation_agent", node_fact_verifier) # Alias
    builder.add_node("hallucination_auditor", node_hallucination_auditor)
    builder.add_node("end_node", node_end)

    # Start Edge
    builder.add_edge(START, "master_orchestrator")

    # Conditional Routing Edges
    builder.add_conditional_edges(
        "master_orchestrator",
        route_next_step,
        {
            "master_orchestrator": "master_orchestrator",
            "document_decomposer": "document_decomposer",
            "vector_retrieval_agent": "vector_retrieval_agent",
            "communication_orchestrator": "communication_orchestrator",
            "end_node": "end_node"
        }
    )

    builder.add_edge("document_decomposer", "master_orchestrator")
    builder.add_edge("vector_retrieval_agent", "master_orchestrator")
    builder.add_edge("layman_simplifier", "master_orchestrator")

    builder.add_conditional_edges(
        "communication_orchestrator",
        route_next_step,
        {
            "communication_orchestrator": "communication_orchestrator",
            "notification_drafter": "notification_drafter",
            "fact_verifier": "fact_verifier",
            "hallucination_auditor": "hallucination_auditor",
            "end_node": "end_node"
        }
    )

    builder.add_edge("notification_drafter", "communication_orchestrator")
    builder.add_edge("fact_verifier", "communication_orchestrator")
    builder.add_edge("hallucination_auditor", "communication_orchestrator")
    builder.add_edge("end_node", END)

    compiled_graph = builder.compile()
    logger.info("LangGraph Agentic Framework state graph compiled successfully.")
    return compiled_graph

workflow_graph = build_workflow_graph()
