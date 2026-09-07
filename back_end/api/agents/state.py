from typing import TypedDict, List, Dict, Any, Optional


class AgentGraphState(TypedDict):
    """
    Explicit TypedDict state schema passed through the 8-agent LangGraph workflow.
    """
    user_id: str
    user_meta: Dict[str, Any]
    raw_input: str
    normalized_query: str
    subtasks: List[str]
    retrieved_context: List[Dict[str, Any]]
    risks: List[str]
    solution_plan: str
    solver_a_output: str
    solver_b_output: str
    evaluator_audit: Dict[str, Any]
    evaluation_passed: bool
    retry_count: int
    max_retries: int
    status: str
    error_message: Optional[str]
    actionable_critique: Optional[str]
    final_solution: str
