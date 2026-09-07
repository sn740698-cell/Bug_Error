import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from api.agents.state import AgentGraphState
from api.agents.nodes import (
    ingestion_node,
    decomposition_node,
    rag_node,
    risk_node,
    planner_node,
    solver_a_node,
    solver_b_node,
    evaluator_node
)
from api.agents.router import route_evaluator_output

logger = logging.getLogger(__name__)


def retry_counter_node(state: AgentGraphState) -> Dict[str, Any]:
    """Helper node to increment retry counter before re-entering Planner."""
    current_retry = state.get("retry_count", 0) + 1
    logger.info(f"[Retry Counter] Incrementing retry_count to {current_retry}")
    return {"retry_count": current_retry}


def create_agent_graph():
    """
    Constructs and compiles the 8-Agent LangGraph StateGraph.
    
    Flow:
    Agent 1 (Ingestion) -> Agent 2 (Decomposition)
      -> Agent 3 (RAG) & Agent 4 (Risk)
      -> Agent 5 (Planner)
      -> Agent 6 (Solver A) & Agent 7 (Solver B) [Parallel Fan-Out]
      -> Agent 8 (Evaluator Judge) [Parallel Fan-In]
      -> Conditional Feedback Loop:
            - Valid OR Max Retries Exhausted -> END
            - Invalid AND Retries Remaining -> Retry Counter -> Agent 5 (Planner)
    """
    builder = StateGraph(AgentGraphState)

    # 1. Add Agent Nodes
    builder.add_node("ingestion_node", ingestion_node)
    builder.add_node("decomposition_node", decomposition_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("risk_node", risk_node)
    builder.add_node("planner_node", planner_node)
    builder.add_node("solver_a_node", solver_a_node)
    builder.add_node("solver_b_node", solver_b_node)
    builder.add_node("evaluator_node", evaluator_node)
    builder.add_node("retry_counter_node", retry_counter_node)

    # 2. Set Entry Point
    builder.set_entry_point("ingestion_node")

    # 3. Add Edges
    builder.add_edge("ingestion_node", "decomposition_node")
    
    # Branching from Decomposition into RAG and Risk analysis
    builder.add_edge("decomposition_node", "rag_node")
    builder.add_edge("decomposition_node", "risk_node")

    # Merge RAG & Risk into Planner
    builder.add_edge("rag_node", "planner_node")
    builder.add_edge("risk_node", "planner_node")

    # Parallel Fan-Out from Planner to Solvers A & B
    builder.add_edge("planner_node", "solver_a_node")
    builder.add_edge("planner_node", "solver_b_node")

    # Parallel Fan-In from Solvers A & B to Evaluator Judge
    builder.add_edge("solver_a_node", "evaluator_node")
    builder.add_edge("solver_b_node", "evaluator_node")

    # Conditional Routing from Evaluator Judge
    builder.add_conditional_edges(
        "evaluator_node",
        route_evaluator_output,
        {
            "end_node": END,
            "ingestion_node": "retry_counter_node"
        }
    )

    # Retry counter routes back into Agent 1 (Ingestion Node) for complete re-chunking & re-division
    builder.add_edge("retry_counter_node", "ingestion_node")

    compiled_graph = builder.compile()
    logger.info("Compiled 8-Agent LangGraph workflow successfully.")
    return compiled_graph
