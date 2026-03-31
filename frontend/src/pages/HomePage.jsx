import { useEffect, useState } from 'react'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'
import { EditorialList } from '../components/EditorialList'
import { MetricStrip } from '../components/MetricStrip'

const tabs = {
  hot: { label: 'Hot now', path: '/content/hot' },
  liked: { label: 'Most liked', path: '/content/top-liked' },
  favorited: { label: 'Most favorited', path: '/content/top-favorited' },
}

export function HomePage() {
  const [tab, setTab] = useState('hot')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')

    apiRequest(tabs[tab].path)
      .then((result) => {
        const data = unwrapEnvelope(result, 'Unable to load content feed.')
        const nextItems = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
        if (active) {
          setItems(nextItems)
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [tab])

  const hero = items[0]
  const rest = items.slice(1)

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <SectionHeader
          eyebrow="Editorial board"
          title="An editorial frontend for a vertical-interest community."
          subtitle="Warm serif-led composition, restrained color, and direct wiring to the existing Flask API."
        />

        <div className="tab-row">
          {Object.entries(tabs).map(([key, value]) => (
            <button
              key={key}
              className={`tab-row__button${key === tab ? ' is-active' : ''}`}
              type="button"
              onClick={() => setTab(key)}
            >
              {value.label}
            </button>
          ))}
        </div>

        {loading ? <div className="screen-state">Loading feed...</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}

        {hero ? (
          <article className="feature-story">
            <div className="feature-story__copy">
              <p className="eyebrow-row">
                <span>{hero.content_type || 'content'}</span>
                <span>{hero.author_name || 'anonymous'}</span>
              </p>
              <h2>{hero.title}</h2>
              <p className="feature-story__meta">Published {String(hero.created_at || '').slice(0, 10)}</p>
            </div>
            <MetricStrip
              metrics={[
                { label: 'Likes', value: hero.like_count },
                { label: 'Comments', value: hero.comment_count },
                { label: 'Views', value: hero.view_count },
              ]}
            />
          </article>
        ) : null}
      </section>

      <section>
        <SectionHeader
          eyebrow="Latest list"
          title="Current visible content"
          subtitle="The scaffold keeps the magazine-like hierarchy from the original prototype, but moves it into reusable React modules."
        />
        <EditorialList items={rest.length ? rest : items} />
      </section>
    </div>
  )
}
