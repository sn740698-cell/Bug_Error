import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import IngestedDocument, AgentExecutionLog
from api.services.vectorstore import ChromaVectorStoreService

print("Resetting database...")

# 1. Clear relational models
IngestedDocument.objects.all().delete()
AgentExecutionLog.objects.all().delete()
print("Cleared SQLite IngestedDocument and AgentExecutionLog models.")

# 2. Clear ChromaDB collection
try:
    vector_service = ChromaVectorStoreService()
    if vector_service.collection is not None:
        try:
            vector_service.client.delete_collection(vector_service.collection_name)
            print(f"Deleted ChromaDB collection '{vector_service.collection_name}'.")
        except Exception as e:
            print(f"Collection delete notice: {e}")
        
        # Re-initialize collection
        vector_service.collection = vector_service.client.get_or_create_collection(
            name=vector_service.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("Re-created clean ChromaDB vector store collection.")
except Exception as e:
    print(f"ChromaDB reset error: {e}")

print("Database reset complete!")
