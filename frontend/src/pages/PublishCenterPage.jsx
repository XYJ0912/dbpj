import { useEffect, useState } from 'react'
import { PublishReport } from '../components/PublishReport'
import { SectionHeader } from '../components/SectionHeader'
import { API_BASE, apiRequest, getStoredUser, unwrapEnvelope } from '../lib/api'

export function PublishCenterPage() {
  const [works, setWorks] = useState([])
  const [selected, setSelected] = useState([])
  const [featured, setFeatured] = useState([])
  const [report, setReport] = useState(null)
  const [snapshot, setSnapshot] = useState(null)
  const [snapshots, setSnapshots] = useState([])
  const [renamingId, setRenamingId] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [homepage, setHomepage] = useState(null)
  const [accentColor, setAccentColor] = useState('#8fb8a8')
  const [error, setError] = useState('')
  const [downloadingId, setDownloadingId] = useState(null)
  const [deployingId, setDeployingId] = useState(null)
  const [gitRepoUrl, setGitRepoUrl] = useState('')
  const [gitBranch, setGitBranch] = useState('main')
  const [gitMessage, setGitMessage] = useState('Update portfolio snapshot')
  const [gitResult, setGitResult] = useState(null)

  async function loadSnapshots() {
    const result = await apiRequest('/publish/snapshots')
    setSnapshots(unwrapEnvelope(result, 'Unable to load snapshots.'))
  }

  useEffect(() => {
    Promise.all([apiRequest('/workspace/works'), apiRequest('/publish/homepage'), apiRequest('/publish/snapshots')])
      .then(([worksResult, homepageResult, snapshotsResult]) => {
        setWorks(unwrapEnvelope(worksResult, 'Unable to load works.'))
        const config = unwrapEnvelope(homepageResult, 'Unable to load homepage config.')
        setHomepage(config)
        setAccentColor(config.accent_color || '#8fb8a8')
        setFeatured((config.featured_work_ids || []).map((item) => Number(item)).filter(Boolean))
        setSnapshots(unwrapEnvelope(snapshotsResult, 'Unable to load snapshots.'))
      })
      .catch((err) => setError(err.message))
  }, [])

  function toggle(workId) {
    setSelected((current) => current.includes(workId) ? current.filter((id) => id !== workId) : [...current, workId])
  }

  function toggleFeatured(workId) {
    setFeatured((current) => current.includes(workId) ? current.filter((id) => id !== workId) : [...current, workId])
  }

  function publishPayload() {
    return { work_ids: selected, featured_work_ids: featured, template_id: 'creator_gallery' }
  }

  async function check() {
    setError('')
      const result = await apiRequest('/publish/check', {
        method: 'POST',
        body: JSON.stringify(publishPayload()),
      })
    const data = unwrapEnvelope(result, 'Publish check failed.')
    setReport(data.report)
  }

  async function generate() {
    setError('')
    try {
      const result = await apiRequest('/publish/snapshot', {
        method: 'POST',
        body: JSON.stringify({ ...publishPayload(), snapshot_name: 'creator-gallery' }),
      })
      const data = unwrapEnvelope(result, 'Unable to generate creator gallery site.')
      setSnapshot(data.snapshot || data)
      setReport(data.report)
      await loadSnapshots()
    } catch (err) {
      setError(err.message)
    }
  }

  function startRename(item) {
    setRenamingId(item.snapshot_id)
    setRenameValue(item.snapshot_name || `snapshot-${item.snapshot_id}`)
  }

  async function renameSnapshot(item) {
    const name = renameValue.trim()
    if (!name || name === item.snapshot_name) {
      setRenamingId(null)
      return
    }
    setError('')
    try {
      await apiRequest(`/publish/snapshots/${item.snapshot_id}`, {
        method: 'PATCH',
        body: JSON.stringify({ snapshot_name: name }),
      }).then((result) => unwrapEnvelope(result, 'Unable to rename snapshot.'))
      setRenamingId(null)
      await loadSnapshots()
    } catch (err) {
      setError(err.message)
    }
  }

  async function downloadSnapshot(item) {
    if (downloadingId) return
    setError('')
    setDownloadingId(item.snapshot_id)
    try {
      const user = getStoredUser()
      const url = item.download_url || `${API_BASE}/publish/snapshots/${item.snapshot_id}/download`
      const response = await fetch(url, {
        headers: user?.token ? { Authorization: `Bearer ${user.token}` } : {},
      })
      if (!response.ok) {
        throw new Error('Unable to download snapshot.')
      }
      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = `${safeDownloadName(item.snapshot_name || `snapshot-${item.snapshot_id}`)}.zip`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30000)
    } catch (err) {
      setError(err.message)
    } finally {
      window.setTimeout(() => setDownloadingId(null), 800)
    }
  }

  async function deleteSnapshot(item) {
    const ok = window.confirm(`Delete snapshot "${item.snapshot_name || item.snapshot_id}" and its exported files?`)
    if (!ok) return
    setError('')
    try {
      await apiRequest(`/publish/snapshots/${item.snapshot_id}`, {
        method: 'DELETE',
      }).then((result) => unwrapEnvelope(result, 'Unable to delete snapshot.'))
      if (snapshot?.snapshot_id === item.snapshot_id) setSnapshot(null)
      await loadSnapshots()
    } catch (err) {
      setError(err.message)
    }
  }

  async function deploySnapshot(item) {
    setError('')
    setGitResult(null)
    if (!gitRepoUrl.trim()) {
      setError('Git repository URL is required.')
      return
    }
    setDeployingId(item.snapshot_id)
    try {
      const result = await apiRequest(`/publish/snapshots/${item.snapshot_id}/git-deploy`, {
        method: 'POST',
        body: JSON.stringify({
          repo_url: gitRepoUrl.trim(),
          branch: gitBranch.trim() || 'main',
          commit_message: gitMessage.trim() || 'Update portfolio snapshot',
        }),
      })
      const data = unwrapEnvelope(result, 'Unable to deploy snapshot with Git.')
      setGitResult(data)
      if (!data.ok) {
        setError(data.error || 'Git deploy failed.')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setDeployingId(null)
    }
  }

  async function saveHomepageLayout() {
    setError('')
    try {
      const result = await apiRequest('/publish/homepage', {
        method: 'PATCH',
        body: JSON.stringify({ template_id: 'creator_gallery', theme: homepage?.theme || 'warm_gallery', accent_color: accentColor, featured_work_ids: featured }),
      })
      setHomepage(unwrapEnvelope(result, 'Unable to save homepage layout.'))
      setReport(null)
    } catch (err) {
      setError(err.message)
    }
  }

  function safeDownloadName(value) {
    return String(value || 'portfolio-gallery-snapshot')
      .trim()
      .replace(/[^a-z0-9._-]+/gi, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 80) || 'portfolio-gallery-snapshot'
  }

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Publish"
        titleClassName="section-header__title--publish"
        title={(
          <>
            Check public content
            <br />
            and export a static
            <br />
            homepage snapshot.
          </>
        )}
      />
      <div className="publish-layout">
        <section className="publish-work-list">
          <div className="layout-panel publish-config-panel">
            <strong>Portfolio Gallery</strong>
            <label className="field-label">
              Accent color
              <input type="color" value={accentColor} onChange={(event) => setAccentColor(event.target.value)} />
            </label>
            <button className="secondary-button secondary-button--compact" type="button" onClick={saveHomepageLayout}>
              Save
            </button>
            <small>{homepage?.template_id || 'creator_gallery'} exports public works and media.</small>
          </div>
          <div className="publish-list-header publish-work-row">
            <span>Use</span>
            <span>Feat.</span>
            <span>Work</span>
            <span>Status</span>
          </div>
          {works.map((work) => (
            <div key={work.work_id} className="publish-work-row">
              <input type="checkbox" checked={selected.includes(work.work_id)} onChange={() => toggle(work.work_id)} aria-label={`Publish ${work.title}`} />
              <input type="checkbox" checked={featured.includes(work.work_id)} onChange={() => toggleFeatured(work.work_id)} aria-label={`Feature ${work.title}`} />
              <strong>{work.title}</strong>
              <small>{work.visibility} / {work.work_status}</small>
            </div>
          ))}
        </section>
        <section>
          <div className="toolbar-row">
            <button className="secondary-button" type="button" onClick={check}>Run check</button>
            <button className="primary-button" type="button" onClick={generate}>Generate Portfolio Gallery Site</button>
          </div>
          {error ? <div className="error-banner">{error}</div> : null}
          {snapshot ? (
            <div className="success-banner snapshot-result">
              <span>Generated: {snapshot.output_dir}</span>
            </div>
          ) : null}
          <PublishReport report={report} />
          <section className="snapshot-panel">
            <div className="panel-heading">
              <strong>Previous snapshots</strong>
              <button className="secondary-button" type="button" onClick={loadSnapshots}>Refresh</button>
            </div>
            <div className="git-deploy-panel">
              <strong>Git deploy assistant</strong>
              <input
                value={gitRepoUrl}
                placeholder="https://github.com/YOUR_NAME/YOUR_REPO.git"
                onChange={(event) => setGitRepoUrl(event.target.value)}
              />
              <div className="git-deploy-row">
                <input value={gitBranch} placeholder="main" onChange={(event) => setGitBranch(event.target.value)} />
                <input value={gitMessage} placeholder="Commit message" onChange={(event) => setGitMessage(event.target.value)} />
              </div>
              <small>Uses your local Git credentials. If push fails, sign in with GitHub Desktop or Git Credential Manager first.</small>
              {gitResult ? (
                <div className={`git-result ${gitResult.ok ? 'git-result--ok' : 'git-result--error'}`}>
                  <strong>{gitResult.ok ? (gitResult.no_changes ? 'No changes to deploy' : 'Git deploy complete') : 'Git deploy failed'}</strong>
                  {gitResult.deploy_dir ? <small>Local repo: {gitResult.deploy_dir}</small> : null}
                  {(gitResult.steps || []).map((step) => <small key={step}>{step}</small>)}
                  {gitResult.human_hint ? <small>{gitResult.human_hint}</small> : null}
                </div>
              ) : null}
            </div>
            {snapshots.length ? (
              <div className="snapshot-list">
                {snapshots.map((item) => (
                  <div key={item.snapshot_id} className="snapshot-row">
                    <div>
                      {renamingId === item.snapshot_id ? (
                        <input
                          className="snapshot-rename-input"
                          value={renameValue}
                          onChange={(event) => setRenameValue(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter') renameSnapshot(item)
                            if (event.key === 'Escape') setRenamingId(null)
                          }}
                        />
                      ) : (
                        <strong>{item.snapshot_name || `snapshot-${item.snapshot_id}`}</strong>
                      )}
                      <small>{item.output_dir}</small>
                      <small>{item.warning_count || 0} warning(s), {item.error_count || 0} error(s)</small>
                    </div>
                    <div className="snapshot-actions">
                      <a className="snapshot-link" href={item.site_url} target="_blank" rel="noreferrer">Open</a>
                      <button
                        className="secondary-button"
                        type="button"
                        disabled={downloadingId === item.snapshot_id}
                        onClick={() => downloadSnapshot(item)}
                      >
                        {downloadingId === item.snapshot_id ? 'Preparing...' : 'Download'}
                      </button>
                      {renamingId === item.snapshot_id ? (
                        <button className="secondary-button" type="button" onClick={() => renameSnapshot(item)}>Save</button>
                      ) : (
                        <button className="secondary-button" type="button" onClick={() => startRename(item)}>Rename</button>
                      )}
                      <button
                        className="secondary-button"
                        type="button"
                        disabled={deployingId === item.snapshot_id}
                        onClick={() => deploySnapshot(item)}
                      >
                        {deployingId === item.snapshot_id ? 'Deploying...' : 'Deploy Git'}
                      </button>
                      <button className="danger-button" type="button" onClick={() => deleteSnapshot(item)}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="screen-state">No snapshots generated yet.</div>
            )}
          </section>
        </section>
      </div>
    </div>
  )
}
