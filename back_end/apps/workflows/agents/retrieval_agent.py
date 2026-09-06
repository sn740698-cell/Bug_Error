import logging
from typing import Any
from apps.workflows.state import WorkflowState, RetrievedContextState
from apps.vectorstore.retrieval import vector_retrieval_service

logger = logging.getLogger(__name__)

class VectorKnowledgeRetrievalAgent:
    """
    Vector Knowledge Retrieval Agent (formerly RetrievalAgent):
    Retrieves relevant financial document chunks using 2-stage ChromaDB + DistilBERT filtering.
    """

    def retrieve(self, state: WorkflowState) -> dict[str, Any]:
        """Perform semantic retrieval based on current workflow state & missing fields."""
        missing_fields = []
        for ins in state.financial_insights:
            if ins.value is None or ins.confidence < 0.70:
                missing_fields.append(ins.field_name)

        if missing_fields:
            query = f"Financial details for invoice balance due total amount customer due date missing {', '.join(missing_fields)}"
        else:
            query = "Invoice balance due total amount payment terms customer vendor due date"

        logger.info(f"VectorKnowledgeRetrievalAgent: Executing context retrieval for query: '{query}'")

        # Perform 2-stage vector retrieval & DistilBERT filtering
        results = vector_retrieval_service.retrieve_financial_context(query=query)

        context_states = []
        for item in results:
            context_states.append(
                RetrievedContextState(
                    chunk_id=item.get("chunk_id", ""),
                    document_id=item.get("document_id", ""),
                    text=item.get("text", ""),
                    similarity_score=item.get("similarity_score", 0.0),
                    metadata=item.get("metadata", {})
                )
            )

        logger.info(f"VectorKnowledgeRetrievalAgent: Retained {len(context_states)} relevant context chunks.")
        return {
            "retrieved_context": context_states,
            "retrieval_attempts": state.retrieval_attempts + 1,
            "current_agent": "vector_retrieval_agent"
        }

vector_knowledge_retrieval_agent = VectorKnowledgeRetrievalAgent()
# Backward compatibility alias
retrieval_agent = vector_knowledge_retrieval_agent
