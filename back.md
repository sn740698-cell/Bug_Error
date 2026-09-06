# Backend Architecture & System Specification (`back.md`)

This document provides a comprehensive technical specification and architectural breakdown of the **Django REST + LangGraph + Ollama GGUF + ChromaDB** backend for the **J.A.R.V.I.S. Universal Multi-Agent AI Intelligence Platform**.

---

## 🏛️ System Architecture Overview

```
                      +----------------------------------+
                      |     React Frontend Dashboard     |
                      +----------------------------------+
                                       |
                                       v
                      +----------------------------------+
                      |       Django REST API Layer      |
                      |    (apps/workflows_api/views)    |
                      +----------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
    +------------------------------+       +------------------------------+
    |   ChromaDB Vector Store      |       |  LangGraph StateGraph        |
    |   + DistilBERT Re-ranking    |       |  5-Agent Multi-Supervisor    |
    +------------------------------+       +------------------------------+
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                      +----------------------------------+
                      |      Ollama LLMRouter (GGUF)     |
                      |   Primary: Llama 3.2 1B Instruct |
                      |   Fallback: Qwen 2.5 1B Instruct |
                      +----------------------------------+
```

---

## 🛠️ Technology Stack & Dependencies

- **Framework**: Django 5.x + Django REST Framework
- **Orchestration**: LangGraph (`StateGraph`, `CompiledGraph`)
- **Primary LLM**: Ollama GGUF (`Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0`)
- **Secondary Fallback LLM**: Ollama GGUF (`Qwen2.5-1B-Instruct-Q8_0-GGUF:Q8_0`)
- **Vector Database**: ChromaDB (Local Persistent Storage)
- **Re-ranking Model**: HuggingFace DistilBERT (`distilbert-base-uncased`)
- **Database**: SQLite (Development / Production DB)

---

## 📁 Backend Directory & Directory Structure

```text
back_end/
├── api/                        # General API utilities & health endpoints
├── apps/
│   ├── ai/                     # LLM & Embedding services
│   │   ├── distilbert_service.py # 2-Stage DistilBERT contextual re-ranking
│   │   ├── llm_router.py       # LLM selection & automatic fallback router
│   │   ├── ollama_service.py   # Ollama API client & output filter
│   │   └── gpu_manager.py      # Memory & device execution manager
│   ├── documents/              # File ingestion, OCR, and text extraction
│   │   ├── models.py           # Document model
│   │   ├── services.py         # PDF / DOCX / TXT text extraction service
│   │   └── views.py            # POST /api/documents/upload/
│   ├── health/                 # GPU, Ollama, VectorStore health diagnostics
│   ├── vectorstore/            # ChromaDB interface
│   │   ├── chroma_service.py   # ChromaDB collection initialization
│   │   ├── embeddings.py       # SentenceTransformers embedding generation
│   │   └── retrieval.py        # Two-stage vector retrieval pipeline
│   ├── workflows/              # LangGraph multi-agent core
│   │   ├── agents/
│   │   │   ├── decomposer_agent.py          # 1. Structural Section Decomposer
│   │   │   ├── retrieval_agent.py           # 2. Vector Retrieval Agent
│   │   │   ├── simplifier_agent.py          # 3. Layman Simplifier Agent
│   │   │   ├── texting_agent.py             # 4. Executive Summary Drafter Agent
│   │   │   ├── validation_agent.py          # 5. Fact Verification Agent
│   │   │   └── hallucination_audit_agent.py # 6. Real-time NLI Hallucination Auditor
│   │   ├── supervisors/
│   │   │   ├── financial_supervisor.py      # Master Orchestrator Supervisor
│   │   │   └── communication_supervisor.py  # Communication Orchestrator Supervisor
│   │   ├── graph.py            # LangGraph StateGraph compilation
│   │   ├── reducers.py         # State append & merge reducers
│   │   └── state.py            # WorkflowState & Shared Memory Pydantic Models
│   └── workflows_api/          # REST API Controllers & Background Tasks
│       ├── models.py           # Workflow, DocumentInsight, GeneratedDraft models
│       ├── serializers.py      # DRF Serializers
│       ├── tasks.py            # Background thread workflow execution
│       ├── urls.py             # URL route definitions
│       └── views.py            # API View classes
├── config/                     # Django settings, ASGI/WSGI, Celery config
│   ├── settings.py             # Global settings & AI thresholds
│   └── urls.py                 # Master URL routing
├── manage.py                   # Django management script
└── requirements.txt            # Python dependencies
```

---

## 🧠 5-Agent Anti-Hallucination & Verification Framework

All 5 agents operate on a **unified shared memory state** (`WorkflowState`), sharing 4 structural document sections and canonical ground-truth facts:

