from django.test import TestCase
from django.db.utils import IntegrityError
from api.models import UserProfile, IngestedDocument, AgentExecutionLog


class ModelTests(TestCase):
    def test_create_user_profile(self):
        user = UserProfile.objects.create(
            name="Alex Mercer",
            email="alex.mercer@innovate.org",
            section="Distributed Systems"
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(str(user), "Alex Mercer <alex.mercer@innovate.org>")

    def test_unique_email_constraint(self):
        UserProfile.objects.create(
            name="User 1",
            email="duplicate@example.com"
        )
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(
                name="User 2",
                email="duplicate@example.com"
            )

    def test_ingested_document_relation(self):
        user = UserProfile.objects.create(
            name="Doc User",
            email="docuser@example.com"
        )
        doc = IngestedDocument.objects.create(
            user=user,
            original_file_name="architecture.pdf",
            normalized_file_type="PDF",
            stored_file_path="/tmp/architecture.pdf",
            total_chunks=12,
            ingestion_status="INDEXED"
        )
        self.assertEqual(user.ingested_documents.count(), 1)
        self.assertEqual(user.ingested_documents.first(), doc)

    def test_agent_execution_log_relation(self):
        user = UserProfile.objects.create(
            name="Log User",
            email="loguser@example.com"
        )
        log = AgentExecutionLog.objects.create(
            user=user,
            query="Design low-latency ledger",
            final_output="Consensus solution text",
            retry_iterations=1,
            evaluation_passed=True,
            execution_status="COMPLETED"
        )
        self.assertEqual(user.execution_logs.count(), 1)
        self.assertTrue(log.evaluation_passed)
