export function VisibilityBadge({ value }) {
  return <span className={`status-badge status-badge--${value || 'private'}`}>{value || 'private'}</span>
}

export function AuthorizationBadge({ value }) {
  return <span className={`status-badge status-badge--${value || 'unknown'}`}>{value || 'unknown'}</span>
}

export function AssetTypeBadge({ value }) {
  return <span className="status-badge status-badge--neutral">{value || 'asset'}</span>
}

export function WorkStatusBadge({ value }) {
  return <span className={`status-badge status-badge--${value || 'draft'}`}>{value || 'draft'}</span>
}
