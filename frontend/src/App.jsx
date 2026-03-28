import { useState, useEffect, useRef } from 'react'
import { motion, useInView, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts'
import {
  Shield, Search, Brain, Eye, Database, Zap,
  AlertTriangle, CheckCircle, Clock, ArrowRight,
  FileText, Lock, Activity, Send, ChevronDown
} from 'lucide-react'
import axios from 'axios'
import './App.css'

const API_BASE = '/api'

/* ═══════════════════════════════════════════
   ANIMATED SECTION WRAPPER
   ═══════════════════════════════════════════ */
function FadeInSection({ children, delay = 0, className = '' }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{ duration: 0.7, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      {children}
    </motion.div>
  )
}

/* ═══════════════════════════════════════════
   SHIELD LOGO SVG
   ═══════════════════════════════════════════ */
function ShieldLogo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(59,130,246,0.15)" stroke="#3b82f6" />
      <path d="M9 12l2 2 4-4" stroke="#5eb0ff" />
    </svg>
  )
}

/* ═══════════════════════════════════════════
   CONNECTING LINES CANVAS
   ═══════════════════════════════════════════ */
function ConnectingLines() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1

    function resize() {
      const rect = canvas.parentElement.getBoundingClientRect()
      canvas.width = rect.width * dpr
      canvas.height = 120 * dpr
      canvas.style.width = rect.width + 'px'
      canvas.style.height = '120px'
      ctx.scale(dpr, dpr)
    }

    resize()

    let frame = 0
    function draw() {
      const w = canvas.width / dpr
      const h = canvas.height / dpr
      ctx.clearRect(0, 0, w, h)

      const centerX = w / 2
      const points = [w * 0.12, w * 0.37, w * 0.63, w * 0.88]

      points.forEach((px, i) => {
        ctx.beginPath()
        ctx.moveTo(centerX, 0)
        const cp1x = centerX + (px - centerX) * 0.3
        const cp1y = h * 0.4
        const cp2x = px - (px - centerX) * 0.2
        const cp2y = h * 0.7
        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, px, h - 10)

        const gradient = ctx.createLinearGradient(centerX, 0, px, h)
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)')
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.1)')

        ctx.strokeStyle = gradient
        ctx.lineWidth = 1.5
        ctx.stroke()

        // Animated dot
        const t = ((frame + i * 30) % 120) / 120
        const dotX = Math.pow(1-t, 3) * centerX +
                     3 * Math.pow(1-t, 2) * t * cp1x +
                     3 * (1-t) * Math.pow(t, 2) * cp2x +
                     Math.pow(t, 3) * px
        const dotY = Math.pow(1-t, 3) * 0 +
                     3 * Math.pow(1-t, 2) * t * cp1y +
                     3 * (1-t) * Math.pow(t, 2) * cp2y +
                     Math.pow(t, 3) * (h - 10)

        ctx.beginPath()
        ctx.arc(dotX, dotY, 3, 0, Math.PI * 2)
        ctx.fillStyle = '#5eb0ff'
        ctx.shadowColor = '#3b82f6'
        ctx.shadowBlur = 10
        ctx.fill()
        ctx.shadowBlur = 0
      })

      frame++
      requestAnimationFrame(draw)
    }

    draw()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])

  return <canvas ref={canvasRef} style={{ position: 'absolute', top: 0, left: 0, width: '100%', pointerEvents: 'none' }} />
}

