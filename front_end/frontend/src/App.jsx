import { useState, useEffect } from 'react'
import './App.css'

const BACKEND_URL = 'http://127.0.0.1:8000'

// 5-Agent Anti-Hallucination & Verification Framework
const AGENTS = [
  { id: 'master_orchestrator', name: 'Master Orchestrator Supervisor', role: 'Supervisor', icon: '🏛️', desc: 'Orchestrates 5-agent anti-hallucination workflow' },
  { id: 'document_decomposer', name: 'Document Decomposer Agent (1)', role: 'Agent', icon: '📑', desc: 'Multi-part structural partitioning & ground-truth extraction' },
  { id: 'vector_retrieval_agent', name: 'Vector Knowledge Retrieval Agent (2)', role: 'Agent', icon: '📚', desc: '2-Stage ChromaDB + DistilBERT contextual re-ranking' },
  { id: 'layman_simplifier', name: 'Layman Simplifier Agent (3)', role: 'Agent', icon: '📝', desc: 'Grounded plain-English executive summary' },
  { id: 'communication_orchestrator', name: 'Communication Orchestrator Supervisor', role: 'Supervisor', icon: '💬', desc: 'Llama 3.2 1B primary model orchestration' },
  { id: 'notification_drafter', name: 'Executive Summary Drafter Agent', role: 'Agent', icon: '✍️', desc: 'Synthesizes structured executive summary & recommendations' },
  { id: 'fact_verifier', name: 'Fact Verification Agent (4)', role: 'Agent', icon: '✅', desc: 'Fact-checking draft against extracted ground-truth' },
  { id: 'hallucination_auditor', name: 'Hallucination Audit Agent (5)', role: 'Agent', icon: '🛡️', desc: 'Real-time NLI cross-verification & zero-hallucination audit' }
]

function App() {
  // System Health State
  const [health, setHealth] = useState({
    status: 'checking',
    ollama: { connected: false, qwen_model: '', llama_model: '', available_models: [] },
    vectorstore: { indexed_chunks: 0 },
    gpu: { device: 'CPU', free_mb: 0, total_mb: 0 }
  })

  // Document Upload State
  const [selectedFile, setSelectedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedDoc, setUploadedDoc] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  // Workflow State
  const [activeWorkflowId, setActiveWorkflowId] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [workflowStatus, setWorkflowStatus] = useState(null)
  const [insights, setInsights] = useState([])
  const [draft, setDraft] = useState(null)
  const [isRegenerating, setIsRegenerating] = useState(false)

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [isChatting, setIsChatting] = useState(false)

  // Agent Activity Logs
  const [agentLogs, setAgentLogs] = useState([])

  // Send Chatbot Message Handler
  const handleSendChatMessage = async (qText) => {
    const question = qText || chatInput
    if (!question || isChatting) return
    const targetWfId = activeWorkflowId || 'general'

    const userMsg = { sender: 'user', text: question, time: new Date().toLocaleTimeString() }
    setChatMessages(prev => [...prev, userMsg])
    if (!qText) setChatInput('')
    setIsChatting(true)

    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows/${targetWfId}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })
      const data = await res.json()
      if (res.ok) {
        const botMsg = {
          sender: 'bot',
          text: data.answer,
          model: data.llm_model,
          sources: data.sources,
          time: new Date().toLocaleTimeString()
        }
        setChatMessages(prev => [...prev, botMsg])
      } else {
        setChatMessages(prev => [...prev, { sender: 'bot', text: `Error: ${data.error}`, time: new Date().toLocaleTimeString() }])
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'bot', text: "Network error getting response from Chatbot.", time: new Date().toLocaleTimeString() }])
    } finally {
      setIsChatting(false)
    }
  }

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

  // Poll Active Workflow Status
  useEffect(() => {
    if (!activeWorkflowId) return

    const pollWorkflow = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/workflows/${activeWorkflowId}/`)
        if (res.ok) {
          const data = await res.json()
          setWorkflowStatus(data)

          // Generate Agent Activity Log Entries
          if (data.routing_decisions) {
            const logs = data.routing_decisions.map((rd, i) => ({
              time: new Date(rd.created_at).toLocaleTimeString(),
              supervisor: rd.supervisor,
              target: rd.selected_target,
              reason: rd.reason
            }))
            setAgentLogs(logs)
          }

          // If workflow completes, fetch insights & draft
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            setIsAnalyzing(false)
            fetchInsights(activeWorkflowId)
            fetchDraft(activeWorkflowId)
          }
        }
      } catch (e) {
        console.error("Workflow status poll error:", e)
      }
    }

    pollWorkflow()
    const interval = setInterval(pollWorkflow, 2000)
    return () => clearInterval(interval)
  }, [activeWorkflowId])

  // Fetch Insights
  const fetchInsights = async (wfId) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows/${wfId}/insights/`)
      if (res.ok) {
        const data = await res.json()
        setInsights(data.insights || [])
      }
    } catch (e) {
      console.error("Fetch insights error:", e)
    }
  }

  // Fetch Draft
  const fetchDraft = async (wfId) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows/${wfId}/draft/`)
      if (res.ok) {
        const data = await res.json()
        setDraft(data.draft || null)
      }
    } catch (e) {
      console.error("Fetch draft error:", e)
    }
  }

  // Handle Document Upload
  const handleFileUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setIsUploading(true)
    setUploadError(null)
    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const res = await fetch(`${BACKEND_URL}/api/documents/upload/`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setUploadedDoc(data.document)
        fetchHealth()
      } else {
        setUploadError(data.error || 'Upload failed')
      }
    } catch (err) {
      setUploadError('Network error uploading document')
    } finally {
      setIsUploading(false)
    }
  }

  // 1-Click Quick Demo Handler for Hackathon Presentations
  const handleQuickDemo = async () => {
    const sampleText = `PROJECT SPECIFICATION & SYSTEM ARCHITECTURE PROPOSAL
