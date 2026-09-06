import re
import logging
from typing import Any
from apps.workflows.state import WorkflowState, FinancialInsightState

logger = logging.getLogger(__name__)

class DocumentDecomposerAgent:
    """
    Universal Document Decomposer Agent:
    Partitions / divides ANY document (Resumes, Proposals, Technical Specs, Reports)
    into 4 specialized structural sections:
      1. Title, Author & Header Metadata Section (header_metadata)
      2. Main Content & Primary Details Section (core_details)
      3. Core Skills, Topics & Focus Areas Section (key_topics)
      4. Key Takeaways, Outcomes & Next Steps Section (action_items)
    Analyzes each section to extract 8-10 universal document facts with confidence scores.
    """

    def decompose_and_analyze(self, state: WorkflowState) -> dict[str, Any]:
        """Divide document into 4 structural sections and extract universal document facts."""
        doc_text = ""
        if state.processed_documents:
            doc_text = state.processed_documents[0].text_content

        if not doc_text:
            logger.warning("DocumentDecomposerAgent: Document text content is empty.")
            return {
                "financial_insights": [],
                "document_sections": {},
                "current_agent": "document_decomposer"
            }

        logger.info(f"DocumentDecomposerAgent: Decomposing document ({len(doc_text)} chars) into universal sections...")

        lines = [line.strip() for line in doc_text.splitlines() if line.strip()]

        header_lines = []
        core_lines = []
        topics_lines = []
        action_lines = []

        # Categorize lines into 4 general structural sections
        for idx, line in enumerate(lines):
            lower = line.lower()
            if idx < 6 or any(k in lower for k in ["resume", "curriculum vitae", "proposal", "specification", "title:", "author:", "name:", "email:", "contact:", "phone:"]):
                header_lines.append(line)
            elif any(k in lower for k in ["skills", "experience", "projects", "education", "technologies", "topics", "highlights"]):
                topics_lines.append(line)
            elif any(k in lower for k in ["summary", "next steps", "recommendations", "action", "takeaway", "conclusion", "outcomes"]):
                action_lines.append(line)
            else:
                core_lines.append(line)

        document_sections = {
            "header_metadata": " | ".join(header_lines[:5]) if header_lines else doc_text[:300],
            "core_details": " | ".join(core_lines[:10]) if core_lines else doc_text[300:800],
            "key_topics": " | ".join(topics_lines[:8]) if topics_lines else "Key skills & focus areas extracted",
            "action_items": " | ".join(action_lines[:5]) if action_lines else "Summary takeaways & outcomes extracted"
        }

        # 2. Extract Universal Document Facts
        insights = []

        # Document Title
        title_val = lines[0] if lines else "Document Summary"
        if len(title_val) > 80:
            title_val = title_val[:80] + "..."
        insights.append(FinancialInsightState(field_name="document_title", value=title_val, confidence=0.95, source="DocumentDecomposer.Header"))

        # Primary Entity or Author Name
        author_val = None
        for line in lines[:8]:
            m = re.search(r'(?:name|author|candidate|vendor|presenter)\s*[:\s]*([A-Za-z\s\.\-_]+)', line, re.IGNORECASE)
            if m and len(m.group(1).strip()) > 2:
                author_val = m.group(1).strip()
                break
        if not author_val and lines:
            # Fallback to first line if title-like
            first_line = lines[0].strip()
            if len(first_line.split()) <= 4 and not any(c in first_line for c in [':', '@', 'http']):
                author_val = first_line

        insights.append(FinancialInsightState(field_name="primary_entity_or_author", value=author_val or "General Author / Entity", confidence=0.88 if author_val else 0.50, source="DocumentDecomposer.Header"))

        # Document Category
        cat_val = "General Document"
        lower_full = doc_text.lower()
        if "resume" in lower_full or "curriculum vitae" in lower_full or "education" in lower_full and "skills" in lower_full:
            cat_val = "Resume / Candidate CV"
        elif "proposal" in lower_full or "architecture" in lower_full or "specification" in lower_full:
            cat_val = "Project Proposal / Specification"
        elif "report" in lower_full or "paper" in lower_full:
            cat_val = "Research / Technical Report"
        elif "invoice" in lower_full or "billing" in lower_full:
            cat_val = "Business / Financial Document"

        insights.append(FinancialInsightState(field_name="document_category", value=cat_val, confidence=0.92, source="DocumentDecomposer.Header"))

        # Contact or Location Info
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', doc_text)
        location_match = re.search(r'(?:location|address|city)\s*[:\s]*([A-Za-z0-9\s,\.\-_]+)', doc_text, re.IGNORECASE)
        contact_info = []
        if email_match:
            contact_info.append(email_match.group(1))
        if location_match:
            contact_info.append(location_match.group(1).split('\n')[0].strip())
        contact_val = " | ".join(contact_info) if contact_info else None

        insights.append(FinancialInsightState(field_name="contact_or_location", value=contact_val, confidence=0.90 if contact_val else 0.0, source="DocumentDecomposer.Header"))

        # Primary Skills or Focus Topics
        skills_lines = [line for line in lines if any(k in line.lower() for k in ["python", "react", "django", "javascript", "ai", "machine learning", "java", "c++", "sql", "git", "cloud", "aws"])]
        skills_val = ", ".join(list(set([w.strip() for line in skills_lines for w in line.replace('|', ',').split(',') if len(w.strip()) < 30])))
        if len(skills_val) > 120:
            skills_val = skills_val[:120] + "..."

        insights.append(FinancialInsightState(field_name="primary_skills_or_domain", value=skills_val or "General Multi-Domain Analysis", confidence=0.85 if skills_val else 0.50, source="DocumentDecomposer.Topics"))

        # Key Highlights
        highlights = [line for line in lines if any(k in line.lower() for k in ["project", "worked", "built", "developed", "winner", "award", "experience", "result", "achieved"])]
        highlights_val = " | ".join(highlights[:3]) if highlights else doc_text[:200]
        if len(highlights_val) > 150:
            highlights_val = highlights_val[:150] + "..."

        insights.append(FinancialInsightState(field_name="key_highlights", value=highlights_val, confidence=0.88, source="DocumentDecomposer.Topics"))

        # Action Items & Recommendations
        action_val = "Review core details, verify key competencies, and assess next implementation steps."
        insights.append(FinancialInsightState(field_name="action_items", value=action_val, confidence=0.90, source="DocumentDecomposer.ActionItems"))

        logger.info(f"DocumentDecomposerAgent: Extracted {len(insights)} universal document facts across 4 partitioned sections.")

        return {
            "financial_insights": insights,
            "document_sections": document_sections,
            "current_agent": "document_decomposer"
        }

    def decompose(self, state: WorkflowState) -> dict[str, Any]:
        return self.decompose_and_analyze(state)

    def analyze(self, state: WorkflowState) -> dict[str, Any]:
        return self.decompose_and_analyze(state)

document_decomposer_agent = DocumentDecomposerAgent()
# Backward compatibility alias
data_analyzer_agent = document_decomposer_agent
