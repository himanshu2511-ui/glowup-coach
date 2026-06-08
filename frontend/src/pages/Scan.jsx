import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import {
  analyzeFrame, computeTotal, accumulate, finalizeAcc,
  scoreColor, scoreLabel, FEATURE_ICONS,
} from '../utils/faceScorer'
import './Scan.css'

const SCAN_SECONDS = 30
const CDN_BASE     = 'https://cdn.jsdelivr.net/npm/@mediapipe'

const FEATURE_ORDER = [
  'Symmetry', 'Eyes', 'Eyebrows', 'Nose', 'Lips',
  'Cheeks', 'Jawline', 'Ears', 'Forehead', 'Chin',
]

// ─── Load CDN script once ──────────────────────────────────────────────────────
function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) { resolve(); return }
    const s = document.createElement('script')
    s.src = src; s.crossOrigin = 'anonymous'
    s.onload = resolve; s.onerror = reject
    document.head.appendChild(s)
  })
}

// ─── Canvas helpers ────────────────────────────────────────────────────────────
function drawOval(ctx, w, h, detected) {
  ctx.save()
  ctx.strokeStyle = detected ? 'rgba(52,211,153,0.85)' : 'rgba(248,113,113,0.7)'
  ctx.lineWidth   = 2.5
  ctx.setLineDash(detected ? [] : [8, 6])
  ctx.beginPath()
  ctx.ellipse(w / 2, h / 2, w * 0.20, h * 0.33, 0, 0, Math.PI * 2)
  ctx.stroke()
  ctx.restore()
}

function drawMesh(ctx, lm, w, h) {
  const connections = window.FACEMESH_TESSELATION
  if (!connections || !lm) return
  ctx.save()
  ctx.strokeStyle = 'rgba(100,230,120,0.22)'
  ctx.lineWidth   = 0.6
  for (const [s, e] of connections) {
    const p1 = lm[s], p2 = lm[e]
    if (!p1 || !p2) continue
    ctx.beginPath()
    ctx.moveTo((1 - p1.x) * w, p1.y * h)
    ctx.lineTo((1 - p2.x) * w, p2.y * h)
    ctx.stroke()
  }
  const contours = window.FACEMESH_CONTOURS
  if (contours) {
    ctx.strokeStyle = 'rgba(100,230,120,0.55)'
    ctx.lineWidth   = 1.2
    for (const [s, e] of contours) {
      const p1 = lm[s], p2 = lm[e]
      if (!p1 || !p2) continue
      ctx.beginPath()
      ctx.moveTo((1 - p1.x) * w, p1.y * h)
      ctx.lineTo((1 - p2.x) * w, p2.y * h)
      ctx.stroke()
    }
  }
  ctx.restore()
}

