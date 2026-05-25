import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { apiRequest, getStoredUser, setStoredUser } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser())
  const [bootstrapped, setBootstrapped] = useState(false)

  useEffect(() => {
    let active = true

    async function hydrate() {
      const current = getStoredUser()
      if (!current?.token) {
        if (active) {
          setBootstrapped(true)
        }
        return
      }

      try {
        const result = await apiRequest('/user/me')
        if (!active) {
          return
        }
        if (result.response.ok && result.body?.code === 0) {
          const nextUser = { ...current, ...result.body.data, token: current.token }
          setUser(nextUser)
          setStoredUser(nextUser)
        } else {
          setUser(null)
          setStoredUser(null)
        }
      } catch {
        if (active) {
          setUser(current)
        }
      } finally {
        if (active) {
          setBootstrapped(true)
        }
      }
    }

    hydrate()
    return () => {
      active = false
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      bootstrapped,
      login(nextUser) {
        setUser(nextUser)
        setStoredUser(nextUser)
      },
      logout() {
        setUser(null)
        setStoredUser(null)
      },
    }),
    [bootstrapped, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
