import { AssetTypeBadge, AuthorizationBadge, VisibilityBadge } from './StatusBadges'
import { API_BASE } from '../lib/api'

function isBrowserImagePath(value) {
  if (!value) return false
  return (
    value.startsWith('http://') ||
    value.startsWith('https://') ||
    value.startsWith('data:') ||
    value.startsWith('blob:') ||
    value.startsWith('/')
  )
}

function previewSrc(asset) {
  const directPath = [asset.thumbnail_path, asset.public_export_path].find(isBrowserImagePath)
  if (directPath) {
    return directPath
  }
  if (['image', 'video', 'audio'].includes(asset.media_type)) {
    return `${API_BASE}/assets/${asset.asset_id}/preview`
  }
  return ''
}

export function AssetGrid({ assets, selectedId, onSelect }) {
  if (!assets?.length) {
    return <div className="screen-state">No assets yet.</div>
  }

  return (
    <div className="asset-grid">
      {assets.map((asset) => {
        const src = previewSrc(asset)
        return (
          <button
            key={asset.asset_id}
            className={`asset-card ${selectedId === asset.asset_id ? 'asset-card--active' : ''}`}
            type="button"
            onClick={() => onSelect(asset)}
          >
            <div className="asset-card__preview">
              {src && asset.media_type === 'image' ? (
                <img
                  src={src}
                  alt=""
                  onError={(event) => {
                    event.currentTarget.style.display = 'none'
                  }}
                />
              ) : src && asset.media_type === 'video' ? (
                <video src={src} muted controls preload="metadata" />
              ) : src && asset.media_type === 'audio' ? (
                <div className="asset-audio-preview">
                  <span>audio</span>
                  <audio src={src} controls preload="metadata" />
                </div>
              ) : (
                <span>{asset.media_type}</span>
              )}
            </div>
            <div className="asset-card__body">
              <strong>{asset.asset_name || asset.local_path || `Asset ${asset.asset_id}`}</strong>
              <div className="badge-row">
                <AssetTypeBadge value={asset.media_type} />
                <VisibilityBadge value={asset.visibility} />
                <AuthorizationBadge value={asset.authorization_status} />
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
