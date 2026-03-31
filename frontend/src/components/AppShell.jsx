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
            <span className="wordmark__title">Vertical</span>
            <span className="wordmark__sub">Community</span>
          </Link>

          <nav className="main-nav">
            <NavLink to="/" end className="main-nav__link">
              Home
            </NavLink>
            <NavLink to="/discover" className="main-nav__link">
              Discover
            </NavLink>
            {user ? (
              <NavLink to="/publish" className="main-nav__link">
                Publish
              </NavLink>
            ) : null}
          </nav>

          <div className="site-header__actions">
            {user ? (
              <>
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => navigate(`/profile/${user.user_id}`)}
                >
                  Profile
                </button>
                <button className="avatar-chip" type="button" onClick={() => navigate(`/profile/${user.user_id}`)}>
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
        <span className="site-footer__brand">Vertical Community</span>
        <span className="site-footer__text">Editorial frontend scaffold for the Flask API.</span>
      </footer>
    </div>
  )
}