Title: J.A.R.V.I.S. Autonomous Multi-Agent AI Intelligence Platform
Author: Suraj M N (Lead AI Systems Architect)
Contact: sn740698@gmail.com | Location: Bengaluru, Karnataka
Category: Multi-Agent AI & System Architecture Proposal

EXECUTIVE OVERVIEW:
This proposal details the design and deployment of J.A.R.V.I.S.—an autonomous multi-agent AI system powered by LangGraph, local Ollama Llama 3.2 GGUF models, ChromaDB vector indexing, and a 5-Agent Zero-Hallucination Audit Framework.

CORE SYSTEM MODULES & CAPABILITIES:
1. Document Decomposer Agent: Multi-part structural section partitioning and canonical entity extraction across 4 structural boundaries.
2. Vector Knowledge Retrieval Agent: 2-stage ChromaDB vector search + DistilBERT contextual re-ranking for precise context retrieval.
3. Layman Simplifier Agent: Plain-English executive summary generation tailored for rapid decision-making.
4. Executive Summary Drafter & Fact Verification Agent: Automated synthesis of structured project proposals and verification against ground-truth facts.
5. Hallucination Audit Agent: Real-time NLI cross-verification guardrail ensuring 100% zero hallucinations.

KEY HIGHLIGHTS & OUTCOMES:
- Built full-stack platform using Python, React JS, Django REST Framework, Tailwind CSS, Git, and GitHub.
- Integrated local GGUF models via Ollama to ensure complete offline privacy and zero API key dependencies.
- Demonstrated zero-refusal conversational capability for general knowledge, coding, and document analysis queries.

