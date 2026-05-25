import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { SectionHeader } from '../components/SectionHeader'
import { apiRequest, unwrapEnvelope } from '../lib/api'

export function WorkEditorPage() {
  const { workId } = useParams()
  const navigate = useNavigate()
  const [work, setWork] = useState(null)
  const [assets, setAssets] = useState([])
  const [selectedAsset, setSelectedAsset] = useState('')
  const [fillBodyOnAttach, setFillBodyOnAttach] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    const [workResult, assetResult] = await Promise.all([
      apiRequest(`/workspace/works/${workId}`),
      apiRequest('/assets'),
    ])
    setWork(unwrapEnvelope(workResult, 'Unable to load work.'))
    setAssets(unwrapEnvelope(assetResult, 'Unable to load assets.'))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [workId])

  async function patch(patchValue) {
    setError('')
    if ('description' in patchValue && !String(patchValue.description || '').trim()) {
      setError('Description is required.')
      return
    }
    try {
      const result = await apiRequest(`/workspace/works/${workId}`, {
        method: 'PATCH',
        body: JSON.stringify(patchValue),
      })
      setWork(unwrapEnvelope(result, 'Unable to update work.'))
    } catch (err) {
      setError(err.message)
    }
  }

  async function attach(event) {
    event.preventDefault()
    if (!selectedAsset) return
    const assetId = Number(selectedAsset)
    const result = await apiRequest(`/workspace/works/${workId}/assets`, {
      method: 'POST',
      body: JSON.stringify({ asset_id: assetId, role: 'main', is_public: true }),
    })
    setWork(unwrapEnvelope(result, 'Unable to attach asset.'))
    if (fillBodyOnAttach && selectedCanFillBody) {
      const textResult = await apiRequest(`/workspace/works/${workId}/assets/${assetId}/extract-text`, {
        method: 'POST',
      })
      setWork(unwrapEnvelope(textResult, 'Unable to extract text into work.'))
    }
  }

  async function archiveWork() {
    const ok = window.confirm(`Archive work "${work.title}"? You can restore it from the Archived filter.`)
    if (!ok) return
    await apiRequest(`/workspace/works/${workId}/archive`, { method: 'POST' })
      .then((result) => unwrapEnvelope(result, 'Unable to archive work.'))
    navigate('/works')
  }

  async function restoreWork() {
    await apiRequest(`/workspace/works/${workId}/restore`, { method: 'POST' })
      .then((result) => setWork(unwrapEnvelope(result, 'Unable to restore work.')))
  }

  async function deleteWork() {
    const ok = window.confirm(`Permanently delete work "${work.title}"? Its asset files remain in the asset library, but the Work and its bindings will be removed.`)
    if (!ok) return
    await apiRequest(`/workspace/works/${workId}`, { method: 'DELETE' })
      .then((result) => unwrapEnvelope(result, 'Unable to delete work.'))
    navigate('/works')
  }

  async function extractText(asset) {
    setError('')
    try {
      const result = await apiRequest(`/workspace/works/${workId}/assets/${asset.asset_id}/extract-text`, {
        method: 'POST',
      })
      setWork(unwrapEnvelope(result, 'Unable to extract text into work.'))
    } catch (err) {
      setError(err.message)
    }
  }

  if (!work) {
    return <div className="screen-state">{error || 'Loading work...'}</div>
  }

  const imageAssets = (work.assets || []).filter((asset) => asset.media_type === 'image' && asset.is_public)
  const selectedAssetItem = assets.find((asset) => String(asset.asset_id) === String(selectedAsset))
  const selectedCanFillBody = selectedAssetItem?.media_type === 'document'

  return (
    <div className="page-stack page-stack--compact">
      <Link className="secondary-button back-link" to="/works">Back to works</Link>
      <SectionHeader eyebrow="Work editor" title={work.title} />
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="toolbar-row">
        {work.work_status === 'archived' ? (
          <button className="secondary-button" type="button" onClick={restoreWork}>Restore work</button>
        ) : (
          <button className="secondary-button" type="button" onClick={archiveWork}>Archive work</button>
        )}
        <button className="danger-button" type="button" onClick={deleteWork}>Delete permanently</button>
      </div>
      <div className="editor-panel">
        <label>
          Title
          <input value={work.title} onChange={(event) => setWork({ ...work, title: event.target.value })} onBlur={() => patch({ title: work.title })} />
        </label>
        <label>
          <span>Description <span className="required-mark">*</span></span>
          <span className="field-hint">Required general description for this Work. Document text extraction fills Body only and will not overwrite this field.</span>
          <textarea required rows={5} value={work.description || ''} onChange={(event) => setWork({ ...work, description: event.target.value })} onBlur={() => patch({ description: work.description })} />
        </label>
        <label>
          <span>Summary</span>
          <span className="field-hint">Short card copy for the public homepage. If empty, publish auto-generates it from Description or Body.</span>
          <input value={work.summary || ''} onChange={(event) => setWork({ ...work, summary: event.target.value })} onBlur={() => patch({ summary: work.summary })} />
        </label>
        <label>
          <span>Body</span>
          <span className="field-hint">Long-form detail shown in the homepage modal. Use this for article text, process notes, lyrics, or extracted document text.</span>
          <textarea rows={8} value={work.body || ''} onChange={(event) => setWork({ ...work, body: event.target.value })} onBlur={() => patch({ body: work.body })} />
        </label>
        <label>
          Content type
          <select value={work.content_type || 'auto'} onChange={(event) => patch({ content_type: event.target.value })}>
            <option value="auto">auto</option>
            <option value="visual">visual</option>
            <option value="text">text</option>
            <option value="mixed">mixed</option>
            <option value="document">document</option>
            <option value="video">video</option>
            <option value="audio">audio</option>
            <option value="collection">collection</option>
          </select>
        </label>
        <label>
          Cover mode
          <select value={work.cover_mode || 'auto'} onChange={(event) => patch({ cover_mode: event.target.value })}>
            <option value="auto">auto</option>
            <option value="image">image</option>
            <option value="title">title</option>
          </select>
        </label>
        <label>
          Cover asset
          <select value={work.cover_asset_id || ''} onChange={(event) => patch({ cover_asset_id: event.target.value ? Number(event.target.value) : null })}>
            <option value="">Auto select image or first video frame</option>
            {imageAssets.map((asset) => (
              <option key={asset.asset_id} value={asset.asset_id}>
                {asset.asset_name || `Image ${asset.asset_id}`}
              </option>
            ))}
          </select>
        </label>
        <label>
          Visibility
          <select value={work.visibility} onChange={(event) => patch({ visibility: event.target.value })}>
            <option value="private">private</option>
            <option value="public">public</option>
          </select>
        </label>
        <label>
          Status
          <select value={work.work_status} onChange={(event) => patch({ work_status: event.target.value })}>
            <option value="draft">draft</option>
            <option value="ready">ready</option>
            <option value="archived">archived</option>
          </select>
        </label>
      </div>
      <form className="attach-asset-form" onSubmit={attach}>
        <label>
          <span>Attach asset</span>
          <select value={selectedAsset} onChange={(event) => setSelectedAsset(event.target.value)}>
            <option value="">Select asset</option>
            {assets.map((asset) => (
              <option key={asset.asset_id} value={asset.asset_id}>
                {asset.asset_id} - {asset.media_type} - {asset.asset_name || asset.local_path}
              </option>
            ))}
          </select>
        </label>
        {selectedCanFillBody ? (
          <label className="inline-check">
            <input
              type="checkbox"
              checked={fillBodyOnAttach}
              onChange={(event) => setFillBodyOnAttach(event.target.checked)}
            />
            Use document text for Body
          </label>
        ) : null}
        <button className="primary-button" type="submit">Attach</button>
      </form>
      <div className="asset-table">
        <p className="field-hint">Publish exports only assets that are public, active, public in this Work, and not restricted.</p>
        {work.assets?.map((asset) => (
          <div key={asset.asset_id} className="asset-row">
            <span>{asset.asset_name || asset.asset_id}</span>
            <span>{asset.media_type}</span>
            <span>{asset.role}</span>
            <span>{asset.visibility} / {asset.import_status} / {asset.authorization_status}</span>
            <span>{asset.is_public ? 'public in work' : 'private in work'}</span>
            {asset.media_type === 'document' ? (
              <button className="secondary-button" type="button" onClick={() => extractText(asset)}>
                Use text as body
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  )
}
