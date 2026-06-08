import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { FEATURE_COLORS, FEATURE_ICONS, potentialScore } from '../utils/faceScorer'
import './Roadmap.css'

// ─── Score helpers ─────────────────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 85) return '#a78bfa'
  if (s >= 70) return '#34d399'
  if (s >= 55) return '#fbbf24'
  return '#f87171'
}
function scoreLabel(s) {
  if (s >= 92) return 'Elite'
  if (s >= 82) return 'Very Attractive'
  if (s >= 70) return 'Attractive'
  if (s >= 55) return 'Above Average'
  if (s >= 40) return 'Average'
  return 'Needs Work'
}
function getRank(total) {
  if (total >= 85) return { tier: 'S', color: '#a78bfa', emoji: '👑', next: null,          pts: 0  }
  if (total >= 75) return { tier: 'A', color: '#34d399', emoji: '⭐', next: 85, pts: 85 - total }
  if (total >= 60) return { tier: 'B', color: '#38bdf8', emoji: '🔵', next: 75, pts: 75 - total }
  if (total >= 45) return { tier: 'C', color: '#fbbf24', emoji: '🟡', next: 60, pts: 60 - total }
  return               { tier: 'D', color: '#f87171', emoji: '🔴', next: 45, pts: 45 - total }
}

