import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vectorstore.chroma_service import chroma_service

def main():
    print("=== ChromaDB Vector Store Initialization ===")
    print(f"Persist Directory: {chroma_service.persist_dir}")
    print(f"Collection Name: {chroma_service.collection.name}")
    print(f"Current Total Chunks: {chroma_service.get_count()}")
    print("ChromaDB persistent store is initialized and operational.")
    print("===========================================")

if __name__ == '__main__':
    main()
