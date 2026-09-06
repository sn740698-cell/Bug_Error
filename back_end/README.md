# Multi-Agent Financial Document Intelligence Platform Backend

A modular, production-oriented backend for an AI-powered financial document analysis and balance-due notification platform.

## Architecture

- **Django REST Framework**: REST API endpoints for document upload, workflow management, and system health.
- **LangGraph**: Multi-supervisor state graph (`FinancialSupervisor` & `CommunicationSupervisor`) coordinating specialized agents (`DataAnalyzerAgent`, `RetrievalAgent`, `TextingAgent`, `DraftValidationAgent`).
- **Ollama GGUF Inference**: `OllamaService` & `LLMRouter` executing local GGUF models (**Llama 3.2 1B** and **Qwen 2.5 1B**) with memory pinning (`keep_alive`).
- **BERT & DistilBERT**: Lazy-loaded Hugging Face BERT for contextual sentence/entity analysis, and DistilBERT for 2-stage semantic similarity candidate filtering (`threshold >= 0.70`).
- **ChromaDB**: Persistent vector database storing document chunks and embeddings.
- **Celery & Redis**: Asynchronous background workflow execution.

---

## 🛠️ Quick Start

### 1. Environment Setup
```cmd
cd back_end
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Migrations & Initial Checks
```cmd
python manage.py migrate
python scripts/check_models.py
python scripts/initialize_chroma.py
```

### 3. Run Backend Server
```cmd
python manage.py runserver 127.0.0.1:8000
```

---

## 📡 REST API Endpoints

- **`POST /api/documents/upload/`**: Upload PDF/DOCX/TXT file, extract text, chunk, and index into ChromaDB.
- **`POST /api/workflows/analyze/`**: Trigger multi-agent LangGraph workflow.
- **`GET /api/workflows/{workflow_id}/`**: Get workflow progress & status.
- **`GET /api/workflows/{workflow_id}/insights/`**: Retrieve structured financial field extractions.
- **`GET /api/workflows/{workflow_id}/draft/`**: Retrieve validated balance-due notification draft.
- **`POST /api/workflows/{workflow_id}/regenerate/`**: Re-run notification draft generation.
- **`GET /api/health/`**: Health status of Django, Ollama, ChromaDB, and GPU VRAM.

---

## 🐳 Docker Deployment

```cmd
docker-compose up --build
```
