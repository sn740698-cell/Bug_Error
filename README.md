# 🤖 J.A.R.V.I.S. Multi-Agent RAG Intelligence Platform

An enterprise-grade **Multi-Agent RAG System** powered by **Django 5.x REST Framework**, **LangGraph 8-Agent StateGraph**, **ChromaDB Vector Store**, and local **Ollama Llama 3.2 1B GGUF**, with a real-time interactive **React Dashboard**.

---

## ✨ Key Features & Upgrades

- **🎙️ Real-Time Word-by-Word Typewriter Streaming Chatbot**: `POST /api/chat/` streams responses word-by-word via `StreamingHttpResponse` in J.A.R.V.I.S. persona ("Hello, Sir. How may I assist you today?").
- **🧠 8-Agent LangGraph Orchestration**:
  1. `IngestionAgent`: Normalizes input queries and validates tenant boundaries.
  2. `DecompositionAgent`: Decomposes complex queries into atomic subtasks.
  3. `DomainContextRAGAgent`: Performs hybrid vector + keyword search over ChromaDB.
  4. `RiskConstraintAgent`: Audits architectural security constraints and edge cases.
  5. `SynthesisPlannerAgent`: Builds master solution plans and incorporates evaluator feedback on retries.
  6. `PrimaryLLMSolverAgent`: Generates independent Solution A using Llama 3.2 1B.
  7. `SecondaryLLMSolverAgent`: Generates independent Solution B for dual-path validation.
  8. `EvaluatorJudgeAgent`: Performs structured Pydantic anti-hallucination evaluation.
- **📊 Agent Work Progress Percentage UI**: Live animated progress bars and percentage counters (`0%` → `45%` → `85%` → `100%`) for each agent node in the frontend dashboard.
- **📁 Bulletproof Document Ingestion Stack**: Supports PDF (`pymupdf`, `pypdf`, `pdfplumber`), DOCX (`python-docx`), CSV (`pandas`), and TXT with automatic text chunking and vector embedding.
- **🧹 Clean Database Reset Script**: Includes `reset_db.py` to wipe SQLite records and reset ChromaDB vector collections to 0 chunks.

---

## 🏛️ System Architecture

```text
React Frontend (Vite) <---> Django 5.x REST API <---> LangGraph 8-Agent Graph
                                   |                      |
                                   v                      v
                             ChromaDB Vector Store <---> Ollama Llama 3.2 1B
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama running locally with `Llama 3.2 1B Instruct GGUF` installed:
  ```cmd
  ollama run hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0
  ```

### 2. 1-Click Launch (Windows)
Double-click or run:
```cmd
run.bat
```
This automatically starts:
- **Django REST Backend**: `http://127.0.0.1:8000/api/health/`
- **React Frontend Dashboard**: `http://127.0.0.1:5173/`

### 3. Reset Database
To clear all stored documents and reset ChromaDB vector collections:
```cmd
cd back_end
venv\Scripts\python.exe reset_db.py
```

---

## 📖 Technical Documentation

- **Backend Specifications & Architecture**: See [`back.md`](file:///d:/Projects/Hachathon_2/back.md)
- **Frontend Specifications & Components**: See [`front.md`](file:///d:/Projects/Hachathon_2/front.md)

---

## 📜 License
MIT License. Developed for Advanced Multi-Agent RAG Intelligence.
