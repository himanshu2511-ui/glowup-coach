import axios from 'axios'

// In production (Vercel), set VITE_API_BASE_URL to your Render backend URL.
// In local dev, Vite proxy routes / to localhost:8000.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 30000,
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('glowup_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally — redirect to auth
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('glowup_token')
      localStorage.removeItem('glowup_user')
      window.location.href = '/auth'
    }
    return Promise.reject(err)
  }
)

export default api