### 1. 📑 `DocumentDecomposerAgent` (`apps/workflows/agents/decomposer_agent.py`)
- **Role**: Partitions any document into 4 structural sections (`title_header`, `core_details`, `key_topics`, `action_items`).
- **Fact Extraction**: Dynamically extracts universal document facts (`document_title`, `primary_entity_or_author`, `document_category`, `contact_or_location`, `primary_skills_or_domain`, `key_highlights`, `action_items`).

### 2. 📚 `VectorKnowledgeRetrievalAgent` (`apps/workflows/agents/retrieval_agent.py`)
- **Role**: Performs 2-stage retrieval.
- **Stage 1**: Fetches top candidates from ChromaDB.
- **Stage 2**: Applies DistilBERT cross-encoder scoring to filter out irrelevant chunks.

### 3. 📝 `LaymanSimplifierAgent` (`apps/workflows/agents/simplifier_agent.py`)
- **Role**: Converts complex technical/general documents into a 3-5 bullet point plain-English summary.
- **Constraint**: Strict context grounding to avoid inventing false statements or monetary figures.

### 4. ✍️ `ExecutiveSummaryDrafterAgent` (`apps/workflows/agents/texting_agent.py`)
- **Role**: Synthesizes a structured **Executive Summary & Action Plan Draft** based on extracted document facts.

### 5. ✅ `FactVerificationAgent` (`apps/workflows/agents/validation_agent.py`)
- **Role**: Validates that generated executive summary drafts correctly state primary author/entity names, document titles, and factual details.
- **Retry Mechanism**: Rejects invalid drafts for regeneration up to `MAX_DRAFT_RETRIES`.

### 6. 🛡️ `HallucinationAuditAgent` (`apps/workflows/agents/hallucination_audit_agent.py`)
- **Role**: Real-time NLI cross-verification guardrail agent that audits LLM drafts and Chatbot answers against ground-truth facts prior to returning responses to the user.

---

## ⚡ REST API Endpoints & Request/Response Contracts

### 1. Health Check
- **`GET /api/health/`**
- **Response**:
  ```json
  {
    "status": "healthy",
    "ollama": { "connected": true, "llama_model": "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0" },
    "vectorstore": { "indexed_chunks": 14 }
  }
  ```

### 2. Document Upload & Indexing
- **`POST /api/documents/upload/`** (multipart/form-data)
- **Response**:
  ```json
  {
    "message": "Document uploaded and indexed into vector store",
    "document": { "id": "uuid", "filename": "sample.pdf", "status": "INDEXED" },
    "chunk_count": 5
  }
  ```

### 3. Workflow Analysis Execution
- **`POST /api/workflows/analyze/`**
- **Payload**: `{"document_id": "uuid"}`
- **Response**: `{"message": "Workflow analysis initiated", "workflow_id": "uuid", "status": "PENDING"}`

### 4. Workflow Status & Section Breakdown
- **`GET /api/workflows/{workflow_id}/`**
- **Response**: Returns live status, active supervisor, current agent, document sections, and routing decisions.

### 5. Extracted Insights & Facts
- **`GET /api/workflows/{workflow_id}/insights/`**
- **Response**: List of extracted key insights with confidence scores and source attribution.

### 6. Executive Summary Draft
- **`GET /api/workflows/{workflow_id}/draft/`**
- **Response**: Synthesized draft text, LLM model used, attempt count, and validation status (`PASS`).

### 7. Interactive & General Chatbot
- **`POST /api/workflows/{workflow_id_or_general}/chat/`**
- **Payload**: `{"question": "Who is the author and what are the core modules?"}`
- **Response**:
  ```json
  {
    "workflow_id": "uuid",
    "question": "Who is the author and what are the core modules?",
    "answer": "The author of the proposal is Suraj M N. The core modules are...",
    "llm_model": "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0",
    "hallucination_verified": true,
    "sources": ["chk_1", "chk_2"]
  }
  ```

---

## ⚡ Performance Optimizations

1. **Instant Greeting Fast-Path**: Simple conversational greetings (`"hi"`, `"hello"`, `"hi buddy"`, `"hey"`) return instant responses (0ms).
2. **Ollama Acceleration Parameters**:
   - `num_predict: 384` (Limits max predicted tokens for fast response termination)
   - `num_ctx: 2048` (4x faster attention calculation on CPU)
   - `stop: ["<|eot_id|>", "<|im_end|>", "User:", "Question:"]` (Prevents lingering loops)
   - `keep_alive: "60m"` (Keeps model resident in RAM/VRAM)

---

## 🚀 How to Run the Backend

```cmd
cd back_end
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
Or launch both frontend and backend using `run.bat`.
