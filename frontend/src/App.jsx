import { useState } from 'react'
import { Link, NavLink, useNavigate, BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

import Landing    from './pages/Landing'
import Auth       from './pages/Auth'
import Scan       from './pages/Scan'
import Results    from './pages/Results'
import Leaderboard from './pages/Leaderboard'
import Roadmap    from './pages/Roadmap'

// ─── Protected route ──────────────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  return localStorage.getItem('glowup_token')
    ? children
    : <Navigate to="/auth" replace />
}

// ─── Nav ──────────────────────────────────────────────────────────────────────
function Nav() {
  const navigate = useNavigate()
  const token    = localStorage.getItem('glowup_token')
  const user     = JSON.parse(localStorage.getItem('glowup_user') || '{}')

  const logout = async () => {
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch (_) {}
    localStorage.removeItem('glowup_token')
    localStorage.removeItem('glowup_user')
    navigate('/')
  }

  const initial     = user.username?.[0]?.toUpperCase() || '?'
  const genderColor = user.gender === 'male' ? 'var(--male)' : user.gender === 'female' ? 'var(--female)' : 'var(--accent)'

  return (
    <nav className="nav" id="main-nav">
      {/* Logo */}
      <Link to={token ? '/scan' : '/'} className="nav-logo" style={{ textDecoration: 'none' }}>
        <div className="nav-logo-dot" />
        Glowup Coach
      </Link>

      {/* Centre links */}
      <div className="nav-links">
        {!token && (
          <>
            <a href="/#how-it-works" className="nav-link">How it works</a>
          </>
        )}
        {token && (
          <>
            <NavLink to="/scan"        id="nav-scan"        className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Scanner</NavLink>
            <NavLink to="/roadmap"     id="nav-roadmap"     className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Roadmap</NavLink>
            <NavLink to="/results"     id="nav-results"     className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Results</NavLink>
            <NavLink to="/leaderboard" id="nav-leaderboard" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Leaderboard</NavLink>
          </>
        )}
      </div>

      {/* User area */}
      <div className="nav-user">
        {token ? (
          <>
            <div
              id="nav-user-btn"
              className="nav-avatar"
              style={{ borderColor: genderColor, color: genderColor }}
            >
              {initial}
            </div>
            <span className="nav-link" style={{ cursor: 'default', fontWeight: 500, color: 'var(--text-2)', fontSize: 13 }}>
              {user.username}
            </span>
            <button
              id="btn-logout"
              className="nav-link"
              onClick={logout}
              style={{ cursor: 'pointer', color: 'var(--text-3)', fontSize: 13, background: 'none', border: 'none' }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link to="/auth" className="nav-link" id="nav-login">Login</Link>
            <Link to="/auth" className="btn btn-primary" id="nav-signup"
              style={{ fontSize: 13, padding: '7px 18px', borderRadius: 24 }}>
              Get Started
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}

// ─── After-scan auto-redirect helper ──────────────────────────────────────────
// Scan.jsx navigates to /results on done, which is fine.
// After /results we add a "View Roadmap" button (see Results.jsx).

// ─── App shell ────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        {/* Public */}
        <Route path="/"    element={<Landing />} />
        <Route path="/auth" element={<Auth />} />

        {/* Protected */}
        <Route path="/scan"        element={<ProtectedRoute><Scan /></ProtectedRoute>} />
        <Route path="/results"     element={<ProtectedRoute><Results /></ProtectedRoute>} />
        <Route path="/roadmap"     element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
        <Route path="/leaderboard" element={<ProtectedRoute><Leaderboard /></ProtectedRoute>} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
