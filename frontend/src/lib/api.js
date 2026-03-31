const STORAGE_KEY = 'vc_user'
export const API_BASE = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:5000/api').replace(/\/$/, '')

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setStoredUser(user) {
  if (!user) {
    localStorage.removeItem(STORAGE_KEY)
    return
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
}

export async function apiRequest(path, options = {}) {
  const user = getStoredUser()
  const headers = {
    'Content-Type': 'application/json',
    ...(user?.token ? { Authorization: `Bearer ${user.token}` } : {}),
    ...(options.headers || {}),
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  return { response, body }
}

export function unwrapEnvelope(result, fallback = 'Request failed') {
  if (!result.body || typeof result.body !== 'object') {
    throw new Error(fallback)
  }
  if (result.response.ok && result.body.code === 0) {
    return result.body.data
  }
  throw new Error(result.body.msg || fallback)
}

export function listToIds(value) {
  return String(value || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0)
}
