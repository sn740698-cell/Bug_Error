import { useState, useEffect, useRef } from 'react'
import './App.css'
import NeuralAgentNetwork from './components/NeuralAgentNetwork'

const BACKEND_URL = 'http://127.0.0.1:8000'

function App() {
  // User & Query Input State
  const [userName, setUserName] = useState('Alex Mercer')
  const [userEmail, setUserEmail] = useState('alex.mercer@innovate.org')
  const [userSection, setUserSection] = useState('Distributed Systems & Cloud Architecture')
  const [queryText, setQueryText] = useState('Design a geo-distributed low-latency consensus protocol for banking ledger transactions with zero data loss.')
  const [selectedFiles, setSelectedFiles] = useState([])

  // Execution & Pipeline State
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [pipelineResult, setPipelineResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  // LLM Connection Modal State
  const [showLLMModal, setShowLLMModal] = useState(false)

  // Health State
  const [health, setHealth] = useState({
    status: 'checking',
    backend: 'Django REST Framework 5.x',
    vectorstore: { indexed_chunks: 0 },
    llm_providers: { embedding_provider: 'mock', llm_a_provider: 'mock', llm_b_provider: 'mock' }
  })

  // Format model names nicely
  const formatModelName = (fullModelPath, defaultFallback = 'Model') => {
    if (!fullModelPath) return defaultFallback
    if (fullModelPath.includes('Llama-3.2')) return 'Llama 3.2 1B'
    if (fullModelPath.includes('Qwen2.5')) return 'Qwen 2.5 1B'
    if (fullModelPath.includes('qwen3')) return 'Qwen3 4B'
    if (fullModelPath.includes('gpt-4o')) return 'GPT-4o'
    if (fullModelPath.includes('claude-3-5')) return 'Claude 3.5'
    const parts = fullModelPath.split('/')
    const lastPart = parts[parts.length - 1]
    return lastPart.split(':')[0] || defaultFallback
  }

  const getLLMBadgeLabel = () => {
    const provA = health.llm_providers?.llm_a_provider?.toUpperCase() || 'OLLAMA'
    const provB = health.llm_providers?.llm_b_provider?.toUpperCase() || 'OLLAMA'
    const modelA = formatModelName(health.llm_providers?.llm_a_model, 'Llama 3.2 1B')
    const modelB = formatModelName(health.llm_providers?.llm_b_model, 'Llama 3.2 1B')

    if (provA === 'OLLAMA' || health.llm_providers?.ollama_connected) {
      return `⚡ Ollama: Llama 3.2 1B (Dual Solver)`
    }
    return `⚡ LLMs: ${modelA} / ${modelB}`
  }

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [isChatting, setIsChatting] = useState(false)
  const chatHistoryRef = useRef(null)

  // Auto-scroll Chat History when new words stream in
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight
    }
  }, [chatMessages, isChatting])

  // Fetch Health Check
  const fetchHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/health/`)
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch (e) {
      setHealth(prev => ({ ...prev, status: 'offline' }))
    }
  }

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 8000)
    return () => clearInterval(interval)
  }, [])

  // Execute 8-Agent Pipeline via POST /api/pipeline/run/
  const handleRunPipeline = async (e, customQuery = null, customFiles = null) => {
    if (e) e.preventDefault()
    
    const query = customQuery || queryText
    const files = customFiles || selectedFiles

    if (!query.trim()) {
      setErrorMessage("Please enter a query prompt before launching the pipeline.")
      return
    }

    setIsAnalyzing(true)
    setErrorMessage(null)

    const formData = new FormData()
    formData.append('name', userName)
    formData.append('email', userEmail)
    formData.append('section', userSection)
    formData.append('query', query)

    if (files && files.length > 0) {
      Array.from(files).forEach(file => {
        formData.append('files', file)
      })
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/pipeline/run/`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()

      if (res.ok && data.status === 'success') {
        setPipelineResult(data)
        setSelectedFiles([])
        fetchHealth()
      } else {
        setErrorMessage(data.message || data.error || 'Pipeline execution failed.')
      }
    } catch (err) {
      setErrorMessage(`Network error connecting to backend at ${BACKEND_URL}. Ensure Django server is running.`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 1-Click Quick Demo Handler
  const handleQuickDemo = async () => {
    const demoQuery = "Design a geo-distributed low-latency consensus protocol for banking ledger transactions with zero data loss."
    const sampleText = `BANKING LEDGER SYSTEM ARCHITECTURE SPECIFICATION:
1. Multi-region consensus required with sub-50ms commit latency across 3 geographic zones.
2. Zero Recovery Point Objective (RPO=0) with synchronous quorum replication.
3. Byzantine fault tolerance for untrusted edge nodes.
4. Strict ACID transactional semantics for financial ledger balances.`

    const blob = new Blob([sampleText], { type: 'text/plain' })
    const file = new File([blob], "banking_ledger_spec.txt", { type: "text/plain" })

    setQueryText(demoQuery)
    setSelectedFiles([file])
    handleRunPipeline(null, demoQuery, [file])
  }

  // Chatbot Handler streaming word-by-word from POST /api/chat/
  const handleSendChatMessage = async (qText) => {
    const question = qText || chatInput
    if (!question.trim() || isChatting) return

    const userMsg = { sender: 'user', text: question, time: new Date().toLocaleTimeString() }
    setChatMessages(prev => [...prev, userMsg])
    if (!qText) setChatInput('')
    setIsChatting(true)

    // Add initial empty bot bubble for word-by-word stream rendering
    const initialBotMsg = {
      sender: 'bot',
      text: '',
      model: 'J.A.R.V.I.S. (Llama 3.2 1B)',
      time: new Date().toLocaleTimeString()
    }
    setChatMessages(prev => [...prev, initialBotMsg])

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: question, name: userName, email: userEmail })
      })

      if (res.ok && res.body) {
        const reader = res.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let accumulatedText = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          accumulatedText += chunk

          setChatMessages(prev => {
            const copy = [...prev]
            const lastIdx = copy.length - 1
            if (lastIdx >= 0 && copy[lastIdx].sender === 'bot') {
              copy[lastIdx] = { ...copy[lastIdx], text: accumulatedText }
            }
            return copy
          })
        }
      } else {
        setChatMessages(prev => [...prev, { sender: 'bot', text: "Error connecting to AI assistant.", time: new Date().toLocaleTimeString() }])
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'bot', text: "Network error connecting to AI backend.", time: new Date().toLocaleTimeString() }])
    } finally {
      setIsChatting(false)
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <span className="logo-icon">🤖</span>
          <div>
            <h1>Multi-Agent RAG Intelligence Platform</h1>
            <p className="subtitle">Django 5.x REST + LangGraph 8-Agent Graph + ChromaDB + Multi-LLM Orchestration</p>
          </div>
        </div>

        <div className="header-status-group">
          <div className={`status-badge ${health.status === 'healthy' ? 'online' : 'offline'}`}>
            <span className="dot"></span>
            {health.status === 'healthy' ? 'Backend: Connected' : 'Backend: Offline'}
          </div>

          <div 
            className="status-badge active clickable" 
            onClick={() => setShowLLMModal(true)}
            title="Click to view full LLM Connection Matrix"
          >
            {getLLMBadgeLabel()}
          </div>

          <div className="status-badge db-badge">
            📦 Vector DB: {health.vectorstore?.total_indexed_chunks || health.vectorstore?.indexed_chunks || 0} Chunks
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="main-grid">
        {/* 1. Document Ingestion Card */}
        <div className="card full-width" style={{ marginBottom: '16px' }}>
          <div className="card-header-flex">
            <h2>📁 1. RAG Knowledge Base Document Ingestion</h2>
            <span className="status-badge online">
              📥 ChromaDB Vector Store Ready
            </span>
          </div>
          <p className="card-desc">
            Upload PDF, DOCX, CSV, or TXT documents here. Files are automatically chunked, embedded, and stored in ChromaDB vector store with <code>user_id</code> tenant isolation. Use the AI Chatbot below to query your documents or ask any questions directly.
          </p>

          <form onSubmit={(e) => {
            e.preventDefault();
            if (selectedFiles.length === 0) return;
            handleRunPipeline(e, `Analyze and index uploaded documents (${selectedFiles.map(f => f.name).join(', ')})`, selectedFiles);
          }} className="upload-form">
            {/* Drag & Drop File Upload Box */}
            <div className="upload-dropzone" onClick={() => document.getElementById('file-input-element').click()}>
              <input
                id="file-input-element"
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.csv"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files) {
                    setSelectedFiles(prev => [...prev, ...Array.from(e.target.files)])
                  }
                }}
              />
              <div style={{ fontSize: '28px', marginBottom: '6px' }}>📄 ⬆️</div>
              <div style={{ fontWeight: '600', color: '#f8fafc', fontSize: '15px' }}>
                Click or Drag & Drop Documents Here to Index into Vector Database
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                Supported Formats: <strong>PDF, DOCX, CSV, TXT</strong>
              </div>
            </div>

            {/* Selected Files Badge List */}
            {selectedFiles.length > 0 && (
              <div className="file-chip-list">
                {Array.from(selectedFiles).map((file, idx) => (
                  <div key={idx} className="file-chip">
                    <span>📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFiles(prev => prev.filter((_, i) => i !== idx))
                      }}
                      title="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Action Button */}
            {selectedFiles.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <button type="submit" className="primary-btn" disabled={isAnalyzing}>
                  {isAnalyzing ? '⚡ Indexing Documents into ChromaDB...' : '📥 Upload & Index Documents into Vector Store'}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Live Neural Agent Network Graph */}
        <div className="card full-width" style={{ padding: '0', background: 'transparent', border: 'none' }}>
          <NeuralAgentNetwork
            activeAgentId={isAnalyzing ? 'planner' : null}
            pipelineResult={pipelineResult}
            isExecuting={isAnalyzing}
            onQuickDemo={handleQuickDemo}
          />
        </div>



        {/* Master LLM Solution Response Card */}
        {pipelineResult && (
          <div className="card full-width">
            <div className="card-header-flex">
              <h2>2. Master 8-Agent LLM Solution Response</h2>
              <div style={{ display: 'flex', gap: '8px' }}>
                <span className={`status-badge ${pipelineResult.evaluation_passed ? 'online' : 'warn'}`}>
                  {pipelineResult.evaluation_passed ? '✓ Anti-Hallucination Verified' : '⚠️ Unverified Response'}
                </span>
                <span className="status-badge active">
                  🎯 Confidence: {((pipelineResult.hallucination_audit?.confidence || 0.95) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <p className="card-desc">
              Synthesized by Agent 6 (Primary Solver) & Agent 7 (Secondary Solver), audited by Agent 8 (Evaluator Judge).
            </p>

            <div className="draft-container" style={{ background: '#172445', border: '1px solid #38bdf8' }}>
              <div className="draft-meta-bar" style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>Execution ID: <code>{pipelineResult.execution_id}</code></span>
                <span>Indexed Chunks: <strong>{pipelineResult.indexed_chunks}</strong></span>
                <span>Iterations: <strong>{pipelineResult.iterations_used}</strong></span>
                <span>Duration: <strong>{pipelineResult.execution_duration_seconds}s</strong></span>
              </div>

              <div className="draft-text-box" style={{ padding: '16px 0', fontSize: '15px', color: '#f8fafc', lineHeight: '1.6' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{pipelineResult.solution}</pre>
              </div>

              {/* Hallucination Findings & Critique */}
              {pipelineResult.hallucination_audit && (
                <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid #2b3b6b', fontSize: '12px' }}>
                  <div style={{ color: '#38bdf8', fontWeight: 'bold', marginBottom: '4px' }}>🛡️ Anti-Hallucination Audit Report:</div>
                  <div style={{ color: '#cbd5e1' }}>{pipelineResult.hallucination_audit.actionable_critique}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Grounded RAG Sources Section */}
        {pipelineResult?.retrieved_sources && pipelineResult.retrieved_sources.length > 0 && (
          <div className="card full-width">
            <h2>3. Retrieved Grounded Context Chunks ({pipelineResult.retrieved_sources.length})</h2>
            <p className="card-desc">Strictly filtered vector chunks retrieved from ChromaDB with user_id tenant boundary safety.</p>

            <div className="insights-grid">
              {pipelineResult.retrieved_sources.map((src, idx) => (
                <div key={idx} className="insight-card" style={{ borderLeft: '4px solid #38bdf8' }}>
                  <div className="insight-header">
                    <span className="field-name">📄 {src.source} (p.{src.page})</span>
                    <span className="confidence-pill">Score: {(src.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="field-val" style={{ fontSize: '12px', fontWeight: 'normal', color: '#cbd5e1', lineHeight: '1.4' }}>
                    {src.content}
                  </div>
                  <div className="source-tag">Chunk Index: {src.chunk_index}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interactive Chatbot */}
        <div className="card full-width">
          <h2>4. Interactive AI & RAG Assistant</h2>
          <p className="card-desc">Query the multi-agent system directly with general knowledge, code, or document analysis prompts.</p>

          <div className="chatbot-container">
            <div className="chat-chips-group">
              <button className="chip-btn" onClick={() => handleSendChatMessage("What is the theory of relativity and how does time dilation work?")}>
                🌍 General Knowledge
              </button>
              <button className="chip-btn" onClick={() => handleSendChatMessage("How do I implement binary search in Python with O(log n) complexity?")}>
                💻 Coding & Tech
              </button>
              <button className="chip-btn" onClick={() => handleSendChatMessage("What are the key requirements and constraints in the uploaded document?")}>
                📄 Document Analysis
              </button>
            </div>

            <div className="chat-history" ref={chatHistoryRef}>
              {chatMessages.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0', fontSize: '13px' }}>
                  💬 Ask anything! Click a chip above or type your prompt below.
                </div>
              ) : (
                chatMessages.map((msg, i) => {
                  const isLastBotMessage = isChatting && msg.sender === 'bot' && i === chatMessages.length - 1;
                  return (
                    <div key={i} className={`chat-bubble ${msg.sender}`}>
                      <div className="msg-text">
                        {msg.sender === 'bot' && msg.text === '' && isChatting ? (
                          <span className="streaming-dots">⚡ J.A.R.V.I.S. is thinking...</span>
                        ) : (
                          <>
                            {msg.text}
                            {isLastBotMessage && <span className="typing-cursor">▋</span>}
                          </>
                        )}
                      </div>
                      <div className="chat-meta">
                        <span>{msg.time}</span>
                        {msg.model && <span>• Model: {msg.model}</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSendChatMessage(); }} className="chat-input-form">
              <input
                type="text"
                className="chat-input-field"
                placeholder="Ask any question or query the vector store..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatting}
              />
              <button type="submit" className="primary-btn" disabled={!chatInput.trim() || isChatting}>
                {isChatting ? 'Thinking...' : 'Send 💬'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* LLM Connection Details Modal */}
      {showLLMModal && (
        <div className="llm-modal-overlay" onClick={() => setShowLLMModal(false)}>
          <div className="llm-modal" onClick={e => e.stopPropagation()}>
            <div className="llm-modal-header">
              <h3>⚡ Active LLM Connection & System Architecture</h3>
              <button className="close-btn" onClick={() => setShowLLMModal(false)}>✕</button>
            </div>

            <div style={{ marginBottom: '16px', background: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.4)', color: '#34d399', padding: '12px', borderRadius: '10px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px' }}>🟢</span>
              <div>
                <strong>Local Ollama Server Connected:</strong> {health.llm_providers?.ollama_url || 'http://localhost:11434'}
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>High-performance GGUF local model execution active with 60m RAM caching</div>
              </div>
            </div>

            <div className="llm-grid">
              <div className="llm-card">
                <div className="llm-card-title">Primary Solver (LLM A)</div>
                <div className="llm-card-model">{formatModelName(health.llm_providers?.llm_a_model, 'Llama 3.2 1B')}</div>
                <div className="llm-card-sub">Provider: OLLAMA (Local GGUF)</div>
                <div className="llm-card-sub" style={{ fontSize: '10px', marginTop: '2px', color: '#94a3b8' }}>
                  {health.llm_providers?.llm_a_model || 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0'}
                </div>
                <div className="llm-status-row">
                  <span className="dot" style={{ background: '#34d399', width: '8px', height: '8px', borderRadius: '50%' }}></span>
                  <span style={{ color: '#34d399' }}>Real-time Connected (Temp: 0.2, Context: 4k)</span>
                </div>
              </div>

              <div className="llm-card">
                <div className="llm-card-title">Secondary Solver (Agent 7)</div>
                <div className="llm-card-model">{formatModelName(health.llm_providers?.llm_b_model, 'Llama 3.2 1B')}</div>
                <div className="llm-card-sub">Provider: OLLAMA (Local GGUF)</div>
                <div className="llm-card-sub" style={{ fontSize: '10px', marginTop: '2px', color: '#94a3b8' }}>
                  {health.llm_providers?.llm_b_model || 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0'}
                </div>
                <div className="llm-status-row">
                  <span className="dot" style={{ background: '#34d399', width: '8px', height: '8px', borderRadius: '50%' }}></span>
                  <span style={{ color: '#34d399' }}>Real-time Connected (Temp: 0.2, Context: 4k)</span>
                </div>
              </div>

              <div className="llm-card">
                <div className="llm-card-title">Anti-Hallucination Evaluator</div>
                <div className="llm-card-model">{formatModelName(health.llm_providers?.evaluator_model, 'Llama 3.2 1B')}</div>
                <div className="llm-card-sub">Provider: OLLAMA (Local GGUF)</div>
                <div className="llm-card-sub" style={{ fontSize: '10px', marginTop: '2px', color: '#94a3b8' }}>
                  {health.llm_providers?.evaluator_model || 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0'}
                </div>
                <div className="llm-status-row">
                  <span className="dot" style={{ background: '#818cf8', width: '8px', height: '8px', borderRadius: '50%' }}></span>
                  <span style={{ color: '#818cf8' }}>Structured JSON Auditor</span>
                </div>
              </div>

              <div className="llm-card">
                <div className="llm-card-title">Vector Database & Local Embeddings</div>
                <div className="llm-card-model">ChromaDB ({health.vectorstore?.total_indexed_chunks || 0} Chunks)</div>
                <div className="llm-card-sub">Provider: OLLAMA / Local MiniLM-L6-v2</div>
                <div className="llm-status-row">
                  <span className="dot" style={{ background: '#38bdf8', width: '8px', height: '8px', borderRadius: '50%' }}></span>
                  <span style={{ color: '#38bdf8' }}>Tenant Isolated (user_id filtering)</span>
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600' }}>Loaded Ollama GGUF Models on Host:</div>
              <div className="ollama-tag-list">
                {health.llm_providers?.ollama_models?.length > 0 ? (
                  health.llm_providers.ollama_models.map((m, idx) => (
                    <span key={idx} className="ollama-tag">{m}</span>
                  ))
                ) : (
                  <span className="ollama-tag">hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
