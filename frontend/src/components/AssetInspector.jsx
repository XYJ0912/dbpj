import { AuthorizationBadge, VisibilityBadge } from './StatusBadges'
import { API_BASE, apiRequest, unwrapEnvelope } from '../lib/api'
import { useEffect, useState } from 'react'

export function AssetInspector({ asset, onPatch, onArchive, onRestore, onDelete }) {
  const [previewOpen, setPreviewOpen] = useState(false)
  if (!asset) {
    return <aside className="side-inspector">Select an asset to inspect metadata.</aside>
  }

  return (
    <aside className="side-inspector">
      <h2>{asset.asset_name || `Asset ${asset.asset_id}`}</h2>
      <div className="badge-row">
        <VisibilityBadge value={asset.visibility} />
        <AuthorizationBadge value={asset.authorization_status} />
      </div>
      <dl className="meta-list">
        <dt>Type</dt>
        <dd>{asset.media_type}</dd>
        <dt>Size</dt>
        <dd>{asset.file_size || '-'}</dd>
        <dt>Path</dt>
        <dd>{asset.local_path || asset.file_path || '-'}</dd>
        <dt>Status</dt>
        <dd>{asset.import_status}</dd>
      </dl>
      <AssetPreview asset={asset} onOpen={() => setPreviewOpen(true)} />
      {previewOpen ? <PreviewDialog asset={asset} onClose={() => setPreviewOpen(false)} /> : null}
      <div className="inspector-actions">
        {asset.import_status === 'archived' ? (
          <button type="button" onClick={() => onRestore(asset)}>
            Restore asset
          </button>
        ) : (
          <>
            <button type="button" onClick={() => onPatch(asset.asset_id, { visibility: asset.visibility === 'public' ? 'private' : 'public' })}>
              Toggle visibility
            </button>
            <button type="button" onClick={() => onPatch(asset.asset_id, { authorization_status: 'original', allow_public_display: true })}>
              Mark original
            </button>
            <button type="button" onClick={() => onPatch(asset.asset_id, { authorization_status: 'licensed', allow_public_display: true })}>
              Mark licensed
            </button>
            <button type="button" onClick={() => onPatch(asset.asset_id, { authorization_status: 'restricted', allow_public_display: false })}>
              Restrict
            </button>
            <button className="secondary-button" type="button" onClick={() => onArchive(asset)}>
              Archive asset
            </button>
          </>
        )}
        <button className="danger-button" type="button" onClick={() => onDelete(asset)}>
          Delete permanently
        </button>
      </div>
    </aside>
  )
}

function previewSrc(asset) {
  return `${API_BASE}/assets/${asset.asset_id}/preview`
}

function fileExtension(asset) {
  const names = [asset.asset_name, asset.local_path, asset.public_export_path, asset.thumbnail_path].filter(Boolean)
  for (const name of names) {
    const parts = String(name).split('.')
    if (parts.length > 1) return parts.pop().toLowerCase()
  }
  const mime = asset.mime_type || ''
  if (mime === 'text/markdown') return 'md'
  if (mime === 'text/plain') return 'txt'
  if (mime === 'application/pdf') return 'pdf'
  if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return 'docx'
  if (mime === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') return 'pptx'
  return ''
}

function isTextDocumentAsset(asset, ext) {
  return asset.media_type === 'document' || ['docx', 'pptx', 'md', 'txt', 'markdown', 'pdf'].includes(ext)
}

function AssetPreview({ asset, onOpen }) {
  const src = previewSrc(asset)
  const ext = fileExtension(asset)
  const [textPreview, setTextPreview] = useState(null)

  useEffect(() => {
    setTextPreview(null)
    if (!isTextDocumentAsset(asset, ext)) return
    apiRequest(`/assets/${asset.asset_id}/text`)
      .then((result) => unwrapEnvelope(result, 'Unable to extract text.'))
      .then((data) => setTextPreview(data))
      .catch(() => setTextPreview({ text: '', warning: 'Text preview is not available.' }))
  }, [asset.asset_id, asset.media_type, ext])

  if (asset.media_type === 'image') {
    return <button className="inspector-preview" type="button" onClick={onOpen}><img src={src} alt="" /></button>
  }
  if (asset.media_type === 'video') {
    return <button className="inspector-preview" type="button" onClick={onOpen}><video src={src} preload="metadata" /></button>
  }
  if (asset.media_type === 'audio') {
    return <div className="inspector-preview inspector-preview--audio"><audio src={src} controls preload="metadata" /></div>
  }
  if (isTextDocumentAsset(asset, ext)) {
    if (['md', 'markdown'].includes(ext)) {
      return (
        <div className="inspector-preview inspector-preview--document">
          <iframe title="Document preview" src={src} />
        </div>
      )
    }
    if (ext === 'pdf') {
      return (
        <div className="inspector-preview inspector-preview--document">
          <iframe title="Document preview" src={src} />
        </div>
      )
    }
    if (ext === 'txt') {
      return (
        <div className="inspector-preview inspector-preview--file">
          <strong>Text document</strong>
          {textPreview?.text ? <pre>{textPreview.text}</pre> : <span>{textPreview?.warning || 'Extracting text preview...'}</span>}
        </div>
      )
    }
    if (['docx', 'pptx'].includes(ext)) {
      return (
        <div className="inspector-preview inspector-preview--file">
          <strong>{ext.toUpperCase()} document</strong>
          <span>Office files are decoded into plain text for local preview. Formatting is not preserved.</span>
          {textPreview?.text ? <pre>{textPreview.text}</pre> : <span>{textPreview?.warning || 'Extracting text preview...'}</span>}
        </div>
      )
    }
    if (['doc', 'ppt'].includes(ext)) {
      return (
        <div className="inspector-preview inspector-preview--file">
          <strong>{ext.toUpperCase()} document</strong>
          <span>Legacy Office binary files cannot be decoded reliably in this local preview. Convert to DOCX/PPTX for text extraction.</span>
          <a className="secondary-button" href={src} target="_blank" rel="noreferrer">Open file</a>
        </div>
      )
    }
  }
  if (asset.media_type === 'other') {
    return (
      <div className="inspector-preview inspector-preview--file">
        <strong>{ext ? ext.toUpperCase() : 'File'} asset</strong>
        <a className="secondary-button" href={src} target="_blank" rel="noreferrer">Open file</a>
      </div>
    )
  }
  return null
}

function PreviewDialog({ asset, onClose }) {
  const src = previewSrc(asset)
  const ext = fileExtension(asset)
  return (
    <div className="preview-dialog" role="dialog" aria-modal="true">
      <button className="preview-dialog__backdrop" type="button" onClick={onClose} aria-label="Close preview" />
      <div className="preview-dialog__panel">
        <button className="preview-dialog__close" type="button" onClick={onClose} aria-label="Close preview">&times;</button>
        {asset.media_type === 'image' ? <img src={src} alt="" /> : null}
        {asset.media_type === 'video' ? <video src={src} controls autoPlay /> : null}
        {asset.media_type === 'audio' ? <audio src={src} controls autoPlay /> : null}
        {isTextDocumentAsset(asset, ext) && ['pdf', 'md', 'markdown'].includes(ext) ? <iframe title="Document preview" src={src} /> : null}
        {isTextDocumentAsset(asset, ext) && ext === 'txt' ? <pre>{textPreview?.text || ''}</pre> : null}
      </div>
    </div>
  )
}
