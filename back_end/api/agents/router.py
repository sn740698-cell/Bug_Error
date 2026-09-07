import logging
from typing import Dict, Any, Literal
from api.agents.state import AgentGraphState

logger = logging.getLogger(__name__)


def route_evaluator_output(state: AgentGraphState) -> Literal["ingestion_node", "end_node"]:
    """
    Conditional router evaluated after Agent 8 (EvaluatorJudgeAgent).
    If Agent 8 detects an invalid response, routes back to Agent 1 (ingestion_node) for re-chunking and re-planning.
    """
    evaluation_passed = state.get("evaluation_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if evaluation_passed:
        logger.info(f"[Router] Agent 8 Audit PASSED on attempt {retry_count}. Routing to END.")
        return "end_node"

    if retry_count < max_retries:
        logger.warning(
            f"[Router] Agent 8 Audit FAILED on attempt {retry_count} (max={max_retries}). "
            f"Routing back to Agent 1 (IngestionAgent) for complete re-chunking and re-division."
        )
        return "ingestion_node"

    logger.warning(
        f"[Router] Agent 8 Audit FAILED and max retries reached ({retry_count}/{max_retries}). "
        f"Routing to END with best audited output."
    )
    return "end_node"
