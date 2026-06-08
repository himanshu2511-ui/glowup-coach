import { useEffect, useState, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import './Leaderboard.css'

const RANK_MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

const GENDER_FILTERS = [
  { value: '',       label: 'All' },
  { value: 'male',   label: '♂ Male' },
  { value: 'female', label: '♀ Female' },
]

function scoreColor(s) {
  if (s >= 80) return '#a78bfa'
  if (s >= 60) return '#34d399'
  if (s >= 40) return '#fbbf24'
  return '#f87171'
}

function ScoreBar({ score }) {
  return (
    <div className="lb-score-bar-track">
      <div
        className="lb-score-bar-fill"
        style={{ width: `${score}%`, background: scoreColor(score) }}
      />
    </div>
  )
}

export default function Leaderboard() {
  const [data,      setData]      = useState(null)
  const [filter,    setFilter]    = useState('')
  const [loading,   setLoading]   = useState(true)
  const [tick,      setTick]      = useState(0)
  const [liveToast, setLiveToast] = useState(null) // { username, total_score }
  const wsRef = useRef(null)

  const user = JSON.parse(localStorage.getItem('glowup_user') || '{}')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params = filter ? { gender_filter: filter } : {}
      const { data: res } = await api.get('/leaderboard', { params })
      setData(res)
    } catch (_) {}
    finally { setLoading(false) }
  }, [filter])

  useEffect(() => { fetchData() }, [fetchData, tick])

  // Auto-refresh every 30s
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 30000)
    return () => clearInterval(t)
  }, [])

  // Live WebSocket — connects to /ws/leaderboard for instant updates
  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws/leaderboard`
    let ws
    let pingInterval
    let reconnectTimeout

    function connect() {
      ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 20000)
      }

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data)
          if (msg.type === 'leaderboard_update') {
            // Refresh leaderboard data
            setTick(n => n + 1)
            // Show toast notification (dismiss after 4s)
            setLiveToast(msg)
            setTimeout(() => setLiveToast(null), 4000)
          }
        } catch (_) {}
      }

      ws.onclose = () => {
        clearInterval(pingInterval)
        // Reconnect after 5s
        reconnectTimeout = setTimeout(connect, 5000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      clearInterval(pingInterval)
      clearTimeout(reconnectTimeout)
      ws?.close()
    }
  }, [])

  const genderColor = user.gender === 'male' ? 'var(--male)' : user.gender === 'female' ? 'var(--female)' : 'var(--accent)'

  return (
    <div className="lb-page page fade-up">
      <div className="container">

        {/* ── Header ── */}
        <div className="lb-header">
          <div>
            <h1 className="lb-title">Leaderboard</h1>
            <p className="text-2" style={{ marginTop: 6, fontSize: 14 }}>
              Top Glow Scores worldwide — updated every 30 seconds
            </p>
          </div>

          {/* Your rank card */}
          {data && (
            <div className="lb-your-card card-elevated" id="your-rank-card">
              <div className="lb-your-label text-3">Your best score</div>
              {data.your_best_score != null ? (
                <>
                  <div className="lb-your-score" style={{ color: scoreColor(data.your_best_score) }}>
                    {data.your_best_score}
                  </div>
                  {data.your_rank && (
                    <div className="lb-your-rank">Global rank <strong>#{data.your_rank}</strong></div>
                  )}
                </>
              ) : (
                <div style={{ fontSize: 13, color: 'var(--text-3)', margin: '8px 0' }}>
                  No scan yet
                </div>
              )}
              <Link to="/scan" className="btn btn-secondary" style={{ fontSize: 12, padding: '6px 12px', textAlign: 'center' }}>
                {data.your_best_score ? '🔬 Scan again' : '🔬 Start scan'}
              </Link>
            </div>
          )}
        </div>

        {/* ── Controls ── */}
        <div className="lb-controls">
          <div className="lb-filter-group" id="lb-filters">
            {GENDER_FILTERS.map(f => (
              <button
                key={f.value}
                id={`filter-${f.value || 'all'}`}
                className={`lb-filter-btn ${filter === f.value ? 'active' : ''}`}
                onClick={() => { setFilter(f.value) }}
              >
                {f.label}
              </button>
            ))}
          </div>
          <button
            id="btn-refresh-lb"
            className="btn btn-ghost"
            onClick={() => setTick(n => n + 1)}
            style={{ padding: '7px 14px', fontSize: 13 }}
          >
            ↺ Refresh
          </button>
        </div>

        {/* ── Live update toast ── */}
        {liveToast && (
          <div className="lb-live-toast" id="lb-live-toast">
            <span className="lb-live-dot" />
            <span>
              <strong>{liveToast.username}</strong> just scored
              <strong style={{ color: scoreColor(liveToast.total_score) }}> {liveToast.total_score}</strong>
              {' '}&mdash; leaderboard updated!
            </span>
          </div>
        )}

        {/* ── Table ── */}
        <div className="lb-table card-elevated">
          {loading ? (
            <div className="lb-state">
              <div className="spinner" style={{ width: 24, height: 24 }} />
              <p className="text-3" style={{ fontSize: 13 }}>Loading rankings…</p>
            </div>
          ) : !data || data.entries.length === 0 ? (
            <div className="lb-state">
              <p style={{ fontSize: 32, marginBottom: 8 }}>🏆</p>
              <p className="text-2" style={{ fontSize: 14, marginBottom: 16 }}>
                {filter
                  ? `No ${filter} scores yet. Be the first!`
                  : 'No scores yet. Run a scan to claim rank #1!'}
              </p>
              <Link to="/scan" className="btn btn-primary">Start scanning →</Link>
            </div>
          ) : (
            <table className="lb-tbl" id="lb-table">
              <thead>
                <tr className="lb-thead-row">
                  <th className="lb-th lb-th-rank">Rank</th>
                  <th className="lb-th lb-th-user">User</th>
                  <th className="lb-th lb-th-score">Score</th>
                  <th className="lb-th lb-th-bar">Distribution</th>
                  <th className="lb-th lb-th-date">Date</th>
                </tr>
              </thead>
              <tbody>
                {data.entries.map((entry, i) => {
                  const isYou = entry.username === user.username
                  const clr   = scoreColor(entry.total_score)
                  const gClr  = entry.gender === 'male' ? 'var(--male)' : entry.gender === 'female' ? 'var(--female)' : 'var(--accent)'

                  return (
                    <tr
                      key={i}
                      id={`lb-row-${i}`}
                      className={`lb-row ${isYou ? 'lb-row-you' : ''}`}
                    >
                      {/* Rank */}
                      <td className="lb-td lb-td-rank">
                        {RANK_MEDAL[entry.rank]
                          ? <span className="lb-medal">{RANK_MEDAL[entry.rank]}</span>
                          : <span className="lb-rank-num">#{entry.rank}</span>}
                      </td>

                      {/* User */}
                      <td className="lb-td lb-td-user">
                        <div className="lb-user-avatar" style={{ borderColor: gClr, color: gClr }}>
                          {entry.username[0].toUpperCase()}
                        </div>
                        <div className="lb-user-info">
                          <div className="lb-username">
                            {entry.username}
                            {isYou && <span className="lb-you-tag">You</span>}
                          </div>
                          <div className="lb-usergender text-3">
                            {entry.gender?.replace('_', ' ')}
                          </div>
                        </div>
                      </td>

                      {/* Score */}
                      <td className="lb-td lb-td-score">
                        <span className="lb-score-val" style={{ color: clr }}>
                          {entry.total_score}
                        </span>
                        <span className="text-3" style={{ fontSize: 11 }}>/100</span>
                      </td>

                      {/* Bar */}
                      <td className="lb-td lb-td-bar">
                        <ScoreBar score={entry.total_score} />
                      </td>

                      {/* Date */}
                      <td className="lb-td lb-td-date text-3">
                        {new Date(entry.achieved_at).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', year: 'numeric'
                        })}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        <p className="lb-footer-note text-3">
          Auto-refreshes every 30 seconds · {data?.total_users ?? 0} registered users
        </p>
      </div>
    </div>
  )
}