RECOMMENDED NEXT STEPS:
- Deploy production containerized service across edge nodes.
- Expand multi-agent state graph with specialized tool-calling capabilities.`

    const blob = new Blob([sampleText], { type: 'text/plain' })
    const file = new File([blob], "hackathon_demo_proposal.txt", { type: "text/plain" })
    
    setIsUploading(true)
    setUploadError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${BACKEND_URL}/api/documents/upload/`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setUploadedDoc(data.document)
        fetchHealth()
        // Automatically trigger workflow analysis
        setIsAnalyzing(true)
        setWorkflowStatus(null)
        setInsights([])
        setDraft(null)
        setAgentLogs([])
        const wfRes = await fetch(`${BACKEND_URL}/api/workflows/analyze/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ document_id: data.document.id })
        })
        const wfData = await wfRes.json()
        if (wfRes.ok) {
          setActiveWorkflowId(wfData.workflow_id)
        }
      }
    } catch (err) {
      setUploadError('Failed to launch quick demo')
    } finally {
      setIsUploading(false)
    }
  }

  // Start Multi-Agent LangGraph Workflow
  const handleStartAnalysis = async () => {
    if (!uploadedDoc) return

    setIsAnalyzing(true)
    setWorkflowStatus(null)
    setInsights([])
    setDraft(null)
    setAgentLogs([])

    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows/analyze/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: uploadedDoc.id })
      })
      const data = await res.json()
      if (res.ok) {
        setActiveWorkflowId(data.workflow_id)
      } else {
        setIsAnalyzing(false)
        alert(`Analysis failed to start: ${data.error}`)
      }
    } catch (err) {
      setIsAnalyzing(false)
      alert('Network error starting workflow analysis')
    }
  }

  // Trigger Draft Regeneration
  const handleRegenerateDraft = async () => {
    if (!activeWorkflowId) return
    setIsRegenerating(true)

    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows/${activeWorkflowId}/regenerate/`, {
        method: 'POST'
      })
      if (res.ok) {
        setIsAnalyzing(true)
        setWorkflowStatus(prev => ({ ...prev, status: 'PROCESSING' }))
      }
    } catch (err) {
      alert('Failed to trigger regeneration')
    } finally {
      setIsRegenerating(false)
    }
  }

  // Determine current active agent index
  const getAgentStatus = (agentId) => {
    if (!workflowStatus) return 'idle'
    if (workflowStatus.status === 'COMPLETED') return 'completed'
    if (workflowStatus.current_agent === agentId || workflowStatus.current_supervisor === agentId) return 'working'
    
    // Check if agent already executed in routing log
    if (agentLogs.some(log => log.target === agentId || log.supervisor === agentId)) {
      return 'completed'
    }
    return 'idle'
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <span className="logo-icon">🤖</span>
          <div>
            <h1>J.A.R.V.I.S. Multi-Agent AI Intelligence Platform</h1>
            <p className="subtitle">LangGraph StateGraph + 5-Agent Anti-Hallucination Framework + Ollama Llama 3.2 GGUF</p>
          </div>
        </div>

        <div className="header-status-group">
          <div className={`status-badge ${health.status === 'healthy' ? 'online' : 'offline'}`}>
            <span className="dot"></span>
            {health.status === 'healthy' ? 'Django API: Connected' : 'API: Offline'}
          </div>

          <div className={`status-badge ${health.ollama?.connected ? 'active' : 'warn'}`}>
            🤖 Ollama: {health.ollama?.connected ? 'Llama 3.2 GGUF Ready' : 'LLM Missing'}
          </div>

          <div className="status-badge db-badge">
            📦 Vector Store: {health.vectorstore?.indexed_chunks || 0} Chunks
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="main-grid">
        {/* Step 1: Upload & Document Intake */}
        <div className="card">
          <h2>1. Document Intake & Problem Context</h2>
          <p className="card-desc">Upload any document (PDF, DOCX, TXT) or type questions directly to J.A.R.V.I.S.</p>

          <form onSubmit={handleFileUpload} className="upload-form">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setSelectedFile(e.target.files[0])}
            />
            <button type="submit" className="primary-btn" disabled={isUploading || !selectedFile}>
              {isUploading ? 'Uploading & Indexing...' : '📥 Upload & Index Document'}
            </button>
          </form>

          <div style={{ marginTop: '12px' }}>
            <button 
              type="button" 
              className="action-btn" 
              onClick={handleQuickDemo}
              disabled={isUploading || isAnalyzing}
              style={{ width: '100%', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: '#fff', fontWeight: 'bold' }}
            >
              ⚡ 1-Click Hackathon Quick Demo
            </button>
          </div>

          {uploadError && <div className="status-msg error">{uploadError}</div>}

          {uploadedDoc && (
            <div className="doc-summary-box">
              <h3>📄 Document Intake Summary</h3>
              <div className="info-row"><span>Filename:</span> <strong>{uploadedDoc.filename}</strong></div>
              <div className="info-row"><span>Document ID:</span> <code>{uploadedDoc.id}</code></div>
              <div className="info-row"><span>Status:</span> <span className="tag green">{uploadedDoc.status}</span></div>

              <button
                className="action-btn"
                onClick={handleStartAnalysis}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? '⚡ LangGraph Agents Working...' : '🚀 Launch Multi-Agent Workflow'}
              </button>
            </div>
          )}
        </div>

        {/* Live Multi-Agent Execution Visualizer */}
        <div className="card">
          <div className="card-header-flex">
            <h2>2. Live LangGraph Multi-Agent Pipeline</h2>
            {isAnalyzing && (
              <span className="live-pulse-badge">
                <span className="pulse-dot"></span> AGENTS ACTIVE & WORKING
              </span>
            )}
          </div>
          <p className="card-desc">Real-time status of supervisors and specialized agents executing in parallel.</p>

          {/* Interactive Agent Pipeline Cards */}
          <div className="agent-pipeline-grid">
            {AGENTS.map((agent) => {
              const status = getAgentStatus(agent.id)
              return (
                <div key={agent.id} className={`agent-node-card ${status}`}>
                  <div className="agent-node-header">
                    <span className="agent-icon">{agent.icon}</span>
                    <div className="agent-title-wrap">
                      <strong className="agent-name">{agent.name}</strong>
                      <span className="agent-role">{agent.role}</span>
                    </div>
                    <span className={`status-pill ${status}`}>
                      {status === 'working' ? 'WORKING...' : status === 'completed' ? '✓ DONE' : 'IDLE'}
                    </span>
                  </div>
                  <p className="agent-desc">{agent.desc}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Real-time Agent Activity Stream */}
        <div className="card full-width">
          <h2>3. Live Agent Activity & Supervisor Decision Stream</h2>
          <p className="card-desc">Real-time reasoning logs, routing choices, and task delegations between agents.</p>

          {agentLogs.length === 0 ? (
            <div className="empty-placeholder">
              <p>Agent activity logs will stream here live when you launch a workflow.</p>
            </div>
          ) : (
            <div className="agent-log-feed">
              {agentLogs.map((log, idx) => (
                <div key={idx} className="agent-log-entry">
                  <div className="log-time-badge">{log.time}</div>
                  <div className="log-body">
                    <div className="log-flow">
                      <span className="sup-tag">{log.supervisor}</span>
                      <span className="arrow">➔</span>
                      <span className="tgt-tag">{log.target}</span>
                    </div>
                    <p className="log-reason">{log.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Step 4: Multi-Part Document Division & Structural Section Breakdown */}
        <div className="card full-width">
          <h2>4. Document Decomposer Agent: Multi-Part Structural Section Breakdown</h2>
          <p className="card-desc">Document automatically partitioned into 4 universal structural sections to guide agent reasoning & RAG context.</p>

          {workflowStatus?.document_sections && Object.keys(workflowStatus.document_sections).length > 0 ? (
            <div className="insights-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
              <div className="insight-card" style={{ borderLeft: '4px solid var(--accent-blue)' }}>
                <div className="insight-header">
                  <span className="field-name">🏛️ Title & Metadata Section</span>
                </div>
                <div className="field-val" style={{ fontSize: '13px', fontWeight: 'normal', color: 'var(--text-main)', lineHeight: '1.4' }}>
                  {workflowStatus.document_sections.header_metadata || workflowStatus.document_sections.title_header || 'None'}
                </div>
              </div>

              <div className="insight-card" style={{ borderLeft: '4px solid var(--accent-purple)' }}>
                <div className="insight-header">
                  <span className="field-name">📋 Core Content & Main Body</span>
                </div>
                <div className="field-val" style={{ fontSize: '13px', fontWeight: 'normal', color: 'var(--text-main)', lineHeight: '1.4' }}>
                  {workflowStatus.document_sections.line_items || workflowStatus.document_sections.core_details || 'None'}
                </div>
              </div>

              <div className="insight-card" style={{ borderLeft: '4px solid var(--accent-green)' }}>
                <div className="insight-header">
                  <span className="field-name">🎯 Core Skills & Key Topics</span>
                </div>
                <div className="field-val" style={{ fontSize: '13px', fontWeight: 'normal', color: 'var(--text-main)', lineHeight: '1.4' }}>
                  {workflowStatus.document_sections.financial_totals || workflowStatus.document_sections.key_topics || 'None'}
                </div>
              </div>

              <div className="insight-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                <div className="insight-header">
                  <span className="field-name">⚡ Action Items & Next Steps</span>
                </div>
                <div className="field-val" style={{ fontSize: '13px', fontWeight: 'normal', color: 'var(--text-main)', lineHeight: '1.4' }}>
                  {workflowStatus.document_sections.terms_penalties || workflowStatus.document_sections.action_items || 'None'}
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-placeholder">
              <p>Multi-part document division breakdown will appear here once Document Decomposer Agent processes the document.</p>
            </div>
          )}
        </div>

        {/* Step 5: Extracted Document Facts & Insights */}
        <div className="card full-width">
          <h2>5. Document Decomposer Agent: Extracted Key Insights & Document Facts ({insights.length})</h2>
          <p className="card-desc">Universal document fields and canonical entity facts extracted with confidence scores & source attribution.</p>

          {insights.length === 0 ? (
            <div className="empty-placeholder">
              <p>Document facts and insights will appear here once the Document Decomposer Agent completes extraction.</p>
            </div>
          ) : (
            <div className="insights-grid">
              {insights.map((ins, idx) => (
                <div key={idx} className={`insight-card ${ins.field_value ? 'has-val' : 'missing'}`}>
                  <div className="insight-header">
                    <span className="field-name">{ins.field_name}</span>
                    <span className="confidence-pill">{(ins.confidence * 100).toFixed(0)}% Conf</span>
                  </div>
                  <div className="field-val">
                    {ins.field_value !== null ? String(ins.field_value) : <span className="null-val">null</span>}
                  </div>
                  <div className="source-tag">Source: {ins.source}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Step 6: Fact-Checked Executive Summary & Action Plan Draft */}
        <div className="card full-width">
          <div className="card-header-flex">
            <h2>6. Executive Summary Drafter & Fact Verification Agent: Executive Summary & Action Plan Draft</h2>
            {draft && (
              <button
                className="secondary-btn"
                onClick={handleRegenerateDraft}
                disabled={isRegenerating || isAnalyzing}
              >
                {isRegenerating ? 'Regenerating...' : '🔄 Regenerate Draft'}
              </button>
            )}
          </div>
          <p className="card-desc">Executive summary & action plan draft synthesized by LLMRouter (Llama 3.2 1B Primary) and verified by FactVerificationAgent.</p>

          {draft ? (
            <div className="draft-container">
              <div className="draft-meta-bar">
                <span className="meta-tag">Model: <strong>{draft.llm_model}</strong></span>
                <span className="meta-tag">Validation Status: <strong className="green">{draft.validation_status}</strong></span>
                <span className="meta-tag">Attempt #: <strong>{draft.generation_attempt}</strong></span>
              </div>

              <div className="draft-text-box">
                <pre>{draft.draft_text}</pre>
              </div>
            </div>
          ) : (
            <div className="empty-placeholder">
              <p>Executive summary & action plan draft will appear here once Communication Orchestrator & Executive Summary Drafter Agent complete.</p>
            </div>
          )}
        </div>

        {/* Step 7: Layman Simplifier Agent */}
        <div className="card full-width">
          <h2>7. Layman Simplifier Agent: Plain-English Executive Summary</h2>
          <p className="card-desc">Layman summary breaking down document takeaways, key entities, and actionable recommendations.</p>

          {workflowStatus?.simplified_summary ? (
            <div className="summary-box">
              <div className="summary-text-box">
                {workflowStatus.simplified_summary}
              </div>
            </div>
          ) : (
            <div className="empty-placeholder">
              <p>Plain-English simplified summary will appear here once Layman Simplifier Agent completes.</p>
            </div>
          )}
        </div>

        {/* Step 8: Interactive Document & General Chatbot */}
        <div className="card full-width">
          <h2>8. J.A.R.V.I.S. Interactive AI & Problem Solving Assistant</h2>
          <p className="card-desc">Ask J.A.R.V.I.S. anything—general knowledge, complex code, real-world questions, or grounded document queries.</p>

          <div className="chatbot-container">
            {/* Quick Suggestion Chips */}
            <div className="chat-chips-group">
              <button className="chip-btn" onClick={() => handleSendChatMessage("What is the theory of relativity and how does time dilation work?")}>
                🌍 General Knowledge
              </button>
              <button className="chip-btn" onClick={() => handleSendChatMessage("How do I implement binary search in Python with O(log n) complexity?")}>
                💻 Coding & Tech
              </button>
              <button className="chip-btn" onClick={() => handleSendChatMessage("What is the total balance due and payment deadline in the document?")}>
                📄 Document Analysis
              </button>
              <button className="chip-btn" onClick={() => handleSendChatMessage("Summarize the key decisions and recommended next action items.")}>
                ⚡ Action Items
              </button>
            </div>

            {/* Message History */}
            <div className="chat-history">
              {chatMessages.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0', fontSize: '13px' }}>
                  💬 Ask J.A.R.V.I.S. any question! Click a suggestion chip above or type your prompt below.
                </div>
              ) : (
                chatMessages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.sender}`}>
                    <div className="msg-text">{msg.text}</div>
                    <div className="chat-meta">
                      <span>{msg.time}</span>
                      {msg.model && <span>• Model: {msg.model}</span>}
                      {msg.sources && msg.sources.length > 0 && <span>• Sources: {msg.sources.join(', ')}</span>}
                    </div>
                  </div>
                ))
              )}
              {isChatting && (
                <div className="chat-bubble bot" style={{ fontStyle: 'italic', color: 'var(--accent-blue)' }}>
                  🤖 J.A.R.V.I.S. (Llama 3.2 1B GGUF) thinking & auditing response against anti-hallucination guardrails...
                </div>
              )}
            </div>

            {/* Input Form */}
            <form onSubmit={(e) => { e.preventDefault(); handleSendChatMessage(); }} className="chat-input-form">
              <input
                type="text"
                className="chat-input-field"
                placeholder="Ask J.A.R.V.I.S. anything! General knowledge, code, real-world questions, or document analysis..."
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
    </div>
  )
}

export default App
