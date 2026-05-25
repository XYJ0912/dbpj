import { Link } from 'react-router-dom'
import { VisibilityBadge, WorkStatusBadge } from './StatusBadges'

export function WorkCard({ work }) {
  return (
    <article className="work-card">
      <div>
        <h3>{work.title}</h3>
        <p>{work.description || 'No description yet.'}</p>
      </div>
      <div className="work-card__meta">
        <VisibilityBadge value={work.visibility} />
        <WorkStatusBadge value={work.work_status} />
        <span>{work.asset_count || 0} assets</span>
      </div>
      <Link className="secondary-button" to={`/works/${work.work_id}`}>
        Edit
      </Link>
    </article>
  )
}
