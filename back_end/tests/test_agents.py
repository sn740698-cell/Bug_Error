from django.test import TestCase
from apps.workflows.state import WorkflowState, ProcessedDocument, FinancialInsightState
from apps.workflows.agents.decomposer_agent import document_decomposer_agent, DocumentDecomposerAgent
from apps.workflows.agents.validation_agent import fact_verification_agent, FactVerificationAgent
from apps.workflows.agents.simplifier_agent import layman_simplifier_agent
from apps.workflows.agents.texting_agent import notification_drafting_agent

class AgentsTestCase(TestCase):
    def test_document_decomposer_agent(self):
        doc = ProcessedDocument(
            document_id="doc_1",
            filename="proposal.txt",
            file_type="txt",
            file_size=1024,
            text_content="Title: J.A.R.V.I.S. Autonomous AI Platform\nAuthor: Suraj M N\nEmail: sn740698@gmail.com\nCategory: Multi-Agent Systems\nSkills: Python, React, Agentic AI\nSummary: Built autonomous 5-agent zero-hallucination platform."
        )
        state = WorkflowState(workflow_id="wf_agent_test", processed_documents=[doc])
        result = document_decomposer_agent.decompose(state)
        
        self.assertIn("financial_insights", result)
        self.assertIn("document_sections", result)
        
        sections = result["document_sections"]
        self.assertIn("header_metadata", sections)
        self.assertIn("key_topics", sections)

        insights = {ins.field_name: getattr(ins, 'value', getattr(ins, 'field_value', None)) for ins in result["financial_insights"]}
        self.assertIn("document_title", insights)
        self.assertIn("primary_entity_or_author", insights)

    def test_fact_verification_agent(self):
        insights = [
            FinancialInsightState(field_name="document_title", value="J.A.R.V.I.S. Platform Proposal"),
            FinancialInsightState(field_name="primary_entity_or_author", value="Suraj M N"),
            FinancialInsightState(field_name="document_category", value="Project Proposal")
        ]
        valid_draft = "Executive Summary: J.A.R.V.I.S. Platform Proposal authored by Suraj M N."
        state = WorkflowState(workflow_id="wf_val_test", financial_insights=insights, draft_text=valid_draft)
        
        result = fact_verification_agent.validate_draft(state)
        self.assertEqual(result.get("workflow_status"), "COMPLETED")

    def test_hallucination_audit_agent(self):
        from apps.workflows.agents.hallucination_audit_agent import hallucination_audit_agent
        insights = [
            FinancialInsightState(field_name="document_title", value="J.A.R.V.I.S. Platform Proposal"),
            FinancialInsightState(field_name="primary_entity_or_author", value="Suraj M N")
        ]
        valid_draft = "Executive Summary: J.A.R.V.I.S. Platform Proposal authored by Suraj M N."
        state = WorkflowState(workflow_id="wf_audit_test", financial_insights=insights, draft_text=valid_draft)
        
        result = hallucination_audit_agent.audit_state(state)
        self.assertTrue(result.get("hallucination_audit_passed"))
