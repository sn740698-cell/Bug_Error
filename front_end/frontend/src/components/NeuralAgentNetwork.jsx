import React, { useState, useEffect, useRef } from 'react'
import './NeuralAgentNetwork.css'

const NEURAL_NODES = [
  {
    id: 'ingestion',
    name: 'Agent 1: IngestionAgent',
    role: 'Input Boundary Layer',
    icon: '📥',
    layer: 1,
    desc: 'Query normalization, tenant context validation & memory initialization.',
    prompt: 'You are Agent 1: IngestionAgent. Validate user context and normalize query.'
  },
  {
    id: 'decomposition',
    name: 'Agent 2: DecompositionAgent',
    role: 'Atomic Partitioning Layer',
    icon: '📑',
    layer: 2,
    desc: 'Breaks query into subtasks and identifies dependency retrieval targets.',
    prompt: 'You are Agent 2: DecompositionAgent. Partition input query into subtasks.'
  },
  {
    id: 'rag',
    name: 'Agent 3: DomainContextRAGAgent',
    role: 'Semantic Context Layer (ChromaDB)',
    icon: '📚',
    layer: 3,
    desc: 'Queries ChromaDB vector store with strict user_id tenant filtering.',
    prompt: 'You are Agent 3: DomainContextRAGAgent. Search vector database for grounded evidence.'
  },
  {
    id: 'risk',
    name: 'Agent 4: RiskConstraintAgent',
    role: 'Security & Constraints Layer',
    icon: '🛡️',
    layer: 3,
    desc: 'Identifies security risks, edge cases, failure modes, and architectural constraints.',
    prompt: 'You are Agent 4: RiskConstraintAgent. Perform security and edge case risk audit.'
  },
  {
    id: 'planner',
    name: 'Agent 5: SynthesisPlannerAgent',
    role: 'Master Synthesis Layer',
    icon: '🏛️',
    role_type: 'supervisor',
    layer: 4,
    desc: 'Synthesizes RAG evidence, subtasks, and risks into a master solution plan.',
    prompt: 'You are Agent 5: SynthesisPlannerAgent. Build grounded solution plan & revise on retry.'
  },
  {
    id: 'solver_a',
    name: 'Agent 6: PrimaryLLMSolverAgent',
    role: 'Primary Solver (Llama 3.2 1B)',
    icon: '⚡',
    layer: 5,
    desc: 'Independently solves plan using Primary Llama 3.2 1B GGUF model (grounded in context).',
    prompt: 'You are Agent 6: PrimaryLLMSolverAgent (Llama 3.2 1B). Generate independent solution A.'
  },
  {
    id: 'solver_b',
    name: 'Agent 7: SecondaryLLMSolverAgent',
    role: 'Secondary Solver (Llama 3.2 1B Dual-Validator)',
    icon: '🔥',
    layer: 5,
    desc: 'Independently solves plan using Llama 3.2 1B GGUF model for dual-path validation.',
    prompt: 'You are Agent 7: SecondaryLLMSolverAgent (Llama 3.2 1B). Generate independent solution B.'
  },
  {
    id: 'evaluator',
    name: 'Agent 8: EvaluatorJudgeAgent',
    role: 'Anti-Hallucination Audit Layer',
    icon: '✅',
    role_type: 'evaluator',
    layer: 6,
    desc: 'Evaluates Solution A & B against context, risks & requirements via Pydantic audit.',
    prompt: 'You are Agent 8: EvaluatorJudgeAgent. Perform structured anti-hallucination evaluation.'
  }
]

