import { Link } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import './Landing.css'

// ─── Animated counter ──────────────────────────────────────────────────────────
function Counter({ to, suffix = '', duration = 1800 }) {
  const [val, setVal] = useState(0)
  const ref = useRef(null)

  useEffect(() => {
    const obs = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      obs.disconnect()
      let start = null
      const step = (ts) => {
        if (!start) start = ts
        const prog = Math.min((ts - start) / duration, 1)
        const ease = 1 - Math.pow(1 - prog, 3)
        setVal(Math.round(ease * to))
        if (prog < 1) requestAnimationFrame(step)
      }
      requestAnimationFrame(step)
    }, { threshold: 0.3 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [to, duration])

  return <span ref={ref}>{val.toLocaleString()}{suffix}</span>
}

// ─── Feature card ──────────────────────────────────────────────────────────────
function FeatureCard({ icon, title, desc, delay }) {
  const ref = useRef(null)
  const [vis, setVis] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect() } }, { threshold: 0.15 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])
  return (
    <div
      ref={ref}
      className="lp-feature-card"
      style={{ animationDelay: `${delay}ms`, opacity: vis ? undefined : 0, transform: vis ? undefined : 'translateY(30px)' }}
      data-vis={vis}
    >
      <div className="lp-feat-icon">{icon}</div>
      <h3 className="lp-feat-title">{title}</h3>
      <p className="lp-feat-desc">{desc}</p>
    </div>
  )
}

// ─── Floating face dots (decorative) ─────────────────────────────────────────
function FloatingDots() {
  return (
    <div className="lp-dots" aria-hidden>
      {Array.from({ length: 18 }).map((_, i) => (
        <div key={i} className="lp-dot" style={{
          left: `${(i * 37 + 11) % 100}%`,
          top:  `${(i * 53 + 7) % 100}%`,
          animationDelay: `${(i * 0.4) % 3}s`,
          width:  `${4 + (i % 4)}px`,
          height: `${4 + (i % 4)}px`,
          opacity: 0.08 + (i % 5) * 0.03,
        }} />
      ))}
    </div>
  )
}

// ─── How it works step ────────────────────────────────────────────────────────
function Step({ num, icon, title, desc, accent }) {
  const ref = useRef(null)
  const [vis, setVis] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect() } }, { threshold: 0.2 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])
  return (
    <div ref={ref} className={`lp-step ${vis ? 'lp-step-visible' : ''}`} style={{ '--accent': accent }}>
      <div className="lp-step-num" style={{ background: accent }}>{num}</div>
      <div className="lp-step-icon">{icon}</div>
      <div className="lp-step-body">
        <h4 className="lp-step-title">{title}</h4>
        <p className="lp-step-desc">{desc}</p>
      </div>
    </div>
  )
}

