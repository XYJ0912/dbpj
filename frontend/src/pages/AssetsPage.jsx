import { useEffect, useMemo, useState } from 'react'
import { AssetGrid } from '../components/AssetGrid'
import { AssetInspector } from '../components/AssetInspector'
import { SectionHeader } from '../components/SectionHeader'
import { apiRequest, unwrapEnvelope } from '../lib/api'

const initialForm = {
  local_path: '',
  media_type: 'image',
  mime_type: '',
  thumbnail_path: '',
  visibility: 'public',
  authorization_status: 'licensed',
}

export function AssetsPage() {
  const [assets, setAssets] = useState([])
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)

  async function loadAssets() {
    const query = filter === 'archived' ? '?status=archived' : ''
    const result = await apiRequest(`/assets${query}`)
    const data = unwrapEnvelope(result, 'Unable to load assets.')
    setAssets(data)
    setSelected((current) => data.find((item) => item.asset_id === current?.asset_id) || data[0] || null)
  }

  useEffect(() => {
    loadAssets().catch((err) => setError(err.message))
  }, [filter])

  const filteredAssets = useMemo(() => {
    if (filter === 'all' || filter === 'archived') return assets
    return assets.filter((asset) => asset.visibility === filter)
  }, [assets, filter])

  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      await apiRequest('/assets/import', {
        method: 'POST',
        body: JSON.stringify(form),
      }).then((result) => unwrapEnvelope(result, 'Unable to import asset.'))
      setForm(initialForm)
      await loadAssets()
    } catch (err) {
      setError(err.message)
    }
  }

  async function patchAsset(mediaId, patch) {
    await apiRequest(`/assets/${mediaId}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }).then((result) => unwrapEnvelope(result, 'Unable to update asset.'))
    await loadAssets()
  }

  async function archiveAsset(asset) {
    if (!asset) return
    const ok = window.confirm(`Archive asset "${asset.asset_name || asset.asset_id}"? You can restore it later from Archived.`)
    if (!ok) return
    setError('')
    try {
      await apiRequest(`/assets/${asset.asset_id}/archive`, {
        method: 'POST',
      }).then((result) => unwrapEnvelope(result, 'Unable to archive asset.'))
      setSelected(null)
      await loadAssets()
    } catch (err) {
      setError(err.message)
    }
  }

  async function restoreAsset(asset) {
    if (!asset) return
    setError('')
    try {
      await apiRequest(`/assets/${asset.asset_id}/restore`, {
        method: 'POST',
      }).then((result) => unwrapEnvelope(result, 'Unable to restore asset.'))
      await loadAssets()
    } catch (err) {
      setError(err.message)
    }
  }

  async function deleteAsset(asset) {
    if (!asset) return
    const ok = window.confirm(`Permanently delete asset "${asset.asset_name || asset.asset_id}"? You will need to upload or import it again.`)
    if (!ok) return
    setError('')
    try {
      await apiRequest(`/assets/${asset.asset_id}`, {
        method: 'DELETE',
      }).then((result) => unwrapEnvelope(result, 'Unable to delete asset.'))
      setSelected(null)
      await loadAssets()
    } catch (err) {
      setError(err.message)
    }
  }

  async function uploadFiles(fileList) {
    const files = Array.from(fileList || [])
    if (!files.length) return
    setUploading(true)
    setError('')
    try {
      const body = new FormData()
      files.forEach((file) => body.append('files', file))
      body.append('visibility', form.visibility)
      body.append('authorization_status', form.authorization_status)
      body.append('allow_public_display', form.authorization_status === 'original' || form.authorization_status === 'licensed')
      await apiRequest('/assets/upload', {
        method: 'POST',
        body,
      }).then((result) => unwrapEnvelope(result, 'Unable to upload assets.'))
      await loadAssets()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      setDragging(false)
    }
  }

  return (
    <div className="workspace-layout">
      <section className="workspace-main">
        <SectionHeader eyebrow="Assets" title="Upload media or register local references." />
        <div
          className={`drop-zone${dragging ? ' drop-zone--active' : ''}`}
          onDragEnter={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={(event) => {
            event.preventDefault()
            setDragging(false)
          }}
          onDrop={(event) => {
            event.preventDefault()
            uploadFiles(event.dataTransfer.files)
          }}
        >
          <div>
            <strong>{uploading ? 'Uploading...' : 'Drag media files here'}</strong>
            <span>Images, videos, audio, PDFs, docs. Files are copied into this project under uploads/.</span>
          </div>
          <label className="secondary-button">
            Choose files
            <input
              type="file"
              multiple
              hidden
              onChange={(event) => {
                uploadFiles(event.target.files)
                event.target.value = ''
              }}
            />
          </label>
        </div>
        <div className="compact-form">
          <select value={form.visibility} onChange={(event) => setForm({ ...form, visibility: event.target.value })}>
            <option value="public">Upload as public</option>
            <option value="private">Upload as private</option>
          </select>
          <select value={form.authorization_status} onChange={(event) => setForm({ ...form, authorization_status: event.target.value })}>
            <option value="licensed">licensed</option>
            <option value="original">original</option>
            <option value="unknown">unknown license</option>
            <option value="restricted">restricted</option>
          </select>
        </div>
        <div className="toolbar-row">
          <button type="button" onClick={() => setFilter('all')}>All</button>
          <button type="button" onClick={() => setFilter('public')}>Public</button>
          <button type="button" onClick={() => setFilter('private')}>Private</button>
          <button type="button" onClick={() => setFilter('archived')}>Archived</button>
        </div>
        {error ? <div className="error-banner">{error}</div> : null}
        <AssetGrid assets={filteredAssets} selectedId={selected?.asset_id} onSelect={setSelected} />
      </section>
      <AssetInspector asset={selected} onPatch={patchAsset} onArchive={archiveAsset} onRestore={restoreAsset} onDelete={deleteAsset} />
    </div>
  )
}