// ─── Countdown SVG ring ────────────────────────────────────────────────────────
function CountdownRing({ timeLeft, total }) {
  const R = 38
  const C = 2 * Math.PI * R
  const offset = C * (1 - timeLeft / total)
  const color  = timeLeft > 15 ? '#34d399' : timeLeft > 8 ? '#fbbf24' : '#f87171'
  return (
    <svg className="countdown-svg" viewBox="0 0 90 90" width={90} height={90}>
      <circle cx={45} cy={45} r={R} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={5} />
      <circle
        cx={45} cy={45} r={R} fill="none"
        stroke={color} strokeWidth={5}
        strokeDasharray={C} strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 45 45)"
        style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.3s' }}
      />
      <text x={45} y={49} textAnchor="middle" fill="white" fontSize={18} fontWeight="700" fontFamily="Inter">
        {timeLeft}
      </text>
    </svg>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────────
export default function Scan() {
  const navigate      = useNavigate()
  const videoRef      = useRef(null)
  const canvasRef     = useRef(null)
  const faceMeshRef   = useRef(null)
  const cameraRef     = useRef(null)
  const accRef        = useRef({})
  const frameCountRef = useRef(0)
  const timerRef      = useRef(null)
  const animRef       = useRef(null)
  const latestLmRef   = useRef(null)

  const user   = JSON.parse(localStorage.getItem('glowup_user') || '{}')
  const gender = user.gender || 'prefer_not_to_say'

  const [phase,        setPhase]        = useState('loading')
  const [loadMsg,      setLoadMsg]      = useState('Initializing camera...')
  const [faceDetected, setFaceDetected] = useState(false)
  const [liveScores,   setLiveScores]   = useState({})
  const [liveTotal,    setLiveTotal]    = useState(0)
  const [timeLeft,     setTimeLeft]     = useState(SCAN_SECONDS)
  const [finalResult,  setFinalResult]  = useState(null)
  const [submitting,   setSubmitting]   = useState(false)
  const [camError,     setCamError]     = useState('')
  const [pdfStatus,    setPdfStatus]    = useState('idle') // idle | downloading | done | error

  // ── Canvas draw loop ────────────────────────────────────────────────────────
  const drawLoop = useCallback(() => {
    const video  = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    const ctx = canvas.getContext('2d')
    const w   = canvas.width  = video.videoWidth  || 640
    const h   = canvas.height = video.videoHeight || 480
    ctx.drawImage(video, 0, 0, w, h)
    const lm = latestLmRef.current
    if (lm) { drawMesh(ctx, lm, w, h); drawOval(ctx, w, h, true) }
    else     { drawOval(ctx, w, h, false) }
    animRef.current = requestAnimationFrame(drawLoop)
  }, [])

  // ── MediaPipe results callback ─────────────────────────────────────────────
  const onResults = useCallback((results) => {
    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
      const lm = results.multiFaceLandmarks[0]
      latestLmRef.current = lm
      setFaceDetected(true)
      if (timerRef.current !== null) {
        const frameScores = analyzeFrame(lm)
        accumulate(accRef.current, frameScores)
        frameCountRef.current += 1
        if (frameCountRef.current % 3 === 0) {
          const avg = finalizeAcc({ ...accRef.current })
          setLiveScores(avg)
          setLiveTotal(computeTotal(avg, gender))
        }
      }
    } else {
      latestLmRef.current = null
      setFaceDetected(false)
    }
  }, [gender])

  // ── Init MediaPipe (loads from CDN on first visit) ─────────────────────────
  const initMediaPipe = useCallback(async () => {
    try {
      setLoadMsg('Loading face detection model...')
      await Promise.all([
        loadScript(`${CDN_BASE}/face_mesh/face_mesh.js`),
        loadScript(`${CDN_BASE}/camera_utils/camera_utils.js`),
        loadScript(`${CDN_BASE}/drawing_utils/drawing_utils.js`),
      ])
      setLoadMsg('Starting camera...')
      const { FaceMesh, Camera } = window
      if (!FaceMesh || !Camera) throw new Error('MediaPipe not loaded')

      const fm = new FaceMesh({ locateFile: (f) => `${CDN_BASE}/face_mesh/${f}` })
      fm.setOptions({ maxNumFaces: 1, refineLandmarks: true, minDetectionConfidence: 0.7, minTrackingConfidence: 0.7 })
      fm.onResults(onResults)
      faceMeshRef.current = fm

      const video  = videoRef.current
      const camera = new Camera(video, {
        onFrame: async () => { if (faceMeshRef.current) await faceMeshRef.current.send({ image: video }) },
        width: 1280, height: 720,
      })
      await camera.start()
      cameraRef.current = camera
      setPhase('ready')
      animRef.current = requestAnimationFrame(drawLoop)
    } catch (err) {
      console.error(err)
      setCamError(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera access and refresh.'
          : `Could not start scanner: ${err.message}`
      )
      setPhase('error')
    }
  }, [onResults, drawLoop])

  useEffect(() => {
    initMediaPipe()
    return () => {
      cancelAnimationFrame(animRef.current)
      clearInterval(timerRef.current)
      cameraRef.current?.stop?.()
      faceMeshRef.current?.close?.()
    }
  }, [initMediaPipe])

  // ── Start 30-second scan ───────────────────────────────────────────────────
  const startScan = () => {
    accRef.current       = {}
    frameCountRef.current = 0
    setLiveScores({})
    setLiveTotal(0)
    setTimeLeft(SCAN_SECONDS)
    setFinalResult(null)
    setPdfStatus('idle')
    setPhase('scanning')

    let t = SCAN_SECONDS
    timerRef.current = setInterval(() => {
      t -= 1
      setTimeLeft(t)
      if (t <= 0) {
        clearInterval(timerRef.current)
        timerRef.current = null
        finalizeScan()
      }
    }, 1000)
  }

  // ── Finalize: save score → download PDF instantly ──────────────────────────
  const finalizeScan = useCallback(async () => {
    setPhase('done')
    setSubmitting(true)

    const avgScores    = finalizeAcc(accRef.current)
    const clientTotal  = computeTotal(avgScores, gender)
    const scores100    = Object.fromEntries(
      Object.entries(avgScores).map(([k, v]) => [k, parseFloat((v * 100).toFixed(2))])
    )

    let rank = null, tips = [], finalTotal = clientTotal

    // Step 1 — Save to backend, get rank + AI tips
    try {
      const { data } = await api.post('/analyze/finalize', {
        feature_scores:  scores100,
        frames_analyzed: frameCountRef.current,
        gender_applied:  gender,
      })
      rank       = data.rank        ?? null
      tips       = data.tips        ?? []
      finalTotal = data.total_score ?? clientTotal
    } catch (e) {
      console.warn('Save failed:', e.message)
    }

    setFinalResult({ scores0to1: avgScores, total: finalTotal, rank })
    setSubmitting(false)

    // Step 2 — Generate + instantly download PDF to client device
    setPdfStatus('downloading')
    try {
      const res = await api.post(
        '/analyze/report',
        { feature_scores: scores100, total_score: finalTotal, gender_applied: gender,
          frames_analyzed: frameCountRef.current, rank, tips },
        { responseType: 'blob' }
      )
      const blob   = new Blob([res.data], { type: 'application/pdf' })
      const url    = URL.createObjectURL(blob)
      const a      = document.createElement('a')
      a.href       = url
      a.download   = `glowup_report_${user.username || 'me'}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 10000)
      setPdfStatus('done')
    } catch (e) {
      console.warn('PDF download failed:', e.message)
      setPdfStatus('error')
    }
  }, [gender, user.username])

  // ── Auto-navigate to /roadmap after done ──────────────────────────────────
  useEffect(() => {
    if (phase === 'done' && finalResult && !submitting) {
      const t = setTimeout(() => navigate('/roadmap'), 3800)
      return () => clearTimeout(t)
    }
  }, [phase, finalResult, submitting, navigate])

  const genderColor = gender === 'male' ? 'var(--male)' : gender === 'female' ? 'var(--female)' : 'var(--accent)'

  // ─── RENDER ──────────────────────────────────────────────────────────────────
  return (
    <div className="scan-page-wrap">
      <video ref={videoRef} className="scan-hidden-video" playsInline muted />

      {/* LOADING */}
      {phase === 'loading' && (
        <div className="scan-state-overlay">
          <div className="scan-loading-card">
            <div className="scanner-logo-ring" style={{ borderColor: genderColor }}>
              <span style={{ fontSize: 32 }}>&#128302;</span>
            </div>
            <h2 className="scan-state-title">Setting up scanner</h2>
            <p className="scan-state-desc">{loadMsg}</p>
            <div className="scan-progress-bar">
              <div className="scan-progress-fill" style={{ background: genderColor }} />
            </div>
            <p className="scan-hint text-3">Allow camera access when prompted</p>
          </div>
        </div>
      )}

      {/* ERROR */}
      {phase === 'error' && (
        <div className="scan-state-overlay">
          <div className="scan-loading-card">
            <p style={{ fontSize: 40, marginBottom: 12 }}>&#128247;</p>
            <h2 className="scan-state-title">Camera unavailable</h2>
            <p className="scan-state-desc" style={{ color: '#f87171' }}>{camError}</p>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>
              Try again
            </button>
          </div>
        </div>
      )}

      {/* SCANNER (ready | scanning | done) */}
      {(phase === 'ready' || phase === 'scanning' || phase === 'done') && (
        <div className="scanner-layout">

          {/* LEFT — feature bars */}
          <div className="scanner-panel scanner-panel-left">
            <div className="scanner-panel-title">Feature Scores</div>
            <div className="scanner-features">
              {FEATURE_ORDER.map(feat => {
                const val = (liveScores[feat] ?? 0) * 100
                const clr = scoreColor(val)
                return (
                  <div key={feat} className="scanner-feat-row" id={`feat-${feat.toLowerCase()}`}>
                    <div className="scanner-feat-label">
                      <span>{FEATURE_ICONS[feat]}</span>
                      <span>{feat}</span>
                    </div>
                    <div className="scanner-feat-bar-wrap">
                      <div className="scanner-feat-bar-track">
                        <div className="scanner-feat-bar-fill"
                          style={{ width: `${phase === 'ready' ? 0 : val}%`, background: clr }} />
                      </div>
                      <span className="scanner-feat-val" style={{ color: clr }}>
                        {phase === 'ready' ? '--' : Math.round(val)}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="scanner-total-card" style={{ borderColor: genderColor }}>
              <div className="scanner-total-label text-3">Total Score</div>
              <div className="scanner-total-num" style={{ color: scoreColor(liveTotal) }}>
                {phase === 'ready' ? '--' : liveTotal.toFixed(1)}
              </div>
              <div className="scanner-total-verdict" style={{ color: scoreColor(liveTotal) }}>
                {phase === 'scanning' && liveTotal > 0 ? scoreLabel(liveTotal) : ''}
              </div>
            </div>

            {phase === 'scanning' && (
              <div className="scanner-frames text-3">
                {frameCountRef.current} frames &middot; {faceDetected ? 'Face detected' : 'No face'}
              </div>
            )}
          </div>

          {/* CENTRE — camera canvas */}
          <div className="scanner-camera-wrap">
            <canvas ref={canvasRef} className="scanner-canvas" id="scanner-canvas" />

            {phase === 'scanning' && !faceDetected && (
              <div className="scanner-no-face-pill">Center your face in the oval</div>
            )}

            {phase === 'ready' && (
              <div className="scanner-ready-overlay">
                <div className="scanner-ready-box">
                  <div className="scanner-oval-hint">Align your face here</div>
                  <button
                    id="btn-start-scan"
                    className="btn btn-primary scanner-start-btn"
                    onClick={startScan}
                    disabled={!faceDetected}
                  >
                    {faceDetected ? 'Start Scan' : 'Waiting for face...'}
                  </button>
                  {!faceDetected && (
                    <p className="scanner-cam-hint">Position your face in the center</p>
                  )}
                </div>
              </div>
            )}

            {phase === 'done' && finalResult && (
              <div className="scanner-done-overlay">
                <div className="scanner-done-box">
                  <div className="scanner-done-score" style={{ color: scoreColor(finalResult.total) }}>
                    {finalResult.total.toFixed(1)}
                  </div>
                  <div className="scanner-done-label">{scoreLabel(finalResult.total)}</div>
                  {finalResult.rank && (
                    <div className="scanner-done-rank text-2">Global rank #{finalResult.rank}</div>
                  )}

                  {/* PDF download status */}
                  <div className={`scanner-pdf-status ${pdfStatus}`}>
                    {pdfStatus === 'downloading' && (
                      <><div className="spinner" style={{ width: 14, height: 14 }} /> Generating PDF...</>
                    )}
                    {pdfStatus === 'done' && (
                      <><span className="scanner-pdf-check">&#10003;</span> PDF downloaded!</>
                    )}
                    {pdfStatus === 'error' && (
                      <span style={{ color: '#f87171' }}>PDF unavailable</span>
                    )}
                  </div>

                  <div className="scanner-done-sub text-3">
                    {submitting ? 'Saving results...' : 'Redirecting to results...'}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT — countdown + guide */}
          <div className="scanner-panel scanner-panel-right">
            <div className="scanner-countdown-section">
              {phase === 'scanning' ? (
                <>
                  <CountdownRing timeLeft={timeLeft} total={SCAN_SECONDS} />
                  <div className="scanner-countdown-label text-2">seconds left</div>
                </>
              ) : phase === 'done' ? (
                <div className="scanner-done-icon">&#10003;</div>
              ) : (
                <div className="scanner-idle-icon">&#8987;</div>
              )}
            </div>

            <div className="scanner-right-section">
              <div className="scanner-panel-title">Scan Guide</div>
              <ul className="scanner-tips">
                {[
                  ['&#128161;', 'Natural, even lighting'],
                  ['&#128528;', 'Neutral expression'],
                  ['&#128208;', '40-60 cm from camera'],
                  ['&#128683;', 'Remove glasses/hat'],
                  ['&#9634;',   'Plain background'],
                  ['&#129485;', 'Face forward, still'],
                ].map(([icon, text], i) => (
                  <li key={i} className="scanner-tip-item">
                    <span dangerouslySetInnerHTML={{ __html: icon }} />
                    <span className="text-2">{text}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="scanner-gender-badge" style={{ borderColor: genderColor, color: genderColor }}>
              {gender === 'male' ? '(M)' : gender === 'female' ? '(F)' : '(N)'}
              &nbsp;{gender.replace('_', ' ')} weights
            </div>

            <div className="scanner-disclaimer text-3">
              Cosmetic guidance only &mdash; not medical advice
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
