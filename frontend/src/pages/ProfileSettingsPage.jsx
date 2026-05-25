import { useEffect, useState } from 'react'
import { SectionHeader } from '../components/SectionHeader'
import { apiRequest, unwrapEnvelope } from '../lib/api'

const emptyContact = { label: '', url: '' }

function toList(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function fromList(value) {
  return Array.isArray(value) ? value.join(', ') : ''
}

export function ProfileSettingsPage() {
  const [config, setConfig] = useState(null)
  const [assets, setAssets] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([apiRequest('/publish/homepage'), apiRequest('/assets')])
      .then(([homepageResult, assetResult]) => {
        const homepage = unwrapEnvelope(homepageResult, 'Unable to load profile settings.')
        setConfig({
          ...homepage,
          creator_tags_text: fromList(homepage.creator_tags || []),
          contact_links: normalizeContacts(homepage.contact_links),
        })
        setAssets(unwrapEnvelope(assetResult, 'Unable to load assets.'))
      })
      .catch((err) => setError(err.message))
  }, [])

  async function save(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    const payload = {
      ...config,
      creator_tags: toList(config.creator_tags_text),
      contact_links: (config.contact_links || []).filter((link) => link.label && link.url),
    }
    delete payload.creator_tags_text
    try {
      const result = await apiRequest('/publish/homepage', {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
      const saved = unwrapEnvelope(result, 'Unable to save profile settings.')
      setConfig({
        ...saved,
        creator_tags_text: fromList(saved.creator_tags || []),
        contact_links: normalizeContacts(saved.contact_links),
      })
      setMessage('Profile settings saved.')
    } catch (err) {
      setError(err.message)
    }
  }

  function updateContact(index, patch) {
    setConfig((current) => {
      const links = [...(current.contact_links || [])]
      links[index] = { ...links[index], ...patch }
      return { ...current, contact_links: links }
    })
  }

  if (!config) {
    return <div className="screen-state">{error || 'Loading profile settings...'}</div>
  }

  const imageAssets = assets.filter((asset) => asset.media_type === 'image' && asset.import_status === 'active')

  return (
    <div className="page-stack page-stack--compact">
      <SectionHeader eyebrow="Profile" title="Edit public homepage identity." />
      {error ? <div className="error-banner">{error}</div> : null}
      {message ? <div className="success-banner">{message}</div> : null}
      <form className="editor-panel" onSubmit={save}>
        <label>
          <span>Display name</span>
          <input value={config.display_name || ''} onChange={(event) => setConfig({ ...config, display_name: event.target.value })} />
        </label>
        <label>
          <span>Bio</span>
          <textarea rows={4} value={config.bio || ''} onChange={(event) => setConfig({ ...config, bio: event.target.value })} />
        </label>
        <label>
          <span>Avatar image</span>
          <span className="field-hint">Choose an uploaded image asset. It will be copied into the public snapshot as a relative media file.</span>
          <select value={config.avatar_asset_id || ''} onChange={(event) => setConfig({ ...config, avatar_asset_id: event.target.value ? Number(event.target.value) : null })}>
            <option value="">Use initial placeholder</option>
            {imageAssets.map((asset) => (
              <option key={asset.asset_id} value={asset.asset_id}>
                {asset.asset_name || `Image ${asset.asset_id}`}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Creator tags</span>
          <span className="field-hint">Comma-separated labels, for example Illustration, Character Design, Photography.</span>
          <input value={config.creator_tags_text || ''} onChange={(event) => setConfig({ ...config, creator_tags_text: event.target.value })} />
        </label>
        <div className="contact-editor">
          <strong>Contact links</strong>
          {config.contact_links.map((link, index) => (
            <div key={index} className="contact-editor__row">
              <input value={link.label} placeholder="Label" onChange={(event) => updateContact(index, { label: event.target.value })} />
              <input value={link.url} placeholder="URL or mailto:you@example.com" onChange={(event) => updateContact(index, { url: event.target.value })} />
            </div>
          ))}
          <span className="field-hint">Only filled links are shown on the public homepage.</span>
        </div>
        <label>
          <span>License text</span>
          <textarea rows={3} value={config.license_text || ''} onChange={(event) => setConfig({ ...config, license_text: event.target.value })} />
        </label>
        <button className="primary-button" type="submit">Save profile</button>
      </form>
    </div>
  )
}

function normalizeContacts(links) {
  const defaults = [
    { label: 'Email', url: '' },
    { label: 'X', url: '' },
    { label: 'Instagram', url: '' },
  ]
  const existing = (links || []).filter((link) => link?.label || link?.url)
  const merged = defaults.map((item) => {
    const match = existing.find((link) => String(link.label || '').toLowerCase() === item.label.toLowerCase())
    return cleanContact(match || item)
  })
  existing.forEach((link) => {
    if (!merged.some((item) => item === link || item.label === link.label)) {
      merged.push(cleanContact(link))
    }
  })
  return merged.length ? merged : [emptyContact]
}

function cleanContact(link) {
  return {
    label: link?.label || '',
    url: link?.url === '#' ? '' : link?.url || '',
  }
}
