import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiRequest, unwrapEnvelope } from '../lib/api'
import { SectionHeader } from '../components/SectionHeader'
import { MetricStrip } from '../components/MetricStrip'

const tabs = ['tags', 'works', 'friends', 'feed']

export function ProfilePage() {
  const { userId } = useParams()
  const [profile, setProfile] = useState(null)
  const [tab, setTab] = useState('tags')
  const [tabData, setTabData] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setError('')

    apiRequest(`/user/${userId}/profile`)
      .then((result) => {
        const data = unwrapEnvelope(result, 'Unable to load profile.')
        if (active) {
          setProfile(data)
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
  }, [userId])

  useEffect(() => {
    let active = true
    setError('')
    const pathByTab = {
      feed: `/user/${userId}/feed`,
      tags: `/user/${userId}/tags`,
      works: `/user/${userId}/works`,
      friends: `/user/${userId}/friends`,
    }

    apiRequest(pathByTab[tab])
      .then((result) => {
        const data = unwrapEnvelope(result, `Unable to load ${tab}.`)
        const nextData = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
        if (active) {
          setTabData(nextData)
        }
      })
      .catch((err) => {
        if (active) {
          setTabData([])
          setError(err.message)
        }
      })

    return () => {
      active = false
    }
  }, [tab, userId])

  if (error && !profile) {
    return <div className="error-banner">{error}</div>
  }

  if (!profile) {
    return <div className="screen-state">Loading profile...</div>
  }

  return (
    <div className="page-stack">
      <SectionHeader
        eyebrow="Profile"
        title={profile.username}
        subtitle={profile.bio || 'This account has not added a bio yet.'}
      />

      <MetricStrip
        metrics={[
          { label: 'Followers', value: profile.follower_count },
          { label: 'Following', value: profile.following_count },
          { label: 'Published', value: profile.published_content_count },
          { label: 'Drafts', value: profile.draft_content_count },
        ]}
      />

      <div className="tab-row">
        {tabs.map((item) => (
          <button
            key={item}
            className={`tab-row__button${item === tab ? ' is-active' : ''}`}
            type="button"
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="profile-panel">
        {tab === 'feed'
          ? tabData.map((item) => (
              <article key={item.content_id} className="profile-line-item">
                <Link to={`/content/${item.content_id}`}>{item.title}</Link>
                <span>{String(item.created_at || '').slice(0, 10)}</span>
              </article>
            ))
          : null}

        {tab === 'tags'
          ? tabData.map((item) => (
              <article key={item.tag_id} className="profile-line-item">
                <span>#{item.tag_name}</span>
                <span>{item.interaction_score}</span>
              </article>
            ))
          : null}

        {tab === 'works'
          ? tabData.map((item) => (
              <article key={item.tag_id} className="profile-line-item">
                <span>{item.tag_name}</span>
                <span>{item.interaction_score}</span>
              </article>
            ))
          : null}

        {tab === 'friends'
          ? tabData.map((item) => (
              <article key={item.friend_id} className="profile-line-item">
                <Link to={`/profile/${item.friend_id}`}>{item.friend_name}</Link>
                <span>{String(item.follow_time || '').slice(0, 10)}</span>
              </article>
            ))
          : null}

        {!tabData.length ? <div className="empty-state">No visible data for this tab.</div> : null}
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
    </div>
  )
}
