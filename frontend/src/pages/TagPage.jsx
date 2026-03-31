import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { EditorialList } from '../components/EditorialList'
import { SectionHeader } from '../components/SectionHeader'

export function TagPage() {
  const { tagName } = useParams()
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setError('')

    apiRequest(`/content/by-tag?tag_name=${encodeURIComponent(tagName)}`)
      .then((result) => {
        const data = unwrapEnvelope(result, 'Unable to load tag view.')
        const nextItems = Array.isArray(data?.items) ? data.items : []
        if (active) {
          setItems(nextItems)
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message)
        }
      })

    return () => {
      active = false
    }
  }, [tagName])

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Tag lens"
        title={`#${tagName}`}
        subtitle="Directly backed by GET /api/content/by-tag."
      />
      {error ? <div className="error-banner">{error}</div> : null}
      <EditorialList items={items} />
    </div>
  )
}
