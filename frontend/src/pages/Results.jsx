import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import './Results.css'

const FEATURE_ICONS = {
  Symmetry: '⚖',
  Eyes:     '👁',
  Eyebrows: '〰',
  Nose:     '👃',
  Lips:     '💋',
  Cheeks:   '🫧',
  Jawline:  '🔲',
  Ears:     '👂',
  Forehead: '📐',
  Chin:     '🫦',
}

function scoreClass(s) {
  if (s >= 80) return 'elite'
  if (s >= 60) return 'high'
  if (s >= 40) return 'mid'
  return 'low'
}

function scoreLabel(s) {
  if (s >= 92) return 'Elite'
  if (s >= 82) return 'Very Attractive'
  if (s >= 70) return 'Attractive'
  if (s >= 55) return 'Above Average'
  if (s >= 40) return 'Average'
  return 'Needs Work'
}

function scoreColor(s) {
  if (s >= 80) return '#a78bfa'
  if (s >= 60) return '#34d399'
  if (s >= 40) return '#fbbf24'
  return '#f87171'
}

export default function Results() {
  const [scores, setScores] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedScan, setSelectedScan] = useState(null)
  const [expandedTip, setExpandedTip] = useState(null)

  const user = JSON.parse(localStorage.getItem('glowup_user') || '{}')
  const genderColor = user.gender === 'male' ? 'var(--male)' : user.gender === 'female' ? 'var(--female)' : 'var(--accent)'

  useEffect(() => {
    api.get('/scores/me').then(({ data }) => {
      setScores(data)
      if (data.length > 0) setSelectedScan(data[0])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const details = selectedScan
    ? (typeof selectedScan.details === 'string'
        ? JSON.parse(selectedScan.details || '{}')
        : selectedScan.details || {})
    : {}

  if (loading) return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" style={{ width: 28, height: 28 }} />
    </div>
  )

  if (scores.length === 0) return (
    <div className="page fade-up">
      <div className="container" style={{ textAlign: 'center', paddingTop: 80 }}>
        <p style={{ fontSize: 48, marginBottom: 16 }}>🔬</p>
        <h2 style={{ marginBottom: 12 }}>No scan results yet</h2>
        <p className="text-2" style={{ marginBottom: 24, fontSize: 14 }}>
          Run the scanner to see your Glow Score and get your PDF report.
        </p>
        <Link to="/scan" className="btn btn-primary">Go to scanner →</Link>
      </div>
    </div>
  )

  const totalScore = selectedScan?.total_score ?? 0
  const framesAnalyzed = selectedScan?.frames_analyzed ?? 0
  const genderApplied = selectedScan?.gender_applied ?? user.gender

  return (
    <div className="results-page page fade-up">
      <div className="container">

        {/* ── Header ── */}
        <div className="results-header">
          <div>
            <h1 className="results-title">Scan Results</h1>
            <p className="text-2" style={{ fontSize: 14, marginTop: 6 }}>
              {scores.length} scan{scores.length !== 1 ? 's' : ''} recorded
            </p>
          </div>
          <Link to="/leaderboard" className="btn btn-secondary">
            🏆 See leaderboard
          </Link>
        </div>

        {/* ── Scan history tabs ── */}
        {scores.length > 1 && (
          <div className="scan-history-strip">
            {scores.map((s, i) => (
              <button
                key={i}
                id={`scan-tab-${i}`}
                className={`scan-history-btn ${selectedScan === s ? 'active' : ''}`}
                onClick={() => { setSelectedScan(s); setExpandedTip(null) }}
              >
                <span style={{ fontWeight: 700, fontSize: 15, color: scoreColor(s.total_score) }}>
                  {s.total_score.toFixed(1)}
                </span>
                <span className="text-3" style={{ fontSize: 10 }}>
                  {new Date(s.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                </span>
              </button>
            ))}
          </div>
        )}

        {/* ── Score hero ── */}
        <div className="results-hero-grid">
          {/* Big score */}
          <div className="card-elevated results-score-card" style={{ '--gender-color': genderColor }}>
            <div className="results-score-inner">
              <div className="results-score-label text-3">Glow Score</div>
              <div className="results-score-num" style={{ color: scoreColor(totalScore), animation: 'count-up 0.5s ease' }}>
                {totalScore.toFixed(1)}
                <span className="results-score-denom">/100</span>
              </div>
              <div className="results-verdict" style={{ color: scoreColor(totalScore) }}>
                {scoreLabel(totalScore)}
              </div>
              <div className="results-meta">
                <span>{framesAnalyzed} frames analyzed</span>
                <span>·</span>
                <span style={{ textTransform: 'capitalize' }}>
                  {genderApplied?.replace('_', ' ')} weights
                </span>
                <span>·</span>
                <span>
                  {new Date(selectedScan?.created_at).toLocaleDateString('en-IN', {
                    month: 'long', day: 'numeric', year: 'numeric'
                  })}
                </span>
              </div>
            </div>

            <div className="results-actions">
              <Link to="/roadmap" className="btn btn-primary" id="btn-view-roadmap"
                style={{ borderRadius: 28, padding: '12px 28px', fontSize: 15, boxShadow: '0 4px 24px rgba(108,99,255,0.45)' }}>
                &#x1F5FA; View My Glowup Roadmap
              </Link>
              <Link to="/scan" className="btn btn-secondary">
                &#x1F52C; Scan again
              </Link>
              <div className="alert alert-info" style={{ padding: '8px 12px', fontSize: 12, margin: 0 }}>
                &#x1F4C4; PDF report downloaded to your device
              </div>
            </div>

          </div>

          {/* Feature score chart */}
          <div className="card p-24 results-features-card">
            <h3 className="results-section-title">Feature Breakdown</h3>
            <div className="features-list">
              {Object.entries(details).map(([feature, rawScore]) => {
                const score = typeof rawScore === 'number' ? rawScore : 0
                const norm = score > 1 ? score : score * 100
                return (
                  <div key={feature} className="feature-row" id={`feature-${feature.toLowerCase()}`}>
                    <div className="feature-row-label">
                      <span className="feature-icon">{FEATURE_ICONS[feature] || '•'}</span>
                      <span className="feature-name">{feature}</span>
                    </div>
                    <div className="feature-row-right">
                      <div className="feature-bar-track">
                        <div
                          className="feature-bar-fill"
                          style={{
                            width: `${Math.min(norm, 100)}%`,
                            background: scoreColor(norm),
                          }}
                        />
                      </div>
                      <span className="feature-score-val" style={{ color: scoreColor(norm) }}>
                        {Math.round(norm)}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* ── Tips ── */}
        {selectedScan?.tips && selectedScan.tips.length > 0 && (
          <div className="results-section">
            <div className="results-section-header">
              <h2 className="results-section-heading">Personalized Guidance</h2>
              <p className="text-3" style={{ fontSize: 13 }}>
                ⚕ Cosmetic advice only — consult a professional before any decisions
              </p>
            </div>

            <div className="tips-grid">
              {selectedScan.tips.map((tip, i) => (
                <div
                  key={i}
                  id={`tip-${i}`}
                  className={`tip-item card ${expandedTip === i ? 'expanded' : ''}`}
                  onClick={() => setExpandedTip(expandedTip === i ? null : i)}
                >
                  <div className="tip-item-header">
                    <div className="flex items-center gap-8">
                      <span className="feature-icon">{FEATURE_ICONS[tip.feature] || '💡'}</span>
                      <span className="tip-feature-name">{tip.feature}</span>
                      <span className={`pill pill-${tip.severity || 'low'}`}>
                        {tip.severity || 'info'}
                      </span>
                    </div>
                    <span className="tip-toggle text-3">
                      {expandedTip === i ? '▲' : '▼'}
                    </span>
                  </div>

                  {expandedTip === i && (
                    <div className="tip-body">
                      <p className="tip-text text-2">{tip.tip}</p>
                      {tip.medical_note && (
                        <div className="alert alert-warn" style={{ marginTop: 10, padding: '8px 12px', fontSize: 12 }}>
                          <span>⚕</span>
                          <span>{tip.medical_note}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Disclaimer ── */}
        <div className="results-disclaimer">
          <strong>⚕ Medical Disclaimer:</strong> This analysis is for cosmetic and educational guidance only. Scores are based on mathematical facial geometry metrics and do not reflect health outcomes, medical assessments, or personal worth. Consult a licensed dermatologist or surgeon before making any cosmetic decisions.
        </div>

      </div>
    </div>
  )
}
