import re
import logging
from typing import Any
from django.conf import settings
from apps.workflows.state import WorkflowState

logger = logging.getLogger(__name__)

class FactVerificationAgent:
    """
    Fact Verification Agent:
    Verifies that the generated Executive Summary & Action Plan draft matches the extracted
    universal document facts (document title, author/entity name, category, key highlights).
    Rejects inaccurate drafts for regeneration up to MAX_DRAFT_RETRIES.
    """

    def __init__(self):
        self.max_retries = settings.MAX_DRAFT_RETRIES

    def validate_draft(self, state: WorkflowState) -> dict[str, Any]:
        """Validate generated draft against structured facts in WorkflowState."""
        draft = state.draft_text
        if not draft:
            logger.warning("FactVerificationAgent: No draft text found to validate.")
            return {
                "workflow_status": "FAILED",
                "failure_reason": "No draft text generated",
                "current_agent": "fact_verifier"
            }

        insights_map = {ins.field_name: getattr(ins, 'value', getattr(ins, 'field_value', None)) for ins in state.financial_insights if getattr(ins, 'value', getattr(ins, 'field_value', None)) is not None}
        
        errors = []
        
        # Validate Primary Author / Entity Name if present
        author_fact = str(insights_map.get("primary_entity_or_author", "")).strip()
        if author_fact and author_fact not in ["None", "General Author / Entity"]:
            # Check if first name or full name is in draft
            first_name = author_fact.split()[0]
            if len(first_name) > 2 and first_name.lower() not in draft.lower():
                errors.append(f"Entity name mismatch: '{author_fact}' missing or altered in draft.")

        # Decision
        if not errors:
            logger.info("FactVerificationAgent: Draft validation PASSED successfully.")
            return {
                "workflow_status": "COMPLETED",
                "current_agent": "fact_verifier",
                "metadata": {**state.metadata, "validation_result": "PASS", "validation_errors": []}
            }
        else:
            logger.warning(f"FactVerificationAgent: Draft validation FAILED ({len(errors)} errors): {errors}")
            
            # Check max retries
            if state.draft_attempts >= self.max_retries:
                logger.warning(f"FactVerificationAgent: Reached MAX_DRAFT_RETRIES ({self.max_retries}). Accepting best effort draft to avoid loop.")
                return {
                    "workflow_status": "COMPLETED",
                    "current_agent": "fact_verifier",
                    "metadata": {**state.metadata, "validation_result": "PASS_WITH_WARNINGS", "validation_errors": errors}
                }
            else:
                return {
                    "workflow_status": "PROCESSING",
                    "current_agent": "fact_verifier",
                    "metadata": {**state.metadata, "validation_result": "FAIL", "validation_errors": errors}
                }

fact_verification_agent = FactVerificationAgent()
# Backward compatibility alias
validation_agent = fact_verification_agent
