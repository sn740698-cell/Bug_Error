# Multi-Tenant Multi-Agent RAG + LangGraph + Django REST Backend

A production-ready, multi-tenant AI intelligence backend built with **Django 5.x**, **Django REST Framework**, **ChromaDB**, **LangChain**, and an **8-Agent LangGraph Workflow** featuring multi-LLM orchestration, parallel solver fan-in, structured anti-hallucination audit evaluation, and conditional feedback retry loops.

---

## 🏛️ Architecture Overview

```text
React + Tailwind Frontend
        |
        | POST /api/pipeline/run/ (multipart/form-data)
        v
Django REST Framework
        |
        +-----------------------------+
        |                             |
        v                             v
PostgreSQL / SQLite              ChromaDB Vector Database
Relational audit state           Persistent semantic state with user_id tenant filtering
        |                             |
        +-------------+---------------+
                      |
                      v
              LangGraph Orchestrator
                      |
              Agent 1: IngestionAgent
                      |
              Agent 2: DecompositionAgent
                      |
              +-------+-------+
              |               |
              v               v
      Agent 3: RAG      Agent 4: Risk
              |               |
              +-------+-------+
                      |
                      v
              Agent 5: SynthesisPlanner
                      |
              +-------+-------+
              |               |
              v               v
      Agent 6: LLM A    Agent 7: LLM B (Parallel Solvers)
              |               |
              +-------+-------+
                      |
                      v (Parallel Fan-In)
              Agent 8: EvaluatorJudge (Anti-Hallucination Audit)
                      |
            +---------+----------+
            |                    |
          PASS                 FAIL
            |                    |
            v                    v
          END       Planner -> Solvers -> Evaluator
                         |
                  until MAX_RETRIES reached
                         |
                         v
                        END
```

---

## 🤖 8-Agent Workflow Breakdown

1. **Agent 1 — IngestionAgent**: Validates tenant context, normalizes raw input, and initializes workflow state.
2. **Agent 2 — DecompositionAgent**: Decomposes user queries into atomic subtasks and technical retrieval requirements.
3. **Agent 3 — DomainContextRAGAgent**: Queries persistent ChromaDB vector store strictly filtered by `user_id`. Returns `NO_RELEVANT_CONTEXT_FOUND` if context is absent.
4. **Agent 4 — RiskConstraintAgent**: Identifies security vulnerabilities, edge cases, failure modes, and architectural constraints.
5. **Agent 5 — SynthesisPlannerAgent**: Combines subtasks, RAG evidence, and risk analysis into a master solution plan. On retry, explicitly incorporates prior evaluator findings and actionable critique.
6. **Agent 6 — PrimaryLLMSolverAgent (LLM A)**: Independently generates Solution A grounded in evidence.
7. **Agent 7 — SecondaryLLMSolverAgent (LLM B)**: Independently generates Solution B grounded in evidence, providing alternative architectural perspectives.
8. **Agent 8 — EvaluatorJudgeAgent (Evaluator)**: Performs structured Pydantic anti-hallucination audit (`AntiHallucinationAudit`), comparing query, evidence, risks, Solution A, and Solution B. Triggers conditional feedback loop if invalid up to `MAX_RETRIES`.

---

## 🔒 Tenant Isolation & Safety Rules

- Every vector chunk in ChromaDB is indexed with `user_id` metadata.
- All RAG vector store queries enforce strict `where={"user_id": user_id}` metadata filtering.
- Dual-write persistence ensures database records reflect `FAILED` state if vector storage encounters errors.
- Support for PDF, DOCX, CSV, TXT files. Legacy `.doc` binary uploads are rejected with informative conversion guidance.

---

## ⚙️ Prerequisites & Setup

### Requirements
- Python 3.10+
- Virtualenv
- (Optional) PostgreSQL 14+
- (Optional) Ollama / OpenAI / Anthropic API keys

### Installation

```cmd
cd back_end
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Configuration

Copy `.env.example` to `.env`:

```cmd
cp .env.example .env
```

Edit `.env` as appropriate:

```ini
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

CHROMA_PERSIST_DIR=data/chroma

EMBEDDING_PROVIDER=mock
LLM_A_PROVIDER=mock
LLM_B_PROVIDER=mock
EVALUATOR_PROVIDER=mock

MAX_RETRIES=2
```

---

## 🚀 Running Database Migrations & Server

```cmd
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

---

## 🧪 Testing & Verification

Run the test suite:

```cmd
venv\Scripts\python.exe manage.py test api.tests
```

Or run pytest:

```cmd
pytest
```

Run CLI Execution Harness:

```cmd
venv\Scripts\python.exe test_pipeline.py
```

---

## 📡 REST API Contracts

### 1. Execute Multi-Agent RAG Pipeline
- **Endpoint**: `POST /api/pipeline/run/`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `name`: User Name
  - `email`: User Email
  - `section`: Section / Department
  - `query`: Query prompt
  - `files[]`: Optional uploaded files (PDF, DOCX, CSV, TXT)

#### Sample JSON Response:

```json
{
  "status": "success",
  "user_id": "8f2d5e72-3c1a-45b9-9118-86d7e0081a2f",
  "execution_id": "a90b8f1c-7d6e-4f32-8e10-928374615243",
  "indexed_chunks": 12,
  "iterations_used": 1,
  "evaluation_passed": true,
  "solution": "[Consensus Solution] Geo-distributed low-latency consensus protocol...",
  "hallucination_audit": {
    "is_valid": true,
    "confidence": 0.95,
    "findings": [],
    "unsupported_claims": [],
    "contradictions": [],
    "missing_requirements": [],
    "actionable_critique": "Solution is factually grounded."
  },
  "retrieved_sources": [
    {
      "content": "BANKING LEDGER SYSTEM SPECIFICATION...",
      "source": "banking_ledger_spec.txt",
      "page": 1,
      "chunk_index": 0,
      "score": 0.98
    }
  ],
  "execution_duration_seconds": 0.42
}
```

### 2. Backend Health Diagnostic Check
- **Endpoint**: `GET /api/health/`
- **Response**:

```json
{
  "status": "healthy",
  "backend": "Django REST Framework 5.x",
  "vectorstore": {
    "type": "ChromaDB",
    "available": true,
    "collection": "user_knowledge_base",
    "total_indexed_chunks": 12
  },
  "llm_providers": {
    "embedding_provider": "mock",
    "llm_a_provider": "mock",
    "llm_b_provider": "mock",
    "evaluator_provider": "mock"
  },
  "orchestrator": "LangGraph 8-Agent StateGraph with parallel fan-in & feedback loop",
  "max_retries": 2
}
```

---

## 💻 React + Tailwind Frontend Code Snippet

```javascript
const formData = new FormData();
formData.append("name", "Alex Mercer");
formData.append("email", "alex.mercer@innovate.org");
formData.append("section", "Distributed Systems");
formData.append("query", queryText);

uploadedFiles.forEach((file) => {
  formData.append("files", file);
});

const response = await fetch("http://localhost:8000/api/pipeline/run/", {
  method: "POST",
  body: formData
});

const data = await response.json();
console.log("Pipeline result:", data);
```
