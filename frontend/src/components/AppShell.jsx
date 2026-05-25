import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function userInitial(user) {
  return (user?.username || '?').slice(0, 1).toUpperCase()
}

export function AppShell({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="app-frame">
      <header className="site-header">
        <div className="site-header__inner">
          <Link className="wordmark" to="/">
            <span className="wordmark__title">Portfolio</span>
            <span className="wordmark__sub">Library</span>
          </Link>

          <nav className="main-nav">
            <NavLink to="/" end className="main-nav__link">
              Home
            </NavLink>
            {user ? (
              <NavLink to="/assets" className="main-nav__link">
                Assets
              </NavLink>
            ) : null}
            {user ? (
              <NavLink to="/works" className="main-nav__link">
                Works
              </NavLink>
            ) : null}
            {user ? (
              <NavLink to="/publish" className="main-nav__link">
                Publish
              </NavLink>
            ) : null}
            {user ? (
              <NavLink to="/profile" className="main-nav__link">
                Profile
              </NavLink>
            ) : null}
          </nav>

          <div className="site-header__actions">
            {user ? (
              <>
                <button className="avatar-chip" type="button" onClick={() => navigate('/profile')}>
                  {userInitial(user)}
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => {
                    logout()
                    navigate('/')
                  }}
                >
                  Sign out
                </button>
              </>
            ) : (
              <Link className="accent-link" to="/auth">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="page-shell">{children}</main>

      <footer className="site-footer">
        <span className="site-footer__brand">Portfolio Library</span>
        <span className="site-footer__text">Local-first personal asset library and static portfolio publisher.</span>
      </footer>
    </div>
  )
}
