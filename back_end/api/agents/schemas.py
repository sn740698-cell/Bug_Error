from typing import List
from pydantic import BaseModel, Field


class AntiHallucinationAudit(BaseModel):
    """
    Structured audit evaluation schema returned by Agent 8 (EvaluatorJudgeAgent).
    Enforces explicit grounding checks, contradiction detection, and confidence scoring.
    """
    is_valid: bool = Field(description="True if the solution is factually grounded, complete, and free of invalid hallucinations.")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0.")
    hallucination_findings: List[str] = Field(default_factory=list, description="Specific hallucination instances detected.")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims made without retrieved context or explicit proof.")
    contradictions: List[str] = Field(default_factory=list, description="Contradictions between Solution A and Solution B or context.")
    missing_requirements: List[str] = Field(default_factory=list, description="User requirements not satisfied by the solution.")
    actionable_critique: str = Field(default="", description="Constructive, actionable feedback for Agent 5 (Planner) on retry.")
    synthesized_solution: str = Field(default="", description="Final synthesized, grounded solution combining the best outputs.")
