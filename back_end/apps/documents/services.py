import os
import uuid
import logging
from pathlib import Path
from django.conf import settings
from .models import Document, DocumentChunk
from apps.vectorstore.chroma_service import chroma_service

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Handles document file validation, text extraction, cleaning, chunking, and ChromaDB vector indexing."""

    def extract_text_from_file(self, file_path: str, file_type: str) -> tuple[str, list[dict]]:
        """Extract text content and page-wise chunks from PDF, DOCX, or TXT file."""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found at {file_path}")

        full_text = ""
        page_chunks = []

        if file_type.lower() in ['pdf', 'application/pdf']:
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        full_text += f"\n--- Page {idx+1} ---\n" + text
                        page_chunks.append({"page_number": idx+1, "text": text.strip()})
            except Exception as pdf_err:
                logger.warning(f"pypdf extraction failed ({pdf_err}), attempting plain text read.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    txt = f.read()
                    full_text = txt
                    page_chunks.append({"page_number": 1, "text": txt})

        elif file_type.lower() in ['docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            try:
                import docx
                doc = docx.Document(file_path)
                paras = [p.text for p in doc.paragraphs if p.text.strip()]
                full_text = "\n".join(paras)
                page_chunks.append({"page_number": 1, "text": full_text})
            except Exception as docx_err:
                logger.error(f"DOCX extraction error: {docx_err}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    txt = f.read()
                    full_text = txt
                    page_chunks.append({"page_number": 1, "text": txt})

        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                full_text = f.read()
                page_chunks.append({"page_number": 1, "text": full_text})

        return full_text, page_chunks

    def chunk_text(self, document_id: str, page_chunks: list[dict], chunk_size: int = 500) -> list[dict]:
        """Split text into 500-character chunks with page attribution."""
        chunks = []
        for page_data in page_chunks:
            text = page_data.get('text', '')
            page_num = page_data.get('page_number', 1)
            
            # Simple paragraph/sliding window chunking
            words = text.split()
            current_chunk = []
            current_len = 0

            for word in words:
                current_chunk.append(word)
                current_len += len(word) + 1
                if current_len >= chunk_size:
                    chunk_text = " ".join(current_chunk)
                    chk_id = f"chk_{document_id[:8]}_{len(chunks)+1}_{uuid.uuid4().hex[:4]}"
                    chunks.append({
                        "chunk_id": chk_id,
                        "document_id": str(document_id),
                        "page_number": page_num,
                        "text": chunk_text
                    })
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chk_id = f"chk_{document_id[:8]}_{len(chunks)+1}_{uuid.uuid4().hex[:4]}"
                chunks.append({
                    "chunk_id": chk_id,
                    "document_id": str(document_id),
                    "page_number": page_num,
                    "text": chunk_text
                })

        return chunks

    def process_and_index_document(self, document: Document) -> tuple[str, int]:
        """Full pipeline: extract text, save chunks to DB, index into ChromaDB."""
        document.status = 'PROCESSING'
        document.save()

        try:
            full_text, page_chunks = self.extract_text_from_file(document.file_path, document.file_type)
            chunks = self.chunk_text(str(document.id), page_chunks)

            # Store chunks in relational database
            for chunk_data in chunks:
                DocumentChunk.objects.create(
                    document=document,
                    chunk_id=chunk_data['chunk_id'],
                    page_number=chunk_data['page_number'],
                    chunk_text=chunk_data['text']
                )

            # Ingest into persistent ChromaDB vector store
            chroma_service.add_chunks(str(document.id), chunks)

            document.status = 'INDEXED'
            document.save()
            return full_text, len(chunks)

        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {e}")
            document.status = 'FAILED'
            document.save()
            raise e

document_processing_service = DocumentProcessingService()
