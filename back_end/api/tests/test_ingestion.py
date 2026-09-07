from django.test import TestCase
from api.services.ingestion import DocumentIngestionService, RecursiveCharacterTextSplitter


class IngestionTests(TestCase):
    def setUp(self):
        self.service = DocumentIngestionService()

    def test_txt_extraction(self):
        content = "System architecture documentation.\nLine 2 info.".encode('utf-8')
        pages = self.service.extract_text_from_file("sample.txt", content)
        self.assertEqual(len(pages), 1)
        self.assertIn("System architecture documentation", pages[0]['text'])

    def test_csv_extraction(self):
        csv_content = "id,name,value\n1,Alpha,100\n2,Beta,200".encode('utf-8')
        pages = self.service.extract_text_from_file("data.csv", csv_content)
        self.assertTrue(len(pages) >= 1)
        self.assertIn("name=Alpha", pages[0]['text'])

    def test_legacy_doc_rejection(self):
        dummy_bytes = b"fake binary doc content"
        with self.assertRaises(ValueError) as ctx:
            self.service.extract_text_from_file("legacy.doc", dummy_bytes)
        self.assertIn(".doc", str(ctx.exception))
        self.assertIn("not supported directly", str(ctx.exception))

    def test_unsupported_format_rejection(self):
        dummy_bytes = b"executable data"
        with self.assertRaises(ValueError) as ctx:
            self.service.extract_text_from_file("malicious.exe", dummy_bytes)
        self.assertIn("Unsupported file format", str(ctx.exception))

    def test_recursive_character_text_splitter(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        sample_text = "Paragraph 1 is about distributed consensus protocols.\n\nParagraph 2 is about database replication and storage engines."
        chunks = splitter.split_text(sample_text)
        self.assertTrue(len(chunks) >= 2)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 70)