/* ═══════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════ */
function App() {
  const [comment, setComment] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [auditLogs, setAuditLogs] = useState([])
  const [health, setHealth] = useState(null)
  const [activeFeature, setActiveFeature] = useState('hybrid')
  const analysisRef = useRef(null)
  const featuresRef = useRef({ hybrid: null, pii: null, audit: null, cache: null })

  // Fetch health + audit on mount
  useEffect(() => {
    axios.get(`${API_BASE}/health`).then(r => setHealth(r.data)).catch(() => {})
    fetchAuditLogs()
  }, [])

  function fetchAuditLogs() {
    axios.get(`${API_BASE}/audit-logs?limit=20`).then(r => setAuditLogs(r.data)).catch(() => {})
  }

  async function analyzeComment() {
    if (!comment.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await axios.post(`${API_BASE}/predict`, { comment: comment.trim() })
      setResult(res.data)
      fetchAuditLogs()
    } catch (err) {
      setResult({ error: err.response?.data?.detail || 'API connection failed. Is the backend running?' })
    }
    setLoading(false)
  }

  function scrollToAnalysis() {
    analysisRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const demos = [
    { label: '😡 Harassment', text: 'You idiot manager, you deserve to be fired!' },
    { label: '✅ Safe', text: 'Great teamwork on the Q3 deliverables everyone.' },
    { label: '⚠️ Threat', text: "I'll destroy you and this entire department!" },
    { label: '🤝 Neutral', text: 'Please review the attached document at your convenience.' },
  ]

  const chartData = result && !result.error ? [
    { name: 'ML Model', score: Math.round(result.ml_score * 100), color: '#3b82f6' },
    { name: 'LLM (BERT)', score: Math.round(result.llm_confidence * 100), color: '#5eb0ff' },
    { name: 'Hybrid', score: Math.round(result.hybrid_score * 100), color: result.is_toxic ? '#ef4444' : '#22c55e' },
  ] : []

  const featureBlocks = [
    {
      id: 'hybrid',
      icon: <Brain size={22} />,
      title: 'Hybrid Intelligence',
      label: 'ML + LLM',
      desc: 'Combines the speed of traditional ML with the contextual depth of transformer-based LLMs. The Fast ML Layer uses TF-IDF vectorization with balanced Logistic Regression for rapid initial scoring. The Deep LLM Layer leverages Toxic-BERT for nuanced contextual analysis.',
      items: [
        'ML Fast Path: TF-IDF + LogisticRegression (88.6% accuracy)',
        'LLM Deep Path: unitary/toxic-bert (95% F1 Score)',
        'Weighted Ensemble: (ML × 0.3) + (LLM × 0.7) = Hybrid Score',
        'Tri-level Risk Classification: HIGH / MEDIUM / LOW',
        'Automatic Corporate Policy Mapping'
      ]
    },
    {
      id: 'pii',
      icon: <Lock size={22} />,
      title: 'PII Protection',
      label: 'Presidio',
      desc: 'All text is anonymized by Microsoft Presidio before it reaches any ML or LLM model. Personally Identifiable Information is automatically stripped, ensuring no employee names, emails, or sensitive data ever enters the analysis pipeline.',
      items: [
        'Real-time PII detection using Microsoft Presidio NLP engine',
        'Automatic masking of: Names, Emails, Phone Numbers, SSNs',
        'Privacy-first architecture: PII stripped before model inference',
        'Anonymized text preserved in the audit trail'
      ]
    },
    {
      id: 'audit',
      icon: <Database size={22} />,
      title: 'Enterprise Audit Trail',
      label: 'SQLite',
      desc: 'Every inference result is immutably logged to a local SQLite database with full metadata — including the anonymized input, ML/LLM scores, risk level, and policy violation. This creates a tamper-evident compliance trail for HR and legal.',
      items: [
        'SQLAlchemy ORM with structured inference_logs table',
        'Timestamped entries: masked text, scores, risk, policy flags',
        'Queryable via API: GET /audit-logs with configurable limits',
        'Persistent local storage: data/corporate_audit.db'
      ]
    },
    {
      id: 'cache',
      icon: <Zap size={22} />,
      title: 'Intelligent Caching',
      label: 'Memory',
      desc: 'Repeated comment submissions bypass the heavy ML + LLM pipeline entirely, returning cached results in under 1ms. The enterprise cache tracks hit/miss ratios for operational monitoring.',
      items: [
        'In-memory dictionary cache for instant repeat lookups',
        'Bypass both ML and LLM inference on cache hit',
        'Sub-millisecond response time for cached results',
        'Hit/Miss metrics exposed via /health endpoint'
      ]
    }
  ]

  return (
    <>
      {/* ══════════ NAVBAR ══════════ */}
      <nav className="navbar">
        <a href="#" className="navbar-logo">
          <ShieldLogo />
          ToxicGuard
        </a>
        <ul className="navbar-links">
          <li><a href="#features">Features</a></li>
          <li><a href="#analysis">Analyze</a></li>
          <li><a href="#audit">Audit Log</a></li>
          <li>
            {health ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#22c55e', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                <span className="status-dot online" /> System Online
              </span>
            ) : (
              <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                Connecting...
              </span>
            )}
          </li>
        </ul>
        <div className="navbar-cta">
          <button className="btn btn-primary" onClick={scrollToAnalysis}>
            <Search size={15} />
            Analyze Now
          </button>
        </div>
      </nav>

      {/* ══════════ HERO ══════════ */}
      <section className="hero">
        <div className="hero-bg" />

        <motion.div
          className="hero-content"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <h1>
            Protect your<br />
            workplace from <span className="glow-word">toxicity</span>
          </h1>
          <p className="hero-subtitle">
            Detect, analyze, and prevent toxic communication
            with our enterprise-grade Hybrid ML + LLM engine.
            Built for compliance. Powered by intelligence.
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={scrollToAnalysis}>
              Start analyzing
              <ArrowRight size={16} />
            </button>
            <a href="#features" className="btn btn-secondary btn-lg">
              Explore features
              <ChevronDown size={16} />
            </a>
          </div>
        </motion.div>

        <motion.div
          className="hero-features"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
        >
          <ConnectingLines />
          <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', width: '100%', paddingTop: 120, zIndex: 1 }}>
            {[
              { icon: <Search size={14} />, label: 'Detect' },
              { icon: <Brain size={14} />, label: 'Analyze' },
              { icon: <Shield size={14} />, label: 'Protect' },
              { icon: <FileText size={14} />, label: 'Audit' },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                className="feature-pill"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 1 + i * 0.15 }}
                style={{ zIndex: 1 }}
              >
                {item.icon}
                {item.label}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ══════════ LIVE ANALYSIS ══════════ */}
      <section className="analysis-section" id="analysis" ref={analysisRef}>
        <div className="section" style={{ maxWidth: 1280 }}>
          <FadeInSection>
            <span className="section-label">
              <Activity size={14} />
              Live Analysis
            </span>
            <h2 className="section-title">Test the engine</h2>
            <p className="section-description" style={{ marginBottom: 48 }}>
              Enter any text to run it through the full Hybrid ML + LLM pipeline with PII protection.
            </p>
          </FadeInSection>

          <FadeInSection delay={0.15}>
            <div className="analysis-container">
              {/* INPUT */}
              <div className="analysis-input-card">
                <div className="input-label">
                  <Send size={14} />
                  Comment Input
                </div>
                <textarea
                  className="analysis-textarea"
                  placeholder="Enter a comment to analyze for toxicity..."
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) analyzeComment() }}
                />

                <div className="demo-buttons">
                  {demos.map(d => (
                    <button key={d.label} className="demo-btn" onClick={() => setComment(d.text)}>
                      {d.label}
                    </button>
                  ))}
                </div>

                <div className="analyze-btn-container">
                  <button
                    className="btn btn-accent btn-lg"
                    onClick={analyzeComment}
                    disabled={loading || !comment.trim()}
                    style={{ flex: 1, justifyContent: 'center', opacity: loading || !comment.trim() ? 0.5 : 1 }}
                  >
                    {loading ? (
                      <>
                        <div className="loading-spinner" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Shield size={16} />
                        Detect Toxicity
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* RESULTS */}
              <div className="results-panel">
                <AnimatePresence mode="wait">
                  {result && !result.error ? (
                    <motion.div
                      key="results"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.5 }}
                    >
                      {/* STATUS + HYBRID SCORE */}
                      <div className="result-card" style={{ marginBottom: 20 }}>
                        <div className="result-card-header">
                          <span className="result-card-title">Hybrid Score</span>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span className={`risk-badge ${result.is_toxic ? 'toxic-badge' : 'safe-badge'}`}>
                              {result.is_toxic ? <AlertTriangle size={12} /> : <CheckCircle size={12} />}
                              {result.is_toxic ? 'TOXIC' : 'SAFE'}
                            </span>
                            <span className={`risk-badge risk-${result.risk_level.toLowerCase()}`}>
                              {result.risk_level}
                            </span>
                          </div>
                        </div>

                        <div className="score-display">
                          <span className="score-value" style={{ color: result.is_toxic ? 'var(--danger)' : 'var(--success)' }}>
                            {Math.round(result.hybrid_score * 100)}
                          </span>
                          <span className="score-unit">%</span>
                        </div>

                        <div className="score-bar">
                          <div
                            className="score-bar-fill"
                            style={{
                              width: `${result.hybrid_score * 100}%`,
                              background: result.is_toxic
                                ? 'linear-gradient(90deg, #ef4444, #f87171)'
                                : 'linear-gradient(90deg, #22c55e, #4ade80)'
                            }}
                          />
                        </div>

                        {/* ML vs LLM */}
                        <div className="scores-grid" style={{ marginTop: 20 }}>
                          <div className="score-item">
                            <div className="score-item-label">ML Model</div>
                            <div className="score-item-value" style={{ color: '#3b82f6' }}>
                              {Math.round(result.ml_score * 100)}%
                            </div>
                          </div>
                          <div className="score-item">
                            <div className="score-item-label">LLM (BERT)</div>
                            <div className="score-item-value" style={{ color: '#5eb0ff' }}>
                              {Math.round(result.llm_confidence * 100)}%
                            </div>
                          </div>
                        </div>

                        {/* BAR CHART */}
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} barCategoryGap="30%">
                              <XAxis
                                dataKey="name"
                                tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                                axisLine={{ stroke: '#1e293b' }}
                                tickLine={false}
                              />
                              <YAxis
                                domain={[0, 100]}
                                tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                                axisLine={{ stroke: '#1e293b' }}
                                tickLine={false}
                              />
                              <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                                {chartData.map((entry, i) => (
                                  <Cell key={i} fill={entry.color} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* POLICY VIOLATION */}
                      <div className={`result-card policy-card ${!result.is_toxic ? 'safe' : ''}`} style={{ marginBottom: 20 }}>
                        <div className="result-card-header">
                          <span className="result-card-title">Policy Analysis</span>
                        </div>
                        <p className="policy-text" style={{ fontWeight: 600, color: result.is_toxic ? 'var(--danger)' : 'var(--success)', marginBottom: 8 }}>
                          {result.policy_violation}
                        </p>
                        <p className="policy-text">
                          {result.llm_explanation}
                        </p>
                      </div>

                      {/* PII + PERF */}
                      <div className="result-card">
                        <div className="result-card-header">
                          <span className="result-card-title">Privacy & Performance</span>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <span className={`latency-tag ${result.cached ? 'cache-hit' : ''}`}>
                              <Clock size={11} />
                              {result.latency_ms.toFixed(1)}ms
                            </span>
                            {result.cached && (
                              <span className="latency-tag cache-hit">
                                <Zap size={11} />
                                Cache Hit
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="masked-preview">
                          <span style={{ color: 'var(--accent-light)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 6 }}>
                            🛡️ PII-Masked Input
                          </span>
                          {result.masked_comment}
                        </div>
                      </div>
                    </motion.div>
                  ) : result?.error ? (
                    <motion.div
                      key="error"
                      className="result-card"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}
                    >
                      <div className="result-card-header">
                        <span className="result-card-title" style={{ color: 'var(--danger)' }}>Connection Error</span>
                      </div>
                      <p className="policy-text">{result.error}</p>
                      <p className="policy-text" style={{ marginTop: 8, fontSize: 13 }}>
                        Run: <code style={{ background: 'var(--bg-surface)', padding: '2px 8px', borderRadius: 4, fontFamily: 'var(--font-mono)', color: 'var(--accent-light)' }}>
                          uvicorn src.api.main:app --reload
                        </code>
                      </p>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      className="result-card"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <div className="empty-state">
                        <Eye size={48} />
                        <p>Enter a comment and click "Detect Toxicity" to see the analysis</p>
                        <p style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                          Ctrl+Enter to submit
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ══════════ FEATURES (LangChain-Style Sidebar Nav) ══════════ */}
      <section className="features-section" id="features">
        <div className="section">
          <FadeInSection>
            <span className="section-label">
              <Brain size={14} />
              Architecture
            </span>
            <h2 className="section-title">Enterprise-grade under the hood</h2>
            <p className="section-description" style={{ marginBottom: 60 }}>
              Every component is production-ready. No prototypes. No placeholders.
            </p>
          </FadeInSection>

          <div className="features-layout">
            {/* SIDEBAR NAV */}
            <div className="features-sidebar">
              <ul className="features-nav">
                {featureBlocks.map(f => (
                  <li key={f.id}>
                    <a
                      href={`#feature-${f.id}`}
                      className={activeFeature === f.id ? 'active' : ''}
                      onClick={e => {
                        e.preventDefault()
                        setActiveFeature(f.id)
                        featuresRef.current[f.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                      }}
                    >
                      {f.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* FEATURE CONTENT */}
            <div>
              {featureBlocks.map((f, i) => (
                <FadeInSection key={f.id} delay={i * 0.1}>
                  <div
                    className="feature-block"
                    id={`feature-${f.id}`}
                    ref={el => featuresRef.current[f.id] = el}
                  >
                    <div className="feature-block-header">
                      <div className="feature-icon">{f.icon}</div>
                      <span className="section-label" style={{ marginBottom: 0 }}>{f.label}</span>
                    </div>
                    <h3>{f.title}</h3>
                    <p>{f.desc}</p>
                    <ul className="feature-list">
                      {f.items.map((item, j) => (
                        <li key={j}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </FadeInSection>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══════════ AUDIT LOG ══════════ */}
      <section className="audit-section" id="audit">
        <div className="section">
          <FadeInSection>
            <span className="section-label">
              <Database size={14} />
              Compliance
            </span>
            <h2 className="section-title">Audit trail</h2>
            <p className="section-description">
              Every analysis is logged to the enterprise audit database for compliance review.
            </p>
          </FadeInSection>

          <FadeInSection delay={0.15}>
            <div className="audit-table-container">
              {auditLogs.length > 0 ? (
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Timestamp</th>
                      <th>Masked Text</th>
                      <th>ML Score</th>
                      <th>LLM</th>
                      <th>Hybrid</th>
                      <th>Risk</th>
                      <th>Policy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map(log => (
                      <tr key={log.id}>
                        <td>#{log.id}</td>
                        <td>{log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}</td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {log.original_text_masked}
                        </td>
                        <td>{log.ml_score != null ? `${(log.ml_score * 100).toFixed(0)}%` : '—'}</td>
                        <td>{log.llm_confidence != null ? `${(log.llm_confidence * 100).toFixed(0)}%` : '—'}</td>
                        <td style={{ color: log.hybrid_score > 0.5 ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }}>
                          {log.hybrid_score != null ? `${(log.hybrid_score * 100).toFixed(0)}%` : '—'}
                        </td>
                        <td>
                          <span className={`risk-badge risk-${(log.risk_level || 'low').toLowerCase()}`} style={{ fontSize: 10, padding: '3px 8px' }}>
                            {log.risk_level || '—'}
                          </span>
                        </td>
                        <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {log.policy_violation || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <FileText size={48} />
                  <p>No audit logs yet. Run an analysis to start building the compliance trail.</p>
                </div>
              )}
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ══════════ FOOTER ══════════ */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-logo">
            <ShieldLogo size={22} />
            ToxicGuard
          </div>
          <p className="footer-text">
            Corporate Toxic Comment Detector — Hybrid ML + GenAI Engine
          </p>
          <p className="footer-text" style={{ fontSize: 12 }}>
            Internal Use Only • SIH 2024 Digital Safety
          </p>
          {health && (
            <p className="footer-text" style={{ fontSize: 12, color: 'var(--success)' }}>
              <span className="status-dot online" style={{ marginRight: 6 }} />
              ML: 88.6% • LLM: 95% F1 • Cache: {health.cache_hits} hits / {health.cache_misses} misses • Uptime: {health.uptime}
            </p>
          )}
        </div>
      </footer>
    </>
  )
}

export default App
