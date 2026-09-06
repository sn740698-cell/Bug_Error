from django.test import TestCase
from apps.workflows.state import WorkflowState, ProcessedDocument
from apps.workflows.graph import workflow_graph

class WorkflowGraphTestCase(TestCase):
    def test_workflow_graph_compilation(self):
        self.assertIsNotNone(workflow_graph)

    def test_workflow_execution(self):
        doc = ProcessedDocument(
            document_id="doc_graph_test",
            filename="sample_bill.txt",
            file_type="txt",
            file_size=512,
            text_content="INVOICE: INV-1001\nCustomer: John Doe\nBalance Due: ₹15,000.00\nDue Date: 2026-09-10"
        )
        initial_state = WorkflowState(workflow_id="wf_graph_exec", processed_documents=[doc])
        
        final_state = workflow_graph.invoke(initial_state)
        self.assertIsNotNone(final_state)
