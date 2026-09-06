from django.test import TestCase
from apps.workflows.state import WorkflowState, Message, FinancialInsightState, ProcessedDocument
from apps.workflows.reducers import merge_messages, merge_insights

class WorkflowStateTestCase(TestCase):
    def test_state_initialization(self):
        state = WorkflowState(workflow_id="wf_test_001")
        self.assertEqual(state.workflow_id, "wf_test_001")
        self.assertEqual(state.workflow_status, "PENDING")
        self.assertEqual(len(state.messages), 0)

    def test_reducers_merge_messages(self):
        msg1 = Message(id="msg_1", sender="user", content="Hello")
        msg2 = Message(id="msg_2", sender="system", content="Hi")
        merged = merge_messages([msg1], [msg2])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].content, "Hello")
        self.assertEqual(merged[1].content, "Hi")

    def test_reducers_merge_insights(self):
        ins1 = FinancialInsightState(field_name="balance_due", value=1000, confidence=0.8)
        ins2 = FinancialInsightState(field_name="balance_due", value=1000, confidence=0.95)
        merged = merge_insights([ins1], [ins2])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].confidence, 0.95)
