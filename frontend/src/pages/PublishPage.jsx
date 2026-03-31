import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, listToIds, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'

const initialForm = {
  title: '',
  body: '',
  content_type: 'text',
  visibility: 'public',
  tag_ids: '',
  work_ids: '',
  character_ids: '',
}

export function PublishPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const result = await apiRequest('/content', {
        method: 'POST',
        body: JSON.stringify({
          title: form.title,
          body: form.body,
          content_type: form.content_type,
          visibility: form.visibility,
          tag_ids: listToIds(form.tag_ids),
          work_ids: listToIds(form.work_ids),
          character_ids: listToIds(form.character_ids),
        }),
      })
      const data = unwrapEnvelope(result, 'Unable to publish content.')
      navigate(`/content/${data.content_id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page-stack page-stack--narrow">
      <SectionHeader
        eyebrow="Studio"
        title="Publish a new piece with the real API contract."
        subtitle="This page deliberately exposes tag, work, and character IDs because the backend still uses ID-based relations."
      />

      <form className="editorial-form" onSubmit={handleSubmit}>
        <label>
          Title
          <input value={form.title} onChange={(event) => updateField('title', event.target.value)} />
        </label>

        <label>
          Body
          <textarea rows={10} value={form.body} onChange={(event) => updateField('body', event.target.value)} />
        </label>

        <div className="form-grid">
          <label>
            Content type
            <select value={form.content_type} onChange={(event) => updateField('content_type', event.target.value)}>
              <option value="text">text</option>
              <option value="image_post">image_post</option>
              <option value="video_post">video_post</option>
              <option value="mixed">mixed</option>
            </select>
          </label>

          <label>
            Visibility
            <select value={form.visibility} onChange={(event) => updateField('visibility', event.target.value)}>
              <option value="public">public</option>
              <option value="followers_only">followers_only</option>
              <option value="private">private</option>
            </select>
          </label>
        </div>

        <div className="form-grid">
          <label>
            Tag IDs
            <input value={form.tag_ids} onChange={(event) => updateField('tag_ids', event.target.value)} placeholder="1, 2, 3" />
          </label>

          <label>
            Work IDs
            <input value={form.work_ids} onChange={(event) => updateField('work_ids', event.target.value)} placeholder="108" />
          </label>
        </div>

        <label>
          Character IDs
          <input value={form.character_ids} onChange={(event) => updateField('character_ids', event.target.value)} placeholder="211, 212" />
        </label>

        {error ? <div className="error-banner">{error}</div> : null}

        <button className="primary-button" type="submit" disabled={busy}>
          {busy ? 'Publishing...' : 'Publish'}
        </button>
      </form>
    </div>
  )
}
