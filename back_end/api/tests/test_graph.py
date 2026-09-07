from django.test import TestCase
from api.agents.graph import create_agent_graph


class GraphTests(TestCase):
    def setUp(self):
        self.graph = create_agent_graph()

    def test_successful_graph_execution(self):
        initial_state = {
            "user_id": "test_user_001",
            "user_meta": {"name": "Test User", "email": "test@example.com", "section": "Engineering"},
            "raw_input": "Design a high-throughput transaction indexer.",
            "normalized_query": "Design a high-throughput transaction indexer.",
            "subtasks": [],
            "retrieved_context": [],
            "risks": [],
            "solution_plan": "",
            "solver_a_output": "",
            "solver_b_output": "",
            "evaluator_audit": {},
            "evaluation_passed": False,
            "retry_count": 0,
            "max_retries": 2,
            "status": "INITIALIZED",
            "error_message": None,
            "actionable_critique": None,
            "final_solution": ""
        }

        final_state = self.graph.invoke(initial_state)
        
        self.assertTrue(final_state.get("evaluation_passed"))
        self.assertEqual(final_state.get("status"), "EVALUATED")
        self.assertIsNotNone(final_state.get("final_solution"))
        self.assertIn("evaluator_audit", final_state)
        self.assertIn("confidence", final_state["evaluator_audit"])

    def test_max_retries_termination(self):
        # Initial state starting already at max_retries
        initial_state = {
            "user_id": "test_user_002",
            "user_meta": {"name": "Test User 2", "email": "test2@example.com", "section": "Engineering"},
            "raw_input": "Edge case query for retry loop test.",
            "normalized_query": "Edge case query for retry loop test.",
            "subtasks": [],
            "retrieved_context": [],
            "risks": [],
            "solution_plan": "",
            "solver_a_output": "",
            "solver_b_output": "",
            "evaluator_audit": {},
            "evaluation_passed": False,
            "retry_count": 2,
            "max_retries": 2,
            "status": "INITIALIZED",
            "error_message": None,
            "actionable_critique": None,
            "final_solution": ""
        }

        final_state = self.graph.invoke(initial_state)
        # Verify it completes without an infinite loop
        self.assertIsNotNone(final_state.get("final_solution"))
