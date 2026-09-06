import logging
from typing import Any
from apps.workflows.state import WorkflowState
from apps.ai.llm_router import llm_router

logger = logging.getLogger(__name__)

class LaymanSimplifierAgent:
    """
    Layman Simplifier Agent:
    Takes raw document text and extracted key document facts to produce a plain-English,
    layman-friendly executive summary explaining the document's core content, key findings,
    and action items.
    """

    SYSTEM_PROMPT = (
        "You are an expert document simplification assistant (J.A.R.V.I.S.).\n"
        "Your task is to convert any complex document (resumes, technical specifications, research papers, proposals, reports) "
        "into a clear, concise, and easy-to-understand plain English executive summary.\n\n"
        "Rules:\n"
        "1. Write 3-5 clean bullet points summarizing the document in plain English.\n"
        "2. State clearly what this document is (e.g. Candidate Resume, Technical Specification, Project Proposal).\n"
        "3. Highlight key entities, primary skills, core findings, or focus areas accurately.\n"
        "4. Summarize main accomplishments, experience, or takeaways based strictly on provided text.\n"
        "5. Do NOT invent invoices, money amounts, payment terms, or due dates if they are not in the text.\n"
        "6. Keep language plain, professional, and concise.\n"
    )

    def simplify_document(self, state: WorkflowState) -> dict[str, Any]:
        """Generate plain-English simplified document summary."""
        doc_text = ""
        if state.processed_documents:
            doc_text = state.processed_documents[0].text_content[:2000]

        facts_list = []
        for ins in state.financial_insights:
            val = getattr(ins, 'value', getattr(ins, 'field_value', None))
            if val is not None:
                facts_list.append(f"- {ins.field_name}: {val}")
        
        facts_summary = "\n".join(facts_list) if facts_list else "None available"

        user_prompt = (
            f"RAW DOCUMENT EXCERPT:\n{doc_text}\n\n"
            f"EXTRACTED DOCUMENT FACTS:\n{facts_summary}\n\n"
            f"Please provide a 3-5 bullet point plain English executive summary of this document now."
        )

        logger.info(f"LaymanSimplifierAgent: Generating simplified summary (Model: {state.selected_llm})...")

        res = llm_router.generate(
            model=state.selected_llm,
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        if res.get("success"):
            summary_text = res.get("reply", "").strip()
            logger.info("LaymanSimplifierAgent: Simplified summary generated successfully.")
            return {
                "simplified_summary": summary_text,
                "current_agent": "layman_simplifier"
            }
        else:
            fallback_summary = (
                f"• Executive Summary: Document analyzed with key facts: {facts_summary}.\n"
                f"• Please review extracted document insights for details and action items."
            )
            logger.warning(f"LaymanSimplifierAgent fallback used: {res.get('error')}")
            return {
                "simplified_summary": fallback_summary,
                "current_agent": "layman_simplifier"
            }

layman_simplifier_agent = LaymanSimplifierAgent()
# Backward compatibility alias
simplifier_agent = layman_simplifier_agent
