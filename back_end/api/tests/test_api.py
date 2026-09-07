from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
import json


class APITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertIn('vectorstore', data)
        self.assertIn('llm_providers', data)

    def test_pipeline_run_valid_multipart_request(self):
        sample_txt = SimpleUploadedFile(
            "requirements.txt",
            b"System design requirement: sub-100ms API response latency.",
            content_type="text/plain"
        )
        post_data = {
            'name': 'Alex Mercer',
            'email': 'alex.mercer@innovate.org',
            'section': 'Distributed Systems & Cloud Architecture',
            'query': 'Design a geo-distributed low-latency consensus protocol for banking ledger transactions with zero data loss.',
            'files': [sample_txt]
        }

        response = self.client.post('/api/pipeline/run/', post_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertIsNotNone(data.get('execution_id'))
        self.assertTrue(data.get('evaluation_passed'))
        self.assertIsNotNone(data.get('solution'))
        self.assertIn('hallucination_audit', data)

    def test_pipeline_run_validation_error_empty_query(self):
        post_data = {
            'name': 'Alex Mercer',
            'email': 'alex.mercer@innovate.org',
            'query': '   '
        }
        response = self.client.post('/api/pipeline/run/', post_data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('status'), 'error')
        self.assertEqual(data.get('code'), 'VALIDATION_ERROR')

    def test_pipeline_run_unsupported_file_extension(self):
        unsupported_file = SimpleUploadedFile(
            "script.sh",
            b"#!/bin/bash\necho hello",
            content_type="application/x-sh"
        )
        post_data = {
            'name': 'Alex Mercer',
            'email': 'alex.mercer@innovate.org',
            'query': 'Analyze script security.',
            'files': [unsupported_file]
        }
        response = self.client.post('/api/pipeline/run/', post_data)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('status'), 'error')
        self.assertIn('files', str(data.get('details')))
