import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'

export function ContentPage() {
  const { contentId } = useParams()
  const [content, setContent] = useState(null)
  const [comments, setComments] = useState([])
  const [commentText, setCommentText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setError('')

    Promise.all([
      apiRequest(`/content/${contentId}`),
      apiRequest(`/content/${contentId}/comments`),
    ])
      .then(([detailResult, commentResult]) => {
        const detail = unwrapEnvelope(detailResult, 'Unable to load content detail.')
        const commentData = unwrapEnvelope(commentResult, 'Unable to load comments.')
        if (active) {
          setContent(detail)
          setComments(Array.isArray(commentData) ? commentData : [])
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message)
        }
      })

    return () => {
      active = false
    }
  }, [contentId])

  async function handleComment(event) {
    event.preventDefault()
    if (!commentText.trim()) {
      return
    }

    setBusy(true)
    setError('')

    try {
      const result = await apiRequest(`/content/${contentId}/comment`, {
        method: 'POST',
        body: JSON.stringify({ text: commentText }),
      })
      unwrapEnvelope(result, 'Unable to publish comment.')
      const freshComments = await apiRequest(`/content/${contentId}/comments`)
      const commentData = unwrapEnvelope(freshComments, 'Unable to refresh comments.')
      setComments(Array.isArray(commentData) ? commentData : [])
      setCommentText('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (error && !content) {
    return <div className="error-banner">{error}</div>
  }

  if (!content) {
    return <div className="screen-state">Loading story...</div>
  }

  return (
    <div className="page-stack page-stack--narrow">
      <SectionHeader
        eyebrow={content.content_type || 'content'}
        title={content.title}
        subtitle={`${content.author_name || 'anonymous'} · ${String(content.created_at || '').slice(0, 10)}`}
      />

      <article className="story-body">
        <div className="story-body__meta">
          <span>{content.visibility}</span>
          <span>{content.like_count ?? 0} likes</span>
          <span>{content.comment_count ?? 0} comments</span>
          <span>{content.view_count ?? 0} views</span>
        </div>
        <div className="story-body__text">{content.body || 'No body available.'}</div>
      </article>

      <section className="meta-columns">
        <div>
          <h3>Tags</h3>
          <p>{content.tags || 'No general tags yet.'}</p>
        </div>
        <div>
          <h3>Works</h3>
          <p>{content.works || 'No works linked.'}</p>
        </div>
        <div>
          <h3>Characters</h3>
          <p>{content.characters || 'No characters linked.'}</p>
        </div>
      </section>

      <section className="comment-block">
        <SectionHeader eyebrow="Discussion" title="Comments" subtitle="The page already uses the live comment endpoint." />
        <form className="editorial-form" onSubmit={handleComment}>
          <label>
            Add a comment
            <textarea rows={4} value={commentText} onChange={(event) => setCommentText(event.target.value)} />
          </label>
          {error ? <div className="error-banner">{error}</div> : null}
          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? 'Posting...' : 'Post comment'}
          </button>
        </form>

        <div className="comment-list">
          {comments.length ? (
            comments.map((comment) => (
              <article key={comment.comment_id} className="comment-item">
                <p className="eyebrow-row">
                  <span>{comment.author_name}</span>
                  <span>{String(comment.created_at || '').slice(0, 16)}</span>
                </p>
                <p>{comment.comment_text}</p>
              </article>
            ))
          ) : (
            <div className="empty-state">No comments yet.</div>
          )}
        </div>
      </section>
    </div>
  )
}
