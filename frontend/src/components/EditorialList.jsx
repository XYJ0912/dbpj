import { Link } from 'react-router-dom'

function formatDate(value) {
  if (!value) {
    return 'Unknown date'
  }
  return String(value).slice(0, 10)
}

export function EditorialList({ items = [], compact = false }) {
  if (!items.length) {
    return <div className="empty-state">No items yet.</div>
  }

  return (
    <div className="editorial-list">
      {items.map((item, index) => (
        <article key={item.content_id} className={`editorial-item${compact ? ' editorial-item--compact' : ''}`}>
          <div className="editorial-item__index">{String(index + 1).padStart(2, '0')}</div>
          <div className="editorial-item__body">
            <div className="eyebrow-row">
              <span>{item.content_type || 'content'}</span>
              <span>{item.author_name || 'anonymous'}</span>
            </div>
            <h3>
              <Link to={`/content/${item.content_id}`}>{item.title}</Link>
            </h3>
            <p className="editorial-item__meta">
              {formatDate(item.created_at)} · {item.like_count ?? 0} likes · {item.comment_count ?? 0} comments
            </p>
          </div>
        </article>
      ))}
    </div>
  )
}
