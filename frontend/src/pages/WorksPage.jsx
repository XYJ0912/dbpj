import { useEffect, useState } from 'react'
import { SectionHeader } from '../components/SectionHeader'
import { WorkCard } from '../components/WorkCard'
import { apiRequest, unwrapEnvelope } from '../lib/api'

export function WorksPage() {
  const [works, setWorks] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [filter, setFilter] = useState('active')
  const [error, setError] = useState('')

  async function loadWorks() {
    const query = filter === 'archived' ? '?status=archived' : ''
    const result = await apiRequest(`/workspace/works${query}`)
    setWorks(unwrapEnvelope(result, 'Unable to load works.'))
  }

  useEffect(() => {
    loadWorks().catch((err) => setError(err.message))
  }, [filter])

  async function createWork(event) {
    event.preventDefault()
    setError('')
    if (!description.trim()) {
      setError('Description is required.')
      return
    }
    try {
      await apiRequest('/workspace/works', {
        method: 'POST',
        body: JSON.stringify({ title, description, work_type: 'other', visibility: 'public', work_status: 'ready' }),
      }).then((result) => unwrapEnvelope(result, 'Unable to create work.'))
      setTitle('')
      setDescription('')
      await loadWorks()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page-stack page-stack--compact works-page">
      <SectionHeader eyebrow="Works" title="Organize assets into reusable portfolio works." />
      <div className="layout-panel layout-panel--dense">
        <strong>Text fields in a Work</strong>
        <p className="field-hint">Summary is the short text shown on homepage cards. Body is the long detail shown after Read more. Description is the general fallback used when Summary or Body is empty.</p>
      </div>
      <form className="compact-form compact-form--tight" onSubmit={createWork}>
        <input required value={title} placeholder="New work title" onChange={(event) => setTitle(event.target.value)} />
        <input required value={description} placeholder="Description (required)" onChange={(event) => setDescription(event.target.value)} />
        <button className="primary-button" type="submit">Create work</button>
      </form>
      <div className="toolbar-row toolbar-row--tight">
        <button type="button" onClick={() => setFilter('active')}>Active</button>
        <button type="button" onClick={() => setFilter('archived')}>Archived</button>
      </div>
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="work-grid">
        {works.map((work) => <WorkCard key={work.work_id} work={work} />)}
      </div>
    </div>
  )
}
