import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { SectionHeader } from '../components/SectionHeader'
import { apiRequest, unwrapEnvelope } from '../lib/api'

export function WorkspaceOverviewPage() {
  const [overview, setOverview] = useState(null)

  useEffect(() => {
    apiRequest('/workspace/overview')
      .then((result) => setOverview(unwrapEnvelope(result)))
      .catch(() => setOverview(null))
  }, [])

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Overview"
        title="Library dashboard."
        subtitle="A quick status view for assets, works, and publishable portfolio content."
      />
      <div className="metric-grid">
        <div className="metric-card"><strong>{overview?.asset_count ?? '-'}</strong><span> Assets</span></div>
        <div className="metric-card"><strong>{overview?.public_asset_count ?? '-'}</strong><span> Public assets</span></div>
        <div className="metric-card"><strong>{overview?.work_count ?? '-'}</strong><span> Works</span></div>
        <div className="metric-card"><strong>{overview?.publishable_work_count ?? '-'}</strong><span> Publishable works</span></div>
      </div>
      <div className="action-grid">
        <Link className="primary-button" to="/assets">Manage assets</Link>
        <Link className="primary-button" to="/works">Organize works</Link>
        <Link className="primary-button" to="/publish">Publish snapshot</Link>
      </div>
    </div>
  )
}
