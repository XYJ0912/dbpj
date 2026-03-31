import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'

const tabs = {
  works: { label: 'Works', path: '/works' },
  characters: { label: 'Characters', path: '/characters' },
  tags: { label: 'Tags', path: '/tags' },
}

export function DiscoverPage() {
  const [tab, setTab] = useState('works')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')

    apiRequest(tabs[tab].path)
      .then((result) => {
        const data = unwrapEnvelope(result, 'Unable to load discovery data.')
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

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Atlas"
        title="Discover works, tags, and character clusters."
        subtitle="This page keeps the prototype's editorial browsing rhythm, but translates it into actual route-backed views."
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

      {loading ? <div className="screen-state">Loading discovery view...</div> : null}
      {error ? <div className="error-banner">{error}</div> : null}

      <div className={`discovery-grid discovery-grid--${tab}`}>
        {items.map((item) => {
          if (tab === 'works') {
            return (
              <article key={item.work_id} className="discovery-tile">
                <p className="eyebrow-row">
                  <span>{item.work_type || 'work'}</span>
                  <span>{item.character_count ?? 0} cast</span>
                </p>
                <h3>
                  <Link to={`/work/${item.work_id}`}>{item.work_name}</Link>
                </h3>
                <p>{item.description || 'No description available yet.'}</p>
              </article>
            )
          }

          if (tab === 'characters') {
            return (
              <article key={item.character_id} className="discovery-tile">
                <p className="eyebrow-row">
                  <span>character</span>
                  <span>{item.work_count ?? 0} works</span>
                </p>
                <h3>{item.character_name}</h3>
                <p>{item.description || 'No description available yet.'}</p>
              </article>
            )
          }

          return (
            <article key={item.tag_id} className="tag-line-item">
              <Link to={`/tag/${encodeURIComponent(item.tag_name)}`}>#{item.tag_name}</Link>
              <span>{item.tag_type || 'tag'}</span>
            </article>
          )
        })}
      </div>
    </div>
  )
}