// ─── Main Landing Page ─────────────────────────────────────────────────────────
export default function Landing() {
  const token = localStorage.getItem('glowup_token')

  return (
    <div className="lp-root">

      {/* ══════════════ HERO ══════════════════════════════════════════════════ */}
      <section className="lp-hero">
        <FloatingDots />

        <div className="lp-hero-badge">
          <span className="lp-badge-dot" />
          AI-Powered Facial Analysis &bull; Real-Time &bull; Private
        </div>

        <h1 className="lp-hero-title">
          Know Your <span className="lp-gradient-text">Glow Score.</span>
          <br />
          Own Your <span className="lp-gradient-text">Transformation.</span>
        </h1>

        <p className="lp-hero-sub">
          Glowup Coach uses advanced computer vision to analyze 468 facial landmarks in real-time,
          giving you a precise aesthetic score, personalized improvement roadmap, and
          gender-specific guidance — all processed locally in your browser.
        </p>

        <div className="lp-hero-cta">
          <Link
            to={token ? '/scan' : '/auth'}
            className="btn btn-primary lp-cta-btn"
            id="btn-hero-cta"
          >
            {token ? 'Start My Scan' : 'Get My Free Score'}
          </Link>
          <a href="#how-it-works" className="btn btn-ghost lp-cta-ghost">
            See how it works &darr;
          </a>
        </div>

        {/* Live stats */}
        <div className="lp-stats-row">
          <div className="lp-stats-inner">
            <div className="lp-stat">
              <span className="lp-stat-num"><Counter to={468} /></span>
              <span className="lp-stat-label">Facial landmarks tracked</span>
            </div>
            <div className="lp-stat-sep" />
            <div className="lp-stat">
              <span className="lp-stat-num"><Counter to={10} /></span>
              <span className="lp-stat-label">Features scored</span>
            </div>
            <div className="lp-stat-sep" />
            <div className="lp-stat">
              <span className="lp-stat-num"><Counter to={30} suffix="s" /></span>
              <span className="lp-stat-label">Scan duration</span>
            </div>
            <div className="lp-stat-sep" />
            <div className="lp-stat">
              <span className="lp-stat-num"><Counter to={100} suffix="%" /></span>
              <span className="lp-stat-label">Private &amp; local</span>
            </div>
          </div>
        </div>

      </section>

      {/* ══════════════ WHY IT MATTERS ════════════════════════════════════════ */}
      <section className="lp-why">
        <div className="lp-section-header">
          <div className="lp-section-tag">Why Glowup Coach</div>
          <h2 className="lp-section-title">Looks matter more than ever — <br />and now you can measure them.</h2>
          <p className="lp-section-sub">
            Studies show first impressions form in under 100ms. Understanding your facial
            aesthetics is the first step to optimizing them — with or without surgery.
          </p>
        </div>

        <div className="lp-feature-grid">
          <FeatureCard delay={0}   icon="&#128301;" title="468-Point Facial Mesh" desc="MediaPipe FaceMesh maps 468 unique landmarks across your face in real-time at 30fps, tracking micro-geometry that the human eye misses." />
          <FeatureCard delay={80}  icon="&#9878;"   title="Gender-Specific Scoring" desc="Male and female aesthetics are scored with separate, research-backed weight tables. Jawline matters more for men; eyes and lips for women." />
          <FeatureCard delay={160} icon="&#128640;" title="4-Week Roadmap" desc="Every weak feature gets a day-by-day 28-day improvement plan — from mewing and gua sha to professional consultation advice." />
          <FeatureCard delay={240} icon="&#127942;" title="Global Leaderboard" desc="See how you rank against others of the same gender. Real-time WebSocket updates mean you see new scores appear live." />
          <FeatureCard delay={320} icon="&#128274;" title="100% Private" desc="Your camera feed never leaves your browser. Only numerical scores are sent to the server — no images, no biometrics stored." />
          <FeatureCard delay={400} icon="&#128196;" title="Instant PDF Report" desc="A full dark-mode 4-page PDF report is generated and downloaded to your device the moment your scan completes." />
        </div>
      </section>

      {/* ══════════════ HOW IT WORKS ══════════════════════════════════════════ */}
      <section className="lp-how" id="how-it-works">
        <div className="lp-section-header">
          <div className="lp-section-tag">The Process</div>
          <h2 className="lp-section-title">From signup to insights <br />in under 5 minutes</h2>
        </div>

        <div className="lp-steps">
          <Step num="01" icon="&#128100;" accent="#6c63ff"
            title="Create your profile"
            desc="Sign up with your username and select your gender. This determines which scoring algorithm and improvement tips you receive." />
          <div className="lp-step-connector" />
          <Step num="02" icon="&#128247;" accent="#38bdf8"
            title="Allow camera access"
            desc="Click 'Start Scan' in the browser. Your webcam activates locally — no data leaves your device. Center your face in the oval guide." />
          <div className="lp-step-connector" />
          <Step num="03" icon="&#129504;" accent="#34d399"
            title="30-second AI analysis"
            desc="MediaPipe analyzes hundreds of frames, measuring symmetry, proportions, jawline, eyes, lips and 6 more features in real-time." />
          <div className="lp-step-connector" />
          <Step num="04" icon="&#128202;" accent="#fbbf24"
            title="Get your score &amp; rank"
            desc="Receive your 0-100 Glow Score, per-feature breakdown, global rank, and see exactly where you stand." />
          <div className="lp-step-connector" />
          <Step num="05" icon="&#128640;" accent="#f472b6"
            title="Follow your roadmap"
            desc="Get your personalized 4-week transformation plan, highlighted techniques, and a full PDF report — automatically downloaded." />
        </div>
      </section>

      {/* ══════════════ SCORE SCALE ═══════════════════════════════════════════ */}
      <section className="lp-scale">
        <div className="lp-section-header">
          <div className="lp-section-tag">The Scale</div>
          <h2 className="lp-section-title">What does your score mean?</h2>
        </div>
        <div className="lp-scale-grid">
          {[
            { range: '92 – 100', label: 'Elite',          desc: 'Top 1% globally. Near-perfect facial geometry.',            color: '#a78bfa' },
            { range: '82 – 91',  label: 'Very Attractive', desc: 'Top 5%. Strong features with excellent proportions.',       color: '#34d399' },
            { range: '70 – 81',  label: 'Attractive',      desc: 'Top 20%. Noticeably good-looking with minor improvements.', color: '#34d399' },
            { range: '55 – 69',  label: 'Above Average',   desc: 'Above the population mean. Solid foundation to build on.', color: '#fbbf24' },
            { range: '40 – 54',  label: 'Average',         desc: 'Population average. Major gains possible with guidance.',   color: '#fbbf24' },
            { range: '0 – 39',   label: 'Needs Work',      desc: 'High improvement potential. Roadmap will help most here.',  color: '#f87171' },
          ].map(s => (
            <div key={s.label} className="lp-scale-card">
              <div className="lp-scale-range" style={{ color: s.color }}>{s.range}</div>
              <div className="lp-scale-label" style={{ color: s.color }}>{s.label}</div>
              <div className="lp-scale-desc">{s.desc}</div>
              <div className="lp-scale-bar" style={{ background: s.color }} />
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════ FINAL CTA ═════════════════════════════════════════════ */}
      <section className="lp-final-cta">
        <div className="lp-cta-glow" />
        <h2 className="lp-cta-title">Ready to discover your score?</h2>
        <p className="lp-cta-sub">
          Join thousands measuring their glow. Takes 30 seconds.
          <br />No images stored. No BS.
        </p>
        <Link
          to={token ? '/scan' : '/auth'}
          className="btn btn-primary lp-cta-btn lp-cta-large"
          id="btn-final-cta"
        >
          {token ? 'Scan My Face Now' : 'Get Started — It\'s Free'}
        </Link>
        <p className="lp-cta-note">
          &#9888; Cosmetic guidance only &mdash; not medical advice
        </p>
      </section>

    </div>
  )
}
