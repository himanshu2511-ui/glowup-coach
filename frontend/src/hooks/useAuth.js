import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export function useAuth() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('glowup_user')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const signup = useCallback(async (username, email, password, gender) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/auth/signup', { username, email, password, gender })
      localStorage.setItem('glowup_token', data.access_token)
      localStorage.setItem('glowup_user', JSON.stringify(data.user))
      setUser(data.user)
      navigate('/scan')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const login = useCallback(async (username, password) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/auth/login', { username, password })
      localStorage.setItem('glowup_token', data.access_token)
      localStorage.setItem('glowup_user', JSON.stringify(data.user))
      setUser(data.user)
      navigate('/scan')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout')
    } catch (_) { /* already expired */ }
    localStorage.removeItem('glowup_token')
    localStorage.removeItem('glowup_user')
    setUser(null)
    navigate('/auth')
  }, [navigate])

  const updateGender = useCallback(async (gender) => {
    const { data } = await api.patch('/auth/gender', { gender })
    const updated = { ...user, gender: data.gender }
    localStorage.setItem('glowup_user', JSON.stringify(updated))
    setUser(updated)
    return updated
  }, [user])

  return { user, loading, error, signup, login, logout, updateGender }
}