// ─── Animated progress ring ────────────────────────────────────────────────────
function ScoreRing({ score, potential, size = 160 }) {
  const R1 = size / 2 - 10    // outer — potential
  const R2 = size / 2 - 20    // inner — current
  const C1 = 2 * Math.PI * R1
  const C2 = 2 * Math.PI * R2
  const [pPot, setPPot] = useState(0)
  const [pCur, setPCur] = useState(0)
  const sColor = scoreColor(score)

  useEffect(() => {
    const t1 = setTimeout(() => setPPot(potential / 100), 200)
    const t2 = setTimeout(() => setPCur(score    / 100), 400)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [score, potential])

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ filter: 'drop-shadow(0 0 20px rgba(99,102,241,0.3))' }}>
      {/* Outer track — potential */}
      <circle cx={size/2} cy={size/2} r={R1} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={7} />
      <circle cx={size/2} cy={size/2} r={R1} fill="none"
        stroke="url(#grad-potential)" strokeWidth={7}
        strokeDasharray={C1} strokeDashoffset={C1 * (1 - pPot)}
        strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)' }}
      />
      {/* Inner ring — current */}
      <circle cx={size/2} cy={size/2} r={R2} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={9} />
      <circle cx={size/2} cy={size/2} r={R2} fill="none"
        stroke={sColor} strokeWidth={9}
        strokeDasharray={C2} strokeDashoffset={C2 * (1 - pCur)}
        strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 6px ${sColor})` }}
      />
      {/* Gradient defs */}
      <defs>
        <linearGradient id="grad-potential" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%"   stopColor="#00d4ff" stopOpacity="0.6" />
          <stop offset="50%"  stopColor="#a855f7" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#ec4899" stopOpacity="0.6" />
        </linearGradient>
      </defs>
      {/* Score text */}
      <text x={size/2} y={size/2 - 6} textAnchor="middle" fill={sColor}
        fontSize={size * 0.22} fontWeight="800" fontFamily="'Space Grotesk', sans-serif">
        {Math.round(score)}
      </text>
      <text x={size/2} y={size/2 + 12} textAnchor="middle" fill="rgba(255,255,255,0.35)"
        fontSize={size * 0.085} fontFamily="Space Grotesk, sans-serif" fontWeight="600">
        now
      </text>
      <text x={size/2} y={size/2 + 26} textAnchor="middle" fill="rgba(168,85,247,0.7)"
        fontSize={size * 0.075} fontFamily="Space Grotesk, sans-serif" fontWeight="600">
        ↑{Math.round(potential)} potential
      </text>
    </svg>
  )
}

// ─── Tier badge ────────────────────────────────────────────────────────────────
function TierBadge({ tier, color, emoji }) {
  return (
    <div className="rm-tier-badge" style={{ borderColor: `${color}55`, background: `${color}12` }}>
      <span className="rm-tier-emoji">{emoji}</span>
      <span className="rm-tier-letter" style={{ color }}>{tier}</span>
      <span className="rm-tier-sub" style={{ color: `${color}99` }}>Tier</span>
    </div>
  )
}

// ─── Dual bar — current vs potential ──────────────────────────────────────────
function DualBar({ feature, current, potential }) {
  const color    = FEATURE_COLORS[feature] || '#6366f1'
  const [anim, setAnim] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setAnim(true); obs.disconnect() } }, { threshold: 0.3 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  return (
    <div ref={ref} className="rm-dual-bar-wrap">
      {/* Potential bar (background, wider) */}
      <div className="rm-bar-track">
        <div className="rm-bar-potential" style={{
          width: anim ? `${potential}%` : '0%',
          background: `${color}28`,
          border: `1px dashed ${color}44`,
        }} />
        {/* Current bar (on top) */}
        <div className="rm-bar-current" style={{
          width: anim ? `${current}%` : '0%',
          background: `linear-gradient(90deg, ${color}cc, ${color})`,
          boxShadow: `0 0 12px ${color}66`,
        }} />
      </div>
      <div className="rm-bar-labels">
        <span style={{ color }}>Now: <strong>{Math.round(current)}</strong></span>
        <span style={{ color: `${color}88` }}>Goal: <strong>{Math.round(potential)}</strong> (+{Math.round(potential - current)})</span>
      </div>
    </div>
  )
}

// ─── Week flow node ────────────────────────────────────────────────────────────
const WEEK_COLORS  = ['#00d4ff', '#a855f7', '#ec4899', '#10b981']
const WEEK_LABELS  = ['Days 1–7', 'Days 8–14', 'Days 15–21', 'Days 22–28']

function WeekNode({ week, color, text, delay }) {
  const ref = useRef(null)
  const [vis, setVis] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect() } }, { threshold: 0.2 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={`rm-week-node ${vis ? 'rm-week-visible' : ''}`}
      style={{ '--wk-color': color, animationDelay: `${delay}ms` }}
    >
      <div className="rm-week-header" style={{ borderColor: `${color}44`, background: `${color}0f` }}>
        <div className="rm-week-dot" style={{ background: color, boxShadow: `0 0 8px ${color}` }} />
        <span className="rm-week-label" style={{ color }}>{week}</span>
      </div>
      <div className="rm-week-body">{text}</div>
    </div>
  )
}

// ─── Feature card with dual bar + expandable 4-week plan ──────────────────────
function FeatureCard({ feature, current, potential, highlight, weeks, index }) {
  const [open, setOpen]   = useState(index < 2)
  const color             = FEATURE_COLORS[feature] || '#6366f1'
  const icon              = FEATURE_ICONS[feature]  || '✦'
  const weekEntries = [weeks.week1, weeks.week2, weeks.week3, weeks.week4]
  const hasWeeks    = weekEntries.some(Boolean)
  const gain        = Math.round(potential - current)

  return (
    <div
      className={`rm-feat-card ${open ? 'rm-feat-open' : ''}`}
      style={{ '--feat-color': color }}
    >
      {/* Header row */}
      <button className="rm-feat-header" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        {/* Icon + name + highlight */}
        <div className="rm-feat-left">
          <div className="rm-feat-icon-wrap" style={{ background: `${color}18`, borderColor: `${color}33` }}>
            <span className="rm-feat-icon">{icon}</span>
          </div>
          <div>
            <div className="rm-feat-name">{feature}</div>
            {highlight && <div className="rm-feat-highlight"><span style={{ color }}>★</span> {highlight}</div>}
          </div>
        </div>

        {/* Scores + chevron */}
        <div className="rm-feat-right">
          <div className="rm-score-pair">
            <div className="rm-score-now" style={{ color }}>
              {Math.round(current)}<span className="rm-score-denom">/100</span>
            </div>
            <div className="rm-score-arrow" style={{ color: `${color}66` }}>→</div>
            <div className="rm-score-potential" style={{ color: `${color}bb` }}>
              {Math.round(potential)}<span className="rm-score-denom">/100</span>
            </div>
            <div className="rm-gain-badge" style={{ background: `${color}18`, borderColor: `${color}44`, color }}>
              +{gain}
            </div>
          </div>
          <span className={`rm-chevron ${open ? 'open' : ''}`}>⌄</span>
        </div>
      </button>

      {/* Dual progress bar always visible */}
      <div className="rm-feat-bars-wrap">
        <DualBar feature={feature} current={current} potential={potential} />
      </div>

      {/* 4-week flowchart */}
      {open && hasWeeks && (
        <div className="rm-feat-flow">
          <div className="rm-flow-connector-line" style={{ background: `linear-gradient(90deg, ${WEEK_COLORS[0]}, ${WEEK_COLORS[1]}, ${WEEK_COLORS[2]}, ${WEEK_COLORS[3]})` }} />
          <div className="rm-flow-grid">
            {weekEntries.map((text, i) => text ? (
              <WeekNode
                key={i}
                week={WEEK_LABELS[i]}
                color={WEEK_COLORS[i]}
                text={text}
                delay={i * 70}
              />
            ) : null)}
          </div>
          {/* Potential marker */}
          <div className="rm-potential-label" style={{ borderColor: `${color}44`, color }}>
            <span className="rm-potential-star">🎯</span>
            Target after 28 days: <strong>{Math.round(potential)}/100</strong>
            &nbsp;(+{gain} from {Math.round(current)})
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main Roadmap ──────────────────────────────────────────────────────────────
export default function Roadmap() {
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)
  const user = JSON.parse(localStorage.getItem('glowup_user') || '{}')

  useEffect(() => {
    api.get('/scores/me/latest')
      .then(({ data: res }) => { setData(res); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="rm-loading">
      <div className="spinner" /><p>Loading your roadmap...</p>
    </div>
  )

  if (!data?.feature_scores) return (
    <div className="rm-empty">
      <p style={{ fontSize: 32 }}>🗺️</p>
      <p>No scan data yet.</p>
      <Link to="/scan" className="btn btn-primary">Take your first scan</Link>
    </div>
  )

  const total    = data.total_score    ?? 0
  const features = data.feature_scores ?? {}
  const tips     = data.tips           ?? []
  const rank     = data.rank
  const tierInfo = getRank(total)

  // Potential total = average potential across features
  const potTotal = Math.min(
    Object.entries(features).reduce((sum, [feat, sc]) => sum + potentialScore(sc, feat), 0) / Math.max(Object.keys(features).length, 1),
    95
  )

  const tipsMap = Object.fromEntries(tips.map(t => [t.feature, t]))
  const featList = Object.entries(features).sort(([, a], [, b]) => a - b) // worst first

  const gColor = user.gender === 'male' ? '#00d4ff' : user.gender === 'female' ? '#ec4899' : '#6366f1'

  return (
    <div className="rm-root">

      {/* ══ HERO ════════════════════════════════════════════════════════════ */}
      <section className="rm-hero">
        <div className="rm-hero-bg" />

        <div className="rm-hero-content">
          <div className="rm-hero-left">
            <div className="rm-hero-tag" style={{ color: gColor, borderColor: `${gColor}44`, background: `${gColor}0f` }}>
              Glowup Roadmap
            </div>
            <h1 className="rm-hero-name">
              <span className="holo-text">{user.username || 'Your'}'s</span>
              <br />Transformation Plan
            </h1>
            <p className="rm-hero-sub" style={{ color: 'var(--text-2)' }}>
              {data.frames_analyzed || 0} frames analyzed &bull; {user.gender?.replace('_', ' ') || 'neutral'} profile
              {rank && <> &bull; Rank <strong style={{ color: gColor }}>#{rank}</strong></>}
            </p>

            {/* Badges */}
            <div className="rm-badges">
              <div className="rm-verdict" style={{ borderColor: scoreColor(total), color: scoreColor(total) }}>
                {scoreLabel(total)}
              </div>
              <TierBadge tier={tierInfo.tier} color={tierInfo.color} emoji={tierInfo.emoji} />
            </div>

            {/* Potential summary */}
            <div className="rm-potential-summary" style={{ borderColor: 'rgba(168,85,247,0.3)', background: 'rgba(168,85,247,0.06)' }}>
              <div className="rm-ps-label">After 28-day glowup</div>
              <div className="rm-ps-values">
                <span style={{ color: scoreColor(total) }}>{total.toFixed(1)}</span>
                <span className="rm-ps-arrow">→</span>
                <span style={{ color: '#a855f7' }}>{potTotal.toFixed(1)}</span>
                <span className="rm-ps-gain" style={{ color: '#a855f7' }}>+{(potTotal - total).toFixed(1)}</span>
              </div>
              <div className="rm-ps-bar">
                <div className="rm-ps-bar-now"  style={{ width: `${total}%`,    background: scoreColor(total) }} />
                <div className="rm-ps-bar-goal" style={{ width: `${potTotal}%`, background: 'rgba(168,85,247,0.4)' }} />
              </div>
            </div>

            <div className="rm-hero-actions">
              <Link to="/scan"        className="btn btn-primary"   id="btn-rescan">↺ Rescan</Link>
              <Link to="/leaderboard" className="btn btn-secondary" id="btn-lb">Leaderboard</Link>
              <Link to="/results"     className="btn btn-secondary" id="btn-results">Results</Link>
            </div>
          </div>

          <div className="rm-hero-right">
            <ScoreRing score={total} potential={potTotal} size={200} />
            {/* Legend */}
            <div className="rm-ring-legend">
              <div className="rm-legend-item">
                <div className="rm-legend-line" style={{ background: scoreColor(total) }} />
                <span>Current: {total.toFixed(1)}</span>
              </div>
              <div className="rm-legend-item">
                <div className="rm-legend-line rm-legend-dashed" style={{ background: 'rgba(168,85,247,0.6)' }} />
                <span>Potential: {potTotal.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ TIER PROGRESS ════════════════════════════════════════════════════ */}
      <div className="rm-tier-section">
        <div className="rm-tier-row">
          {[
            { tier: 'D', color: '#f87171', min: 0,  max: 44 },
            { tier: 'C', color: '#fbbf24', min: 45, max: 59 },
            { tier: 'B', color: '#38bdf8', min: 60, max: 74 },
            { tier: 'A', color: '#34d399', min: 75, max: 84 },
            { tier: 'S', color: '#a78bfa', min: 85, max: 100 },
          ].map(t => (
            <div key={t.tier} className={`rm-tier-seg ${tierInfo.tier === t.tier ? 'rm-tier-active' : ''}`}
              style={{ '--tc': t.color, flex: t.tier === 'S' ? '1.5' : '1' }}>
              <span className="rm-tier-char" style={{ color: t.color }}>{t.tier}</span>
              <span className="rm-tier-range">{t.min}–{t.tier === 'S' ? '100' : t.max}</span>
            </div>
          ))}
          <div className="rm-tier-marker" style={{
            left: `calc(${Math.min(total, 99)}% - 7px)`,
            background: scoreColor(total),
            boxShadow: `0 0 12px ${scoreColor(total)}`,
          }}>
            <div className="rm-tier-marker-tip" style={{ color: scoreColor(total) }}>
              {total.toFixed(0)}
            </div>
          </div>
        </div>
        {tierInfo.next && (
          <p className="rm-tier-hint">
            Need <strong style={{ color: scoreColor(total) }}>{tierInfo.pts.toFixed(1)} more points</strong> to reach {tierInfo.tier === 'D' ? 'C' : tierInfo.tier === 'C' ? 'B' : tierInfo.tier === 'B' ? 'A' : 'S'} Tier — follow the plan below.
          </p>
        )}
      </div>

      {/* ══ FEATURE ROADMAP ══════════════════════════════════════════════════ */}
      <section className="rm-roadmap-section">
        <div className="rm-section-header">
          <div className="rm-section-tag">28-Day Transformation</div>
          <h2 className="rm-section-title">
            Your Personalized <span className="holo-text">Glowup Flowchart</span>
          </h2>
          <p className="rm-section-sub">
            Features ranked worst→best. Each shows your current score, potential after the plan, and a day-by-day action flowchart.
          </p>
        </div>

        <div className="rm-features">
          {featList.map(([feat, sc], i) => {
            const tip = tipsMap[feat] || {}
            const pot = potentialScore(sc, feat)
            return (
              <FeatureCard
                key={feat}
                feature={feat}
                current={sc}
                potential={pot}
                highlight={tip.highlight || ''}
                weeks={{ week1: tip.week1, week2: tip.week2, week3: tip.week3, week4: tip.week4 }}
                index={i}
              />
            )
          })}
        </div>

        {/* Final milestone card */}
        <div className="rm-milestone-card">
          <div className="rm-milestone-glow" />
          <div className="rm-milestone-content">
            <div className="rm-milestone-tag">🎯 Your 28-Day Goal</div>
            <div className="rm-milestone-scores">
              <div className="rm-ms-score" style={{ color: scoreColor(total) }}>
                <span className="rm-ms-label">Today</span>
                <span className="rm-ms-val">{total.toFixed(1)}</span>
                <span className="rm-ms-tier">{scoreLabel(total)}</span>
              </div>
              <div className="rm-ms-arrow">→</div>
              <div className="rm-ms-score" style={{ color: '#a855f7' }}>
                <span className="rm-ms-label">After Glowup</span>
                <span className="rm-ms-val">{potTotal.toFixed(1)}</span>
                <span className="rm-ms-tier">{scoreLabel(potTotal)}</span>
              </div>
            </div>
            <p className="rm-milestone-desc">
              Follow the 4-week plan above consistently. Rescan every 14 days to track progress.
              {tierInfo.next && ` You're ${tierInfo.pts.toFixed(1)} points away from ${tierInfo.tier === 'D' ? 'C' : tierInfo.tier === 'C' ? 'B' : tierInfo.tier === 'B' ? 'A' : 'S'} Tier.`}
            </p>
            <Link to="/scan" className="btn btn-primary rm-rescan-btn" id="btn-roadmap-rescan">
              Start a New Scan
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
