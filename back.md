# Backend Architecture & System Upgrades (`back.md`)

This document provides a comprehensive technical specification and architectural breakdown of the **Django 5.x REST + LangGraph 8-Agent StateGraph + Ollama Llama 3.2 1B GGUF + ChromaDB Vector Store** backend for the **J.A.R.V.I.S. Multi-Agent RAG Intelligence Platform**.

---

## 🏛️ System Architecture Overview

```
                      +----------------------------------+
                      |     React Frontend Dashboard     |
                      |  (Real-Time Streaming + UI Graph)|
                      +----------------------------------+
                                       |
                                       v
                      +----------------------------------+
                      |      Django 5.x REST API Layer   |
                      |   POST /api/chat/ (Streaming)    |
                      |   POST /api/pipeline/run/        |
                      +----------------------------------+
                                       |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
     +------------------------------+       +------------------------------+
     |   ChromaDB Vector Store      |       |  LangGraph 8-Agent StateGraph|
     |   (Hybrid Vector + Keyword)  |       |  Parallel Fan-In & Feedback  |
     +------------------------------+       +------------------------------+
                    |                                       |
                    +-------------------+-------------------+
                                       |
                                       v
                      +----------------------------------+
                      |      Ollama Local GGUF Engine     |
                      |   Model: Llama 3.2 1B Instruct   |
                      |   (60m RAM caching, Temp: 0.3)   |
                      +----------------------------------+
```

---

## 🛠️ Technology Stack & Upgrade Specifications

- **Framework**: Django 5.x + Django REST Framework (`StreamingHttpResponse`)
- **Multi-Agent Orchestration**: LangGraph (`StateGraph`, `CompiledGraph`)
- **LLM Engine**: Ollama GGUF (`hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0`)
- **Vector Database**: ChromaDB (Persistent local vector database with cosine distance space)
- **Document Extractors**: `pymupdf` (PyMuPDF), `pypdf`, `pdfplumber`, `python-docx`, `pandas`
- **Relational Storage**: SQLite3 (`UserProfile`, `IngestedDocument`, `AgentExecutionLog`)

---

## 🧠 LangGraph 8-Agent StateGraph Workflow

All 8 logical agents operate on a unified Pydantic memory state (`AgentGraphState`) with strict tenant boundary safety and anti-hallucination validation:

### 1. 📥 `IngestionAgent` (Agent 1)
- **Role**: Normalizes user input queries, initializes pipeline execution state, and validates `user_id` tenant context.

### 2. 📑 `DecompositionAgent` (Agent 2)
- **Role**: Decomposes complex user queries into 3-5 atomic subtasks and document retrieval targets.

### 3. 📚 `DomainContextRAGAgent` (Agent 3)
- **Role**: Queries ChromaDB vector database using hybrid semantic vector search + keyword fallback. Returns grounded document context snippets.

### 4. 🛡️ `RiskConstraintAgent` (Agent 4)
- **Role**: Identifies technical, operational, edge-case, and architectural security constraints.

### 5. 🏛️ `SynthesisPlannerAgent` (Agent 5)
- **Role**: Synthesizes subtasks, RAG evidence, and risk analysis into a master solution plan. Dynamically incorporates evaluator feedback on retries.

### 6. ⚡ `PrimaryLLMSolverAgent` (Agent 6)
- **Role**: Solves the master plan independently using Ollama Llama 3.2 1B model, producing **Solution A**.

### 7. 🔥 `SecondaryLLMSolverAgent` (Agent 7)
- **Role**: Solves the master plan independently using Llama 3.2 1B model, producing **Solution B** for dual-path validation.

### 8. ✅ `EvaluatorJudgeAgent` (Agent 8)
- **Role**: Audits Solution A & Solution B using structured Pydantic `AntiHallucinationAudit`. Enforces anti-hallucination checks and loops back to Agent 1 if critique fails.

---

## ⚡ Key Upgrades & Technical Enhancements

### 1. 🎙️ Real-Time Word-by-Word Streaming Chatbot (`POST /api/chat/`)
- Returns a token-by-token `StreamingHttpResponse` (`text/plain; charset=utf-8`).
- Uses `ollama.chat(stream=True)` to stream responses instantly without buffering full paragraphs.
- Configured with strict J.A.R.V.I.S. persona ("Hello, Sir. How may I assist you today?").

### 2. 📁 Hybrid Vector Search & Bulletproof Document Ingestion
- Unified user context resolution between file upload and chatbot retrieval via `UserService.get_or_create_user(email=email)`.
- 3-tier hybrid retrieval in `ChromaVectorStoreService.search`:
  1. Strict `user_id` vector search.
  2. Fallback to all collection documents if tenant query returns 0 hits.
  3. String keyword search fallback for proper nouns/names (e.g. `"suraj"`).

### 3. 📊 Agent Work Progress Percentage UI
- Real-time animated progress bars and percentage counters (`0%` → `45%` → `85%` → `100%`) for each agent node in the frontend `NeuralAgentNetwork`.
- Includes glowing animated loading fill tracks and live inspector modals.

### 4. 🧹 Complete Database Reset Script (`reset_db.py`)
- Python script to purge SQLite records (`IngestedDocument`, `AgentExecutionLog`) and recreate a clean ChromaDB collection (`user_knowledge_base`, 0 indexed chunks).

---

## ⚡ REST API Endpoints

### 1. Health Check
- **`GET /api/health/`**
- **Response**:
  ```json
  {
    "status": "healthy",
    "backend": "Django REST Framework 5.x",
    "vectorstore": { "collection": "user_knowledge_base", "total_indexed_chunks": 0 },
    "llm_providers": { "ollama_connected": true, "llm_a_model": "hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0" }
  }
  ```

### 2. Multi-Agent Pipeline Execution & Document Ingestion
- **`POST /api/pipeline/run/`** (multipart/form-data or JSON)
- **Response**:
  ```json
  {
    "status": "success",
    "execution_id": "uuid",
    "indexed_chunks": 1,
    "iterations_used": 1,
    "evaluation_passed": true,
    "solution": "Synthesized solution...",
    "execution_duration_seconds": 16.74
  }
  ```

### 3. Interactive Real-Time Streaming AI Chat
- **`POST /api/chat/`**
- **Payload**: `{"prompt": "who is suraj", "email": "alex.mercer@innovate.org"}`
- **Response**: Streamed text response word-by-word in J.A.R.V.I.S. persona.

---

## 🚀 How to Run the System

```cmd
run.bat
```
- **Backend REST API**: `http://127.0.0.1:8000/api/health/`
- **React Frontend**: `http://127.0.0.1:5173/`
