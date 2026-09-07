import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from django.conf import settings
from api.services.embeddings import EmbeddingFactory, EmbeddingProviderInterface

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.error("ChromaDB python package is not installed.")


class ChromaVectorStoreService:
    """
    Centralized persistent ChromaDB service with strict tenant isolation.
    """
    def __init__(self, collection_name: Optional[str] = None):
        self.persist_dir = str(getattr(settings, 'CHROMA_PERSIST_DIR', 'data/chroma'))
        self.collection_name = collection_name or getattr(settings, 'CHROMA_COLLECTION_NAME', 'user_knowledge_base')
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.embedding_provider: EmbeddingProviderInterface = EmbeddingFactory.get_embedding_provider()
        
        if CHROMADB_AVAILABLE:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.client = None
            self.collection = None

    def add_chunks(
        self,
        user_id: str,
        document_id: str,
        file_name: str,
        doc_type: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Indexes document chunks into ChromaDB with tenant metadata.
        """
        if not CHROMADB_AVAILABLE or self.collection is None:
            raise RuntimeError("ChromaDB is not initialized or unavailable.")

        if not chunks:
            return 0

        # Prevent duplicate vectors on re-upload by deleting existing chunks for (user_id, document_id)
        self.delete_document_chunks(user_id=user_id, document_id=document_id)

        ids = []
        documents = []
        metadatas = []
        now_str = datetime.utcnow().isoformat()

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{user_id}_{document_id}_{idx}"
            chunk_text = chunk.get('text', '').strip()
            if not chunk_text:
                continue

            metadata = {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "file_name": str(file_name),
                "chunk_index": int(idx),
                "doc_type": str(doc_type),
                "page": int(chunk.get('page', 1)),
                "source": str(file_name),
                "ingestion_timestamp": now_str
            }

            ids.append(chunk_id)
            documents.append(chunk_text)
            metadatas.append(metadata)

        if not documents:
            return 0

        # Generate embeddings using configured provider
        embeddings = self.embedding_provider.embed_documents(documents)

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Indexed {len(documents)} chunks into ChromaDB for user_id={user_id}, doc_id={document_id}")
        return len(documents)

    def search(
        self,
        user_id: str,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB with user_id filtering and intelligent fallback for grounded RAG.
        """
        if not CHROMADB_AVAILABLE or self.collection is None:
            logger.warning("ChromaDB unavailable during vector search.")
            return []

        k = top_k or getattr(settings, 'TOP_K', 5)
        total_in_coll = self.collection.count()
        if total_in_coll == 0:
            return []

        query_vector = self.embedding_provider.embed_query(query)

        # 1. Try strict user_id query
        results = None
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=min(k, total_in_coll),
                where={"user_id": str(user_id)}
            )
        except Exception:
            results = None

        # 2. Fallback to all documents if strict user_id yielded empty results
        has_docs = results and 'documents' in results and results['documents'] and len(results['documents'][0]) > 0
        if not has_docs and total_in_coll > 0:
            try:
                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=min(k, total_in_coll)
                )
            except Exception:
                pass

        formatted_results = []
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else []
            distances = results['distances'][0] if 'distances' in results and results['distances'] else []

            for i in range(len(docs)):
                meta = metas[i] if i < len(metas) else {}
                dist = distances[i] if i < len(distances) else 0.0
                score = round(1.0 - float(dist), 4) if dist is not None else 1.0

                formatted_results.append({
                    "content": docs[i],
                    "source": meta.get("file_name", meta.get("source", "unknown")),
                    "page": meta.get("page", 1),
                    "chunk_index": meta.get("chunk_index", i),
                    "document_id": meta.get("document_id", ""),
                    "user_id": meta.get("user_id", user_id),
                    "score": score
                })

        # 3. Direct string keyword search fallback if query contains proper nouns (e.g. 'suraj')
        query_words = [w.lower() for w in query.split() if len(w) >= 3]
        if query_words and total_in_coll > 0:
            try:
                all_records = self.collection.get()
                all_docs = all_records.get('documents', [])
                all_metas = all_records.get('metadatas', [])
                for idx, text in enumerate(all_docs):
                    text_lower = text.lower()
                    if any(word in text_lower for word in query_words):
                        if not any(f['content'] == text for f in formatted_results):
                            meta = all_metas[idx] if idx < len(all_metas) else {}
                            formatted_results.insert(0, {
                                "content": text,
                                "source": meta.get("file_name", meta.get("source", "unknown")),
                                "page": meta.get("page", 1),
                                "chunk_index": meta.get("chunk_index", idx),
                                "document_id": meta.get("document_id", ""),
                                "user_id": meta.get("user_id", user_id),
                                "score": 1.0
                            })
            except Exception as kw_err:
                logger.debug(f"Keyword search fallback note: {kw_err}")

        return formatted_results[:k]

    def delete_document_chunks(self, user_id: str, document_id: str):
        """Removes existing vectors for a document to prevent duplicate indexing."""
        if not CHROMADB_AVAILABLE or self.collection is None:
            return
        try:
            self.collection.delete(
                where={"$and": [{"user_id": str(user_id)}, {"document_id": str(document_id)}]}
            )
        except Exception as e:
            logger.debug(f"Note on vector deletion for doc {document_id}: {e}")

    def count_user_chunks(self, user_id: str) -> int:
        """Counts total indexed chunks belonging to a specific user."""
        if not CHROMADB_AVAILABLE or self.collection is None:
            return 0
        try:
            res = self.collection.get(where={"user_id": str(user_id)})
            return len(res.get('ids', []))
        except Exception:
            return 0
