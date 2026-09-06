import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
from django.conf import settings
import chromadb

logger = logging.getLogger(__name__)

class ChromaService:
    """
    Persistent ChromaDB vector database service.
    Stores document chunks, embeddings, and metadata (document_id, chunk_id, page_number, invoice_number, document_type, source, created_at).
    """

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="financial_documents_v2"
        )
        logger.info(f"ChromaDB service initialized at {self.persist_dir} (Collection: financial_documents_v2)")

    def add_chunks(self, document_id: str, chunks: list[dict[str, Any]]) -> list[str]:
        """
        Ingest document text chunks into ChromaDB with structured metadata.
        """
        if not chunks:
            return []

        ids = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get('chunk_id') or f"{document_id}_chk_{idx+1}_{uuid.uuid4().hex[:6]}"
            ids.append(chunk_id)
            documents.append(chunk.get('text', ''))
            
            meta = {
                "document_id": str(document_id),
                "chunk_id": str(chunk_id),
                "page_number": int(chunk.get('page_number', 1)),
                "invoice_number": str(chunk.get('invoice_number', '')),
                "document_type": str(chunk.get('document_type', 'financial_invoice')),
                "source": str(chunk.get('source', 'upload')),
                "created_at": datetime.utcnow().isoformat()
            }
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} chunks to ChromaDB for document {document_id}")
        return ids

    def query(self, query_text: str, top_k: int = 10, filter_metadata: dict = None) -> list[dict[str, Any]]:
        """
        Perform vector similarity search in ChromaDB returning candidate chunks.
        """
        try:
            if self.collection.count() == 0:
                return []

            kwargs = {
                "query_texts": [query_text],
                "n_results": min(top_k, max(1, self.collection.count()))
            }
            if filter_metadata:
                kwargs["where"] = filter_metadata

            results = self.collection.query(**kwargs)

            candidates = []
            if results and 'documents' in results and results['documents']:
                docs = results['documents'][0]
                ids = results['ids'][0] if 'ids' in results else []
                metas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else []
                distances = results['distances'][0] if 'distances' in results and results['distances'] else []

                for i in range(len(docs)):
                    dist = distances[i] if i < len(distances) else 0.5
                    # Convert distance to normalized similarity score (0.0 to 1.0)
                    sim_score = max(0.0, min(1.0, round(1.0 - (dist / 2.0 if dist > 1.0 else dist), 4)))
                    
                    candidates.append({
                        "chunk_id": ids[i] if i < len(ids) else f"chk_{i}",
                        "document_id": metas[i].get("document_id", "") if i < len(metas) else "",
                        "text": docs[i],
                        "similarity_score": sim_score,
                        "metadata": metas[i] if i < len(metas) else {}
                    })

            return candidates
        except Exception as e:
            logger.warning(f"ChromaDB query returned fallback empty result: {e}")
            return []

    def get_count(self) -> int:
        """Return total document chunks in ChromaDB."""
        return self.collection.count()

chroma_service = ChromaService()
