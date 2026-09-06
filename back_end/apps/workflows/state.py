from typing import Annotated, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from .reducers import (
    merge_messages,
    merge_documents,
    merge_insights,
    merge_routing_decisions,
    merge_context,
    merge_errors
)


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    sender: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProcessedDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    text_content: str = ""
    chunk_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FinancialInsightState(BaseModel):
    field_name: str
    value: Any = None
    currency: str | None = "INR"
    confidence: float = 0.0
    source: str = "DataAnalyzer"


class RoutingDecisionState(BaseModel):
    id: str = Field(default_factory=lambda: f"route_{uuid.uuid4().hex[:8]}")
    supervisor: str
    selected_target: str
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RetrievedContextState(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    similarity_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedDraftState(BaseModel):
    id: str = Field(default_factory=lambda: f"draft_{uuid.uuid4().hex[:8]}")
    draft_text: str
    selected_llm: str
    generation_attempt: int = 1
    validation_status: str = "PENDING"  # PASS | FAIL | PENDING
    validation_notes: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WorkflowErrorState(BaseModel):
    id: str = Field(default_factory=lambda: f"err_{uuid.uuid4().hex[:8]}")
    agent_or_supervisor: str
    error_message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WorkflowState(BaseModel):
    workflow_id: str
    user_id: str | None = None

    messages: Annotated[list[Message], merge_messages] = Field(default_factory=list)
    processed_documents: Annotated[list[ProcessedDocument], merge_documents] = Field(default_factory=list)
    financial_insights: Annotated[list[FinancialInsightState], merge_insights] = Field(default_factory=list)
    routing_decisions: Annotated[list[RoutingDecisionState], merge_routing_decisions] = Field(default_factory=list)
    retrieved_context: Annotated[list[RetrievedContextState], merge_context] = Field(default_factory=list)

    draft_text: str | None = None
    simplified_summary: str | None = None
    document_sections: dict[str, Any] = Field(default_factory=dict)
    selected_llm: str | None = "llama"
    hallucination_audit_passed: bool = True
    audit_notes: str | None = None
    fallback_used: bool = False
    failure_reason: str | None = None

    workflow_status: str = "PENDING"  # PENDING | PROCESSING | COMPLETED | FAILED
    current_supervisor: str | None = "master_orchestrator"
    current_agent: str | None = "document_decomposer"

    iteration_count: int = 0
    draft_attempts: int = 0
    retrieval_attempts: int = 0

    errors: Annotated[list[WorkflowErrorState], merge_errors] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
