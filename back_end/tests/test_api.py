from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.documents.models import Document
from apps.workflows_api.models import Workflow

class RESTAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.document = Document.objects.create(
            filename="test_invoice.pdf",
            file_path="data/documents/test_invoice.pdf",
            file_type="pdf",
            file_size=1024,
            status="INDEXED"
        )

    def test_health_check_api(self):
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_workflow_analyze_api(self):
        url = reverse('workflow_analyze')
        response = self.client.post(url, {'document_id': str(self.document.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('workflow_id', response.data)
