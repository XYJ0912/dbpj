import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'

const emptyState = {
  username: '',
  email: '',
  password: '',
  bio: '',
}

export function AuthPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState(emptyState)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const heading = useMemo(
    () =>
      mode === 'login'
        ? {
            eyebrow: 'Session',
            title: 'Sign into the local creator workspace.',
            subtitle: 'Use the demo account after importing the minimal SQL, or create a new local account.',
          }
        : {
            eyebrow: 'Account',
            title: 'Create a workspace account.',
            subtitle: 'Registration also creates a default creator profile and homepage config.',
          },
    [mode],
  )

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')

    const payload =
      mode === 'login'
        ? { username: form.username, password: form.password }
        : {
            username: form.username,
            email: form.email,
            password: form.password,
            bio: form.bio,
          }

    try {
      const result = await apiRequest(mode === 'login' ? '/user/login' : '/user/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const data = unwrapEnvelope(result, 'Authentication request failed.')
      login(data)
      setMessage(result.body?.msg || 'Success.')
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-layout">
      <SectionHeader eyebrow={heading.eyebrow} title={heading.title} subtitle={heading.subtitle} />

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={form.username} onChange={(event) => updateField('username', event.target.value)} />
        </label>

        {mode === 'register' ? (
          <label>
            Email
            <input type="email" value={form.email} onChange={(event) => updateField('email', event.target.value)} />
          </label>
        ) : null}

        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={(event) => updateField('password', event.target.value)}
          />
        </label>

        {mode === 'register' ? (
          <label>
            Bio
            <textarea value={form.bio} onChange={(event) => updateField('bio', event.target.value)} rows={4} />
          </label>
        ) : null}

        {message ? <div className="success-banner">{message}</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}

        <div className="auth-form__actions">
          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? 'Working...' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
          <button
            className="ghost-button"
            type="button"
            onClick={() => {
              setMode((current) => (current === 'login' ? 'register' : 'login'))
              setError('')
              setMessage('')
            }}
          >
            {mode === 'login' ? 'Need an account?' : 'Use existing account'}
          </button>
        </div>
      </form>
    </div>
  )
}
