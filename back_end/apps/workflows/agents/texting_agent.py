import logging
from typing import Any
from apps.workflows.state import WorkflowState, GeneratedDraftState
from apps.ai.llm_router import llm_router

logger = logging.getLogger(__name__)

class ExecutiveSummaryDrafterAgent:
    """
    Executive Summary & Action Plan Drafter Agent (formerly NotificationDraftingAgent):
    Receives validated document facts and generates a concise, professional Executive Summary
    and Action Plan draft using LLMRouter (Llama 3.2 1B Primary).
    """

    SYSTEM_PROMPT = (
        "You are an expert executive summary and action plan drafting assistant (J.A.R.V.I.S.).\n"
        "Your job is to create a professional Executive Summary & Action Plan based on the analyzed document.\n\n"
        "Rules:\n"
        "1. Use only the supplied structured document facts and details.\n"
        "2. Never invent unverified facts, financial amounts, or false statements.\n"
        "3. Include a short 2-sentence Overview.\n"
        "4. Include 3 Key Competencies / Findings.\n"
        "5. Include 2 Actionable Recommendations / Next Steps.\n"
        "6. Keep the message professional, structured, and clear.\n"
    )

    def generate_notification(self, state: WorkflowState) -> dict[str, Any]:
        """Generate Executive Summary & Action Plan draft based on structured state facts."""
        insights_map = {ins.field_name: getattr(ins, 'value', getattr(ins, 'field_value', None)) for ins in state.financial_insights if getattr(ins, 'value', getattr(ins, 'field_value', None)) is not None}

        title = insights_map.get("document_title") or "Document Analysis Report"
        author = insights_map.get("primary_entity_or_author") or "General Entity / Author"
        category = insights_map.get("document_category") or "General Document"
        skills = insights_map.get("primary_skills_or_domain") or "N/A"
        highlights = insights_map.get("key_highlights") or "N/A"
        action = insights_map.get("action_items") or "Review details and confirm next steps."

        user_prompt = (
            f"STRUCTURED DOCUMENT FACTS:\n"
            f"- Document Title: {title}\n"
            f"- Author/Entity: {author}\n"
            f"- Category: {category}\n"
            f"- Primary Domain/Skills: {skills}\n"
            f"- Key Highlights: {highlights}\n"
            f"- Action Recommendations: {action}\n\n"
            f"Please generate the Executive Summary & Action Plan draft text now."
        )

        model_choice = state.selected_llm
        logger.info(f"ExecutiveSummaryDrafterAgent: Generating executive summary draft (Model preference: {model_choice})...")

        res = llm_router.generate(
            model=model_choice,
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        if res.get("success"):
            draft_text = res.get("reply", "")
            selected_model = res.get("selected_llm", "llama")
            fallback_used = res.get("fallback_used", False)
            failure_reason = res.get("failure_reason")

            return {
                "draft_text": draft_text,
                "selected_llm": selected_model,
                "fallback_used": fallback_used,
                "failure_reason": failure_reason,
                "draft_attempts": state.draft_attempts + 1,
                "current_agent": "notification_drafter"
            }
        else:
            error_msg = res.get("error", "Failed to generate draft with LLMRouter")
            logger.error(f"ExecutiveSummaryDrafterAgent: {error_msg}")
            return {
                "draft_text": None,
                "failure_reason": error_msg,
                "draft_attempts": state.draft_attempts + 1,
                "current_agent": "notification_drafter"
            }

notification_drafting_agent = ExecutiveSummaryDrafterAgent()
# Backward compatibility alias
texting_agent = notification_drafting_agent
