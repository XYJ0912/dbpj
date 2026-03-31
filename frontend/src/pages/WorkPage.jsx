import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { EditorialList } from '../components/EditorialList'
import { MetricStrip } from '../components/MetricStrip'
import { SectionHeader } from '../components/SectionHeader'

export function WorkPage() {
  const { workId } = useParams()
  const [work, setWork] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setError('')

    apiRequest(`/works/${workId}`)
      .then((result) => {
        const data = unwrapEnvelope(result, 'Unable to load work detail.')
        if (active) {
          setWork(data)
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
  }, [workId])

  if (error && !work) {
    return <div className="error-banner">{error}</div>
  }

  if (!work) {
    return <div className="screen-state">Loading work detail...</div>
  }

  const contents = Array.isArray(work.contents?.items) ? work.contents.items : []
  const characters = Array.isArray(work.characters) ? work.characters : []

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow={work.work_type || 'work'}
        title={work.work_name}
        subtitle={work.description || 'No description available for this work yet.'}
      />

      <MetricStrip
        metrics={[
          { label: 'Characters', value: characters.length },
          { label: 'Content', value: contents.length },
        ]}
      />

      <section className="meta-columns">
        <div>
          <h3>Character set</h3>
          <p>{characters.map((item) => item.character_name).join(', ') || 'No linked characters.'}</p>
        </div>
        <div>
          <h3>Status</h3>
          <p>{work.work_status || 'active'}</p>
        </div>
      </section>

      <section>
        <SectionHeader
          eyebrow="Related content"
          title="Published pieces linked to this work"
          subtitle="Backed by GET /api/works/:work_id."
        />
        <EditorialList items={contents} compact />
      </section>
    </div>
  )
}
