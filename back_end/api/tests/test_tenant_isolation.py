import uuid
from django.test import TestCase
from api.services.vectorstore import ChromaVectorStoreService


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.vector_service = ChromaVectorStoreService(collection_name="test_tenant_isolation_collection")
        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())

    def test_tenant_vector_isolation(self):
        # Index document for User A
        chunks_user_a = [{
            "text": "User A confidential secret financial record 2026.",
            "page": 1
        }]
        self.vector_service.add_chunks(
            user_id=self.user_a_id,
            document_id="doc_user_a_001",
            file_name="user_a_finance.pdf",
            doc_type="PDF",
            chunks=chunks_user_a
        )

        # Index document for User B
        chunks_user_b = [{
            "text": "User B proprietary engineering blueprint specs.",
            "page": 1
        }]
        self.vector_service.add_chunks(
            user_id=self.user_b_id,
            document_id="doc_user_b_001",
            file_name="user_b_specs.pdf",
            doc_type="PDF",
            chunks=chunks_user_b
        )

        # User A searches for User B's content -> MUST return empty
        results_a = self.vector_service.search(
            user_id=self.user_a_id,
            query="engineering blueprint specs"
        )
        for res in results_a:
            self.assertEqual(res['user_id'], self.user_a_id)
            self.assertNotIn("User B proprietary", res['content'])

        # User B searches for User A's content -> MUST return empty
        results_b = self.vector_service.search(
            user_id=self.user_b_id,
            query="confidential secret financial record"
        )
        for res in results_b:
            self.assertEqual(res['user_id'], self.user_b_id)
            self.assertNotIn("User A confidential", res['content'])
