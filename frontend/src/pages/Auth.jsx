import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import './Auth.css'

const GENDERS = [
  { value: 'male',              icon: '♂',  label: 'Male',   desc: 'Male scoring weights' },
  { value: 'female',            icon: '♀',  label: 'Female', desc: 'Female scoring weights' },
  { value: 'prefer_not_to_say', icon: '⊘',  label: 'Other',  desc: 'Neutral weights' },
]

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', email: '', password: '', gender: 'prefer_not_to_say' })
  const [clientError, setClientError] = useState(null)
  const { login, signup, loading, error } = useAuth()

  const set = (k) => (e) => {
    setClientError(null)
    setForm(f => ({ ...f, [k]: e.target.value }))
  }

  const switchMode = (next) => {
    setMode(next)
    setClientError(null)
    setForm({ username: '', email: '', password: '', gender: 'prefer_not_to_say' })
  }

  // Client-side validation before hitting the API
  const validate = () => {
    if (!form.username.trim() || form.username.trim().length < 3)
      return 'Username must be at least 3 characters'
    if (form.username.trim().length > 30)
      return 'Username must be 30 characters or less'
    if (mode === 'signup') {
      if (!form.email.includes('@'))
        return 'Enter a valid email address'
      if (form.password.length < 6)
        return 'Password must be at least 6 characters'
    }
    return null
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const err = validate()
    if (err) { setClientError(err); return }
    if (mode === 'login') login(form.username, form.password)
    else signup(form.username, form.email, form.password, form.gender)
  }

  const displayError = clientError || error

  return (
    <div className="auth-layout">
      {/* Left — Brand */}
      <div className="auth-left">
        <div className="auth-left-inner">
          <div className="auth-brand-tag">Face Analysis Platform</div>

          <h1 className="auth-headline">
            Know your<br />
            <span style={{ color: 'var(--accent)' }}>Glow Score</span>
          </h1>

          <p className="auth-desc">
            A scientific approach to facial aesthetics — 468 landmark analysis, gender-specific scoring, and expert guidance.
          </p>

          <div className="auth-stats">
            {[
              { n: '468',   l: 'Facial landmarks' },
              { n: '10',    l: 'Features scored' },
              { n: '30s',   l: 'Scan duration' },
              { n: '100%',  l: 'Privacy safe' },
            ].map((s, i) => (
              <div key={i} className="auth-stat">
                <span className="auth-stat-n">{s.n}</span>
                <span className="auth-stat-l">{s.l}</span>
              </div>
            ))}
          </div>

          <div className="auth-how">
            <p className="auth-how-title">How it works</p>
            <ol className="auth-steps">
              <li>Sign up and choose your gender</li>
              <li>Run <code>python scanner.py</code> for a 30s live scan</li>
              <li>Get your score, rank, tips and PDF report</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Right — Form */}
      <div className="auth-right">
        <div className="auth-form-wrap card-elevated">
          {/* Mode tabs */}
          <div className="auth-tabs">
            <button
              id="tab-login"
              className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
              onClick={() => switchMode('login')}
            >
              Sign in
            </button>
            <button
              id="tab-signup"
              className={`auth-tab-btn ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => switchMode('signup')}
            >
              Create account
            </button>
          </div>

          <form id="auth-form" onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                id="input-username"
                className="input"
                type="text"
                placeholder="e.g. john_doe"
                value={form.username}
                onChange={set('username')}
                required
                autoComplete="username"
              />
            </div>

            {mode === 'signup' && (
              <div className="form-group">
                <label className="form-label">Email address</label>
                <input
                  id="input-email"
                  className="input"
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={set('email')}
                  required
                  autoComplete="email"
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                id="input-password"
                className="input"
                type="password"
                placeholder={mode === 'signup' ? '6+ characters' : 'Your password'}
                value={form.password}
                onChange={set('password')}
                required
                minLength={6}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            {mode === 'signup' && (
              <div className="form-group">
                <label className="form-label">Gender <span className="form-hint">— sets scoring weights</span></label>
                <div className="gender-grid" id="gender-selector">
                  {GENDERS.map(g => (
                    <button
                      type="button"
                      key={g.value}
                      id={`gender-${g.value}`}
                      className={`gender-btn ${form.gender === g.value ? `selected ${g.value}` : ''}`}
                      onClick={() => setForm(f => ({ ...f, gender: g.value }))}
                    >
                      <span className="gender-btn-icon">{g.icon}</span>
                      <span className="gender-btn-label">{g.label}</span>
                      <span className="gender-btn-desc">{g.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {displayError && (
              <div className="alert alert-error" id="auth-error">
                <span>⚠</span>
                <span>{displayError}</span>
              </div>
            )}

            <button
              id="btn-submit-auth"
              type="submit"
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading
                ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Please wait…</>
                : mode === 'login' ? 'Sign in →' : 'Create account →'
              }
            </button>
          </form>

          <p className="auth-switch-text">
            {mode === 'login' ? "No account? " : "Have an account? "}
            <button
              className="auth-link-btn"
              onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}
            >
              {mode === 'login' ? 'Sign up free' : 'Sign in'}
            </button>
          </p>

          <div className="auth-privacy">
            🔒 Biometric data is never stored. Only geometry metrics are saved.
          </div>
        </div>
      </div>
    </div>
  )
}
