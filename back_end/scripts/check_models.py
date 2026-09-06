import sys
import os
from pathlib import Path

# Add parent directory to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ai.ollama_service import ollama_service
from apps.ai.gpu_manager import gpu_manager

def main():
    print("=== Model & Environment Check ===")
    print("GPU Info:", gpu_manager.get_vram_usage())
    
    print("\nOllama Connection Check...")
    models = ollama_service.list_models()
    print("Available Ollama Models:", models)
    
    qwen_ok = ollama_service.is_model_available(ollama_service.qwen_model)
    llama_ok = ollama_service.is_model_available(ollama_service.llama_model)
    
    print(f"Qwen Model ({ollama_service.qwen_model}): {'READY' if qwen_ok else 'MISSING'}")
    print(f"Llama Model ({ollama_service.llama_model}): {'READY' if llama_ok else 'MISSING'}")
    print("================================")

if __name__ == '__main__':
    main()
