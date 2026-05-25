import { Link } from 'react-router-dom'
import { SectionHeader } from '../components/SectionHeader'
import { useAuth } from '../context/AuthContext'

export function HomePage() {
  const { user } = useAuth()

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <SectionHeader
          eyebrow="Local-first creator workspace"
          title="From local assets to a static public portfolio."
          subtitle="Register assets, organize works, check licensing and privacy, then export a static homepage snapshot."
        />
        <div className="action-grid hero-actions">
          <Link className="primary-button" to={user ? '/workspace' : '/auth'}>
            {user ? 'Open workspace' : 'Sign in'}
          </Link>
          {user ? (
            <Link className="secondary-button" to="/publish">
              Publish check
            </Link>
          ) : null}
        </div>
      </section>

      <section className="step-grid">
        <div className="step-card">
          <strong>1</strong>
          <span>Upload files or register local asset references.</span>
        </div>
        <div className="step-card">
          <strong>2</strong>
          <span>Bind assets into works with public/private controls.</span>
        </div>
        <div className="step-card">
          <strong>3</strong>
          <span>Generate a clean static snapshot after checks pass.</span>
        </div>
      </section>
    </div>
  )
}