export default function NeuralAgentNetwork({ activeAgentId, pipelineResult, isExecuting, onQuickDemo, onRunPipeline }) {
  const containerRef = useRef(null)
  const [nodePositions, setNodePositions] = useState({})
  const [selectedNode, setSelectedNode] = useState(null)
  const [simulationStep, setSimulationStep] = useState(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const [activeProgress, setActiveProgress] = useState({})

  // Calculate coordinates for SVG laser beam connections
  const updateNodePositions = () => {
    if (!containerRef.current) return
    const containerRect = containerRef.current.getBoundingClientRect()
    const newPositions = {}

    NEURAL_NODES.forEach((node) => {
      const el = document.getElementById(`neural-node-${node.id}`)
      if (el) {
        const rect = el.getBoundingClientRect()
        newPositions[node.id] = {
          x: rect.left + rect.width / 2 - containerRect.left,
          y: rect.top + rect.height / 2 - containerRect.top
        }
      }
    })
    setNodePositions(newPositions)
  }

  useEffect(() => {
    updateNodePositions()
    window.addEventListener('resize', updateNodePositions)
    const timeout = setTimeout(updateNodePositions, 300)
    return () => {
      window.removeEventListener('resize', updateNodePositions)
      clearTimeout(timeout)
    }
  }, [NEURAL_NODES])

  // Determine node status based on real-time execution or simulation
  const getNodeStatus = (nodeId) => {
    if (isSimulating) {
      if (simulationStep === nodeId) return 'working'
      const nodeObj = NEURAL_NODES.find(n => n.id === nodeId)
      const currentSimObj = NEURAL_NODES.find(n => n.id === simulationStep)
      if (nodeObj && currentSimObj && nodeObj.layer < currentSimObj.layer) return 'completed'
      return 'idle'
    }

    if (!isExecuting && !pipelineResult) return 'idle'
    if (isExecuting && activeAgentId === nodeId) return 'working'
    if (pipelineResult && pipelineResult.status === 'success') return 'completed'

    return 'idle'
  }

  // Animate progress percentages when agents are working
  useEffect(() => {
    let interval
    if (isSimulating || isExecuting) {
      interval = setInterval(() => {
        setActiveProgress(prev => {
          const next = { ...prev }
          NEURAL_NODES.forEach(node => {
            const status = getNodeStatus(node.id)
            if (status === 'completed') {
              next[node.id] = 100
            } else if (status === 'working') {
              const current = next[node.id] || 15
              next[node.id] = current < 90 ? current + Math.floor(Math.random() * 18 + 12) : 95
            } else {
              next[node.id] = 0
            }
          })
          return next
        })
      }, 350)
    } else if (pipelineResult && pipelineResult.status === 'success') {
      const full = {}
      NEURAL_NODES.forEach(n => full[n.id] = 100)
      setActiveProgress(full)
    } else {
      setActiveProgress({})
    }
    return () => clearInterval(interval)
  }, [isSimulating, isExecuting, simulationStep, activeAgentId, pipelineResult])

  const getAgentProgress = (nodeId) => {
    if (pipelineResult && pipelineResult.status === 'success') return 100
    const status = getNodeStatus(nodeId)
    if (status === 'completed') return 100
    if (status === 'idle') return 0
    return activeProgress[nodeId] || 65
  }

  // Interactive Neural Signal Simulation
  const runNeuralSimulation = async () => {
    if (isSimulating) return
    setIsSimulating(true)
    const steps = ['ingestion', 'decomposition', 'rag', 'risk', 'planner', 'solver_a', 'solver_b', 'evaluator']

    for (let i = 0; i < steps.length; i++) {
      setSimulationStep(steps[i])
      await new Promise(r => setTimeout(r, 800))
    }
    setSimulationStep(null)
    setIsSimulating(false)
  }

  // Helper to render SVG connection line between two nodes
  const renderBeamConnection = (fromId, toId, isFeedback = false) => {
    const p1 = nodePositions[fromId]
    const p2 = nodePositions[toId]
    if (!p1 || !p2) return null

    const statusFrom = getNodeStatus(fromId)
    const statusTo = getNodeStatus(toId)
    const isActive = (statusFrom === 'completed' && statusTo === 'working') || (statusFrom === 'working') || isSimulating

    let lineClass = 'connection-base'
    if (isFeedback) {
      lineClass = 'connection-feedback'
    } else if (isActive) {
      lineClass = 'connection-active'
    } else if (statusFrom === 'completed' && statusTo === 'completed') {
      lineClass = 'connection-completed'
    }

    // Curved cubic bezier path for smooth neural beam look
    const dx = p2.x - p1.x
    const dy = p2.y - p1.y
    const cx1 = p1.x + dx * 0.25
    const cy1 = p1.y + dy * 0.5
    const cx2 = p1.x + dx * 0.75
    const cy2 = p1.y + dy * 0.5

    const pathData = `M ${p1.x} ${p1.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p2.x} ${p2.y}`

    return (
      <path
        key={`${fromId}-${toId}`}
        d={pathData}
        className={lineClass}
      />
    )
  }

  return (
    <div className="neural-network-container" ref={containerRef}>
      <div className="neural-bg-grid" />

      {/* Header Controls */}
      <div className="neural-header">
        <div className="neural-title-group">
          <span className="neural-title-icon">⚡</span>
          <div>
            <h3>Real-Time 8-Agent Neural Work Graph</h3>
            <p className="neural-subtitle">Visualizing real-time agent execution, laser beams & parallel fan-in solver nodes</p>
          </div>
        </div>

        <div className="neural-controls">
          {onQuickDemo && (
            <button
              className="neural-btn"
              onClick={onQuickDemo}
              disabled={isSimulating || isExecuting}
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none' }}
            >
              ⚡ 1-Click Quick Demo
            </button>
          )}

          <button
            className="neural-btn"
            onClick={runNeuralSimulation}
            disabled={isSimulating || isExecuting}
          >
            {isSimulating ? '⚡ Beam Signal Firing...' : '▶️ Simulate Neural Signal'}
          </button>
        </div>
      </div>


      {/* SVG Canvas for Laser Beams */}
      <svg className="neural-svg-canvas">
        <defs>
          <linearGradient id="beamGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#818cf8" stopOpacity="1" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0.9" />
          </linearGradient>
          <linearGradient id="feedbackGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="1" />
            <stop offset="100%" stopColor="#fb7185" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Neural Edge Beams */}
        {renderBeamConnection('ingestion', 'decomposition')}
        {renderBeamConnection('decomposition', 'rag')}
        {renderBeamConnection('decomposition', 'risk')}
        {renderBeamConnection('rag', 'planner')}
        {renderBeamConnection('risk', 'planner')}
        {renderBeamConnection('planner', 'solver_a')}
        {renderBeamConnection('planner', 'solver_b')}
        {renderBeamConnection('solver_a', 'evaluator')}
        {renderBeamConnection('solver_b', 'evaluator')}
        {/* Feedback Edge from Evaluator to Planner */}
        {pipelineResult?.iterations_used > 1 && renderBeamConnection('evaluator', 'planner', True)}
      </svg>

      {/* Neural Node Layers Layout */}
      <div className="neural-nodes-layout">
        {/* Layer 1: Ingestion */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 1).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>

        {/* Layer 2: Decomposition */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 2).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>

        {/* Layer 3: RAG & Risk (Parallel) */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 3).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>

        {/* Layer 4: Planner */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 4).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>

        {/* Layer 5: Solver A & Solver B (Parallel Solvers) */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 5).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>

        {/* Layer 6: Evaluator Judge */}
        <div className="neural-layer">
          {NEURAL_NODES.filter(n => n.layer === 6).map(node => renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode))}
        </div>
      </div>

      {/* Node Inspector Modal */}
      {selectedNode && (
        <div className="node-inspector-backdrop" onClick={() => setSelectedNode(null)}>
          <div className="node-inspector-modal" onClick={e => e.stopPropagation()}>
            <div className="inspector-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '24px' }}>{selectedNode.icon}</span>
                <div>
                  <h4 style={{ margin: 0, fontSize: '16px' }}>{selectedNode.name}</h4>
                  <span style={{ fontSize: '11px', color: '#38bdf8' }}>{selectedNode.role}</span>
                </div>
              </div>
              <button className="inspector-close-btn" onClick={() => setSelectedNode(null)}>✕</button>
            </div>

            <div className="inspector-section">
              <div className="inspector-label">Agent Responsibilities</div>
              <div className="inspector-content">{selectedNode.desc}</div>
            </div>

            <div className="inspector-section">
              <div className="inspector-label">System Prompt Specification</div>
              <div className="inspector-content" style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                {selectedNode.prompt}
              </div>
            </div>

            <div className="inspector-section">
              <div className="inspector-label">Live Status & Progress</div>
              <div className="inspector-content">
                State: <strong>{getNodeStatus(selectedNode.id).toUpperCase()}</strong> ({getAgentProgress(selectedNode.id)}% Complete)
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function renderNodeCard(node, getNodeStatus, getAgentProgress, setSelectedNode) {
  const status = getNodeStatus(node.id)
  const progress = getAgentProgress(node.id)

  return (
    <div
      key={node.id}
      id={`neural-node-${node.id}`}
      className={`neural-node-card ${status}`}
      onClick={() => setSelectedNode(node)}
    >
      <div className="node-top-bar">
        <span className="node-icon-badge">{node.icon}</span>
        <span className={`node-status-badge ${status}`}>
          {status === 'working' ? 'WORKING...' : status === 'completed' ? '✓ DONE' : status === 'retry' ? '⚠️ RETRY' : 'IDLE'}
        </span>
      </div>

      <div className="node-title">
        <span>{node.name}</span>
        <span className="node-number">L{node.layer}</span>
      </div>
      <div className="node-role">{node.role}</div>
      <p className="node-desc">{node.desc}</p>

      {/* Work Progress Percentage Loading Bar */}
      <div className="agent-progress-box">
        <div className="agent-progress-label-row">
          <span className="progress-title">Work Progress</span>
          <span className={`progress-percent ${status}`}>{progress}%</span>
        </div>
        <div className="agent-progress-track">
          <div
            className={`agent-progress-fill ${status}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {status === 'working' && (
        <div className="node-preview-box">
          ⚡ Signal Firing: Processing Agent Node...
        </div>
      )}
    </div>
  )
}
