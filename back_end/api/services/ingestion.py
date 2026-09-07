import os
import io
import time
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path

from django.conf import settings
from api.models import UserProfile, IngestedDocument
from api.services.vectorstore import ChromaVectorStoreService

logger = logging.getLogger(__name__)

# Recursive character text splitter implementation
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []

        final_chunks = []
        # Find best separator
        separator = self.separators[-1]
        for s in self.separators:
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                break

        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        good_splits = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                sub_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=self.separators[1:] if len(self.separators) > 1 else self.separators
                )
                final_chunks.extend(sub_splitter.split_text(s))

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return [c.strip() for c in final_chunks if c.strip()]

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        docs = []
        current_doc = []
        total = 0
        for s in splits:
            len_s = len(s)
            if total + len_s + (len(separator) if current_doc else 0) > self.chunk_size:
                if current_doc:
                    doc = separator.join(current_doc)
                    if doc.strip():
                        docs.append(doc)
                    # Overlap handling
                    while total > self.chunk_overlap and current_doc:
                        removed = current_doc.pop(0)
                        total -= len(removed) + len(separator)
            current_doc.append(s)
            total += len_s + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            doc = separator.join(current_doc)
            if doc.strip():
                docs.append(doc)
        return docs


class DocumentIngestionService:
    def __init__(self):
        self.vector_service = ChromaVectorStoreService()
        self.chunk_size = getattr(settings, 'CHUNK_SIZE', 1000)
        self.chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 150)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def extract_text_from_file(self, file_name: str, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts structured text items with page metadata from supported file formats.
        Returns a list of dicts: [{'text': str, 'page': int}, ...]
        """
        ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        pages_content = []

        if ext == '.pdf':
            pages_content = self._extract_pdf(file_bytes)
        elif ext == '.docx':
            pages_content = self._extract_docx(file_bytes)
        elif ext == '.doc':
            # Explicitly reject legacy binary .doc format with informative validation error
            raise ValueError(
                f"Legacy Microsoft Word format (.doc) for file '{file_name}' is not supported directly. "
                "Please convert the file to modern .docx or plain text (.txt) before uploading."
            )
        elif ext == '.csv':
            pages_content = self._extract_csv(file_bytes)
        elif ext == '.txt':
            pages_content = self._extract_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file format '{ext}' for file '{file_name}'.")

        return pages_content

    def _extract_pdf(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        results = []
        # 1. Try pymupdf / fitz
        try:
            import pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                text = doc[page_num].get_text()
                if text and text.strip():
                    results.append({"text": text.strip(), "page": page_num + 1})
            doc.close()
            if results:
                return results
        except Exception as e:
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page_num in range(len(doc)):
                    text = doc[page_num].get_text()
                    if text and text.strip():
                        results.append({"text": text.strip(), "page": page_num + 1})
                doc.close()
                if results:
                    return results
            except Exception:
                pass

        # 2. Try pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    results.append({"text": text.strip(), "page": idx + 1})
            if results:
                return results
        except Exception as e:
            logger.debug(f"pypdf extraction note: {e}")

        # 3. Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        results.append({"text": text.strip(), "page": idx + 1})
            if results:
                return results
        except Exception as e:
            logger.debug(f"pdfplumber extraction note: {e}")

        return results

    def _extract_docx(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text and paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            joined = "\n\n".join(full_text)
            return [{"text": joined, "page": 1}] if joined else []
        except Exception as e:
            logger.error(f"Error parsing DOCX file: {e}")
            raise ValueError(f"Failed to parse DOCX file: {str(e)}")

    def _extract_csv(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(file_bytes))

            rows_formatted = []
            headers = [str(c) for c in df.columns]

            for idx, row in df.iterrows():
                row_str = f"Row {idx + 1}: " + ", ".join(f"{h}={row[h]}" for h in headers if pd.notna(row[h]))
                rows_formatted.append(row_str)

            # Group rows into manageable chunks of ~50 rows per pseudo-page
            chunk_size_rows = 50
            results = []
            for i in range(0, len(rows_formatted), chunk_size_rows):
                batch = "\n".join(rows_formatted[i:i + chunk_size_rows])
                results.append({"text": batch, "page": (i // chunk_size_rows) + 1})

            return results
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            # Fallback to python csv reader if pandas encounters formatting issues
            import csv
            content_str = file_bytes.decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(content_str))
            rows = list(reader)
            if not rows:
                return []
            header = rows[0]
            rows_formatted = []
            for idx, r in enumerate(rows[1:]):
                row_str = f"Row {idx + 1}: " + ", ".join(f"{header[j]}={r[j]}" for j in range(min(len(header), len(r))))
                rows_formatted.append(row_str)
            joined = "\n".join(rows_formatted)
            return [{"text": joined, "page": 1}] if joined else []

    def _extract_txt(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            text = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = file_bytes.decode('latin-1', errors='ignore')

        text = text.strip()
        return [{"text": text, "page": 1}] if text else []

    def ingest_files(
        self,
        user: UserProfile,
        files: List[Tuple[str, bytes]]
    ) -> Dict[str, Any]:
        """
        Ingests uploaded files into relational database and persistent vector database.
        Returns detailed ingestion statistics.
        """
        start_time = time.time()
        file_count = len(files)
        total_chunks_created = 0
        chunks_skipped = 0
        failures = []
        ingested_docs = []

        user_upload_dir = Path(settings.MEDIA_ROOT) / 'documents' / str(user.id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        for file_name, file_bytes in files:
            ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
            file_type = ext.replace('.', '').upper() or 'TXT'

            # Save file to disk
            saved_file_path = user_upload_dir / file_name
            with open(saved_file_path, 'wb') as f:
                f.write(file_bytes)

            # Create IngestedDocument DB record in PENDING state
            doc_record = IngestedDocument.objects.create(
                user=user,
                original_file_name=file_name,
                normalized_file_type=file_type,
                stored_file_path=str(saved_file_path),
                chroma_collection_name=self.vector_service.collection_name,
                total_chunks=0,
                ingestion_status='PENDING'
            )

            try:
                pages = self.extract_text_from_file(file_name, file_bytes)
                all_chunks = []

                for page_obj in pages:
                    page_num = page_obj['page']
                    raw_text = page_obj['text']
                    split_texts = self.splitter.split_text(raw_text)

                    for text_chunk in split_texts:
                        all_chunks.append({
                            'text': text_chunk,
                            'page': page_num
                        })

                if not all_chunks:
                    doc_record.ingestion_status = 'INDEXED'
                    doc_record.total_chunks = 0
                    doc_record.save()
                    chunks_skipped += 1
                    ingested_docs.append(doc_record)
                    continue

                # Dual-write: Index chunks into ChromaDB with tenant metadata
                indexed_count = self.vector_service.add_chunks(
                    user_id=str(user.id),
                    document_id=str(doc_record.id),
                    file_name=file_name,
                    doc_type=file_type,
                    chunks=all_chunks
                )

                doc_record.total_chunks = indexed_count
                doc_record.ingestion_status = 'INDEXED'
                doc_record.save()

                total_chunks_created += indexed_count
                ingested_docs.append(doc_record)

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to ingest file '{file_name}': {error_msg}")
                doc_record.ingestion_status = 'FAILED'
                doc_record.error_message = error_msg
                doc_record.save()

                failures.append({
                    "file_name": file_name,
                    "error": error_msg
                })

        duration = round(time.time() - start_time, 3)

        return {
            "file_count": file_count,
            "chunks_created": total_chunks_created,
            "chunks_skipped": chunks_skipped,
            "failures": failures,
            "processing_duration": duration,
            "documents": [str(d.id) for d in ingested_docs]
        }
