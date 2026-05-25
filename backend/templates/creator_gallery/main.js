const demoData = {
  profile: {
    display_name: 'Mori Studio',
    bio: 'Illustration, character design, and visual storytelling.',
    avatar: '',
    creator_tags: ['Illustration', 'Character Design', 'Photography'],
    contact_links: [
      { label: 'Email', url: 'mailto:hello@example.com' },
      { label: 'X', url: '#' },
      { label: 'Instagram', url: '#' },
    ],
    license_text: 'Unless otherwise noted, works are for portfolio display only.',
  },
  homepage: {
    template_id: 'creator_gallery',
    theme: 'warm_gallery',
    accent_color: '#8fb8a8',
    featured_work_ids: [],
  },
  works: [
    {
      id: 'demo_001',
      title: 'Night Patrol',
      summary: 'A neon character design study for a quiet urban scene.',
      body: 'A character design study built around neon lighting and quiet urban scenes.',
      description: 'A character design study built around neon lighting and quiet urban scenes.',
      content_type: 'visual',
      cover_mode: 'auto',
      cover: '',
      tags: ['Character', 'Cyberpunk', 'Original'],
      authorization_status: 'original',
      visibility: 'public',
      featured: true,
      assets: [],
    },
    {
      id: 'demo_002',
      title: 'Spring Archive',
      summary: 'A soft-color seasonal illustration series.',
      body: 'A soft-color illustration series exploring seasonal memory and personal objects.',
      description: 'A soft-color illustration series exploring seasonal memory and personal objects.',
      content_type: 'visual',
      cover_mode: 'auto',
      cover: '',
      tags: ['Illustration', 'Series'],
      authorization_status: 'original',
      visibility: 'public',
      featured: true,
      assets: [],
    },
    {
      id: 'demo_003',
      title: 'Portrait Practice',
      summary: 'Lighting and expression studies collected as a practice set.',
      body: 'A collection of lighting and expression studies.',
      description: 'A collection of lighting and expression studies.',
      content_type: 'visual',
      cover_mode: 'auto',
      cover: '',
      tags: ['Portrait', 'Study'],
      authorization_status: 'licensed',
      visibility: 'public',
      featured: false,
      assets: [],
    },
  ],
  tags: [
    { name: 'Illustration', count: 2 },
    { name: 'Original', count: 1 },
    { name: 'Study', count: 1 },
  ],
}

const data = window.__CREATOR_DATA__ || demoData

function $(id) {
  return document.getElementById(id)
}

function setText(id, value) {
  const el = $(id)
  if (el) el.textContent = value || ''
}

function safeUrl(value) {
  const url = String(value || '').trim()
  if (!url) return ''
  if (url.startsWith('javascript:')) return ''
  return url
}

function firstLetter(value) {
  return String(value || 'C').trim().charAt(0).toUpperCase() || 'C'
}

function make(tagName, className, text) {
  const el = document.createElement(tagName)
  if (className) el.className = className
  if (text) el.textContent = text
  return el
}

function normalizeCreatorTags(tags) {
  return (tags || [])
    .flatMap((tag) => String(tag || '').split(/\s+/))
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function assetFormat(asset) {
  const path = String(asset?.path || '')
  return String(asset?.format || path.split('.').pop() || '').toLowerCase()
}

function isMarkdownAsset(asset) {
  return ['md', 'markdown'].includes(assetFormat(asset))
}

function isPdfAsset(asset) {
  return assetFormat(asset) === 'pdf'
}

function init(siteData) {
  const profile = siteData.profile || demoData.profile
  const works = Array.isArray(siteData.works) ? siteData.works : []
  const homepage = siteData.homepage || {}

  if (homepage.accent_color) {
    document.documentElement.style.setProperty('--accent-color', homepage.accent_color)
  }

  renderProfile(profile)
  renderFeaturedWorks(works)
  renderGallery(works)
  setupFilters(works)
  setupModal()

  setText('year', String(new Date().getFullYear()))
}

function renderProfile(profile) {
  const displayName = profile.display_name || 'Portfolio Gallery'
  document.title = `${displayName} - Portfolio Gallery`
  setText('site-title', displayName)
  setText('display-name', displayName)
  setText('bio', profile.bio || 'Selected public works and visual stories.')
  setText('about-name', displayName)
  setText('footer-name', displayName)
  setText('license-text', profile.license_text || '')

  const avatar = $('avatar')
  avatar.replaceChildren()
  const avatarUrl = safeUrl(profile.avatar || profile.avatar_url)
  if (avatarUrl) {
    const img = make('img', 'avatar-image')
    img.src = avatarUrl
    img.alt = `${displayName} avatar`
    img.addEventListener('error', () => {
      avatar.className = 'avatar-placeholder'
      avatar.replaceChildren(document.createTextNode(firstLetter(displayName)))
    })
    avatar.className = ''
    avatar.appendChild(img)
  } else {
    avatar.className = 'avatar-placeholder'
    avatar.textContent = firstLetter(displayName)
  }

  const tags = $('creator-tags')
  tags.replaceChildren()
  normalizeCreatorTags(profile.creator_tags).forEach((tag) => {
    tags.appendChild(make('span', 'tag-pill', tag))
  })
  tags.classList.toggle('is-hidden', !tags.children.length)

  const contacts = $('contact-buttons')
  contacts.replaceChildren()
  ;(profile.contact_links || []).forEach((link) => {
    const url = safeUrl(link.url)
    if (!url) return
    const button = make('button', 'contact-link', link.label || 'Contact')
    button.type = 'button'
    button.title = contactDisplayValue(url)
    button.addEventListener('click', () => openContactModal(link.label || 'Contact', url))
    contacts.appendChild(button)
  })
  contacts.classList.toggle('is-hidden', !contacts.children.length)
}

function renderFeaturedWorks(works) {
  const featured = works.filter((work) => work.featured).slice(0, 4)
  const section = $('featured-section')
  const grid = $('featured-grid')
  grid.replaceChildren()
  section.classList.toggle('is-hidden', featured.length === 0)
  featured.forEach((work) => grid.appendChild(createWorkCard(work, true)))
}

function renderGallery(works) {
  const grid = $('works-grid')
  grid.replaceChildren()
  if (!works.length) {
    grid.appendChild(make('div', 'empty-state', 'No public works yet.'))
    return
  }
  works.forEach((work) => grid.appendChild(createWorkCard(work, false)))
}

function setupFilters(works) {
  const controls = $('filter-controls')
  controls.replaceChildren()
  const tags = Array.from(new Set(works.flatMap((work) => work.tags || []))).sort()
  if (!tags.length) {
    controls.classList.add('is-hidden')
    return
  }
  controls.classList.remove('is-hidden')
  const all = make('button', 'filter-btn is-active', 'All')
  all.type = 'button'
  all.addEventListener('click', () => applyFilter('', works))
  controls.appendChild(all)
  tags.forEach((tag) => {
    const button = make('button', 'filter-btn', tag)
    button.type = 'button'
    button.addEventListener('click', () => applyFilter(tag, works))
    controls.appendChild(button)
  })
}

function applyFilter(tag, works) {
  document.querySelectorAll('.filter-btn').forEach((button) => {
    button.classList.toggle('is-active', button.textContent === (tag || 'All'))
  })
  const visible = tag ? works.filter((work) => (work.tags || []).includes(tag)) : works
  renderGallery(visible)
}

function shouldUseImageCard(work) {
  const mode = work.cover_mode || 'auto'
  const cover = safeUrl(work.cover)
  if (mode === 'title') return false
  if (mode === 'image') return Boolean(cover)
  return Boolean(cover)
}

function createWorkCard(work, featured = false) {
  const imageCard = shouldUseImageCard(work)
  const article = make('article', `work-card ${imageCard ? 'image-card' : 'title-card'}${featured ? ' featured-card' : ''}`)
  article.tabIndex = 0
  article.setAttribute('role', 'button')
  article.addEventListener('click', () => openWorkModal(work))
  article.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openWorkModal(work)
    }
  })

  if (imageCard) {
    const media = make('div', 'work-media')
    const img = make('img')
    img.src = safeUrl(work.cover)
    img.alt = work.title || 'Work cover'
    img.loading = 'lazy'
    img.addEventListener('error', () => {
      article.classList.remove('image-card')
      article.classList.add('title-card')
      media.remove()
    })
    media.appendChild(img)
    article.appendChild(media)
  }

  const body = make('div', 'work-card-body')
  if (!imageCard) {
    body.appendChild(make('span', 'content-type-badge', work.content_type || 'work'))
  }
  body.appendChild(make('h3', '', work.title || 'Untitled work'))
  body.appendChild(make('p', 'work-summary', work.summary || work.description || 'No summary.'))

  const meta = make('div', 'work-meta')
  ;(work.tags || []).forEach((tag) => meta.appendChild(make('span', 'tag-pill', tag)))
  if (work.authorization_status) {
    meta.appendChild(make('span', 'license-badge', work.authorization_status))
  }
  body.appendChild(meta)

  if (!imageCard && ['audio', 'document'].includes(work.content_type)) {
    body.appendChild(createTypePreview(work))
  } else {
    const strip = createAssetPreviewStrip(work, imageCard)
    if (strip) {
      body.appendChild(strip)
    }
  }

  if (!imageCard) {
    const more = make('button', 'read-more', 'Read more')
    more.type = 'button'
    more.addEventListener('click', (event) => {
      event.stopPropagation()
      openWorkModal(work)
    })
    body.appendChild(more)
  }

  article.appendChild(body)
  return article
}

function createTypePreview(work) {
  const type = work.content_type || 'work'
  const preview = make('div', `type-preview type-preview--${type}`)
  if (type === 'audio') {
    const audioMark = make('div', 'audio-mark')
    audioMark.appendChild(make('span', 'audio-note', '♪'))
    audioMark.appendChild(make('span', 'audio-line'))
    preview.appendChild(audioMark)
    preview.appendChild(make('span', 'type-preview-label', 'Audio work'))
    return preview
  }
  if (type === 'document') {
    const lines = make('div', 'document-lines')
    ;[92, 72, 84, 54, 78].forEach((width) => {
      const line = make('span')
      line.style.width = `${width}%`
      lines.appendChild(line)
    })
    preview.appendChild(lines)
    preview.appendChild(make('span', 'type-preview-label', 'Document work'))
    return preview
  }
  preview.appendChild(make('span', 'type-preview-label', type))
  return preview
}

function createAssetPreviewStrip(work, imageCard) {
  const assets = (work.assets || []).filter((asset) => safeUrl(asset.path)).slice(0, imageCard ? 4 : 3)
  if (!assets.length || (imageCard && assets.length <= 1)) return null
  const strip = make('div', imageCard ? 'asset-strip' : 'asset-strip asset-strip--rich')
  assets.forEach((asset) => {
    strip.appendChild(createAssetThumb(asset))
  })
  return strip
}

function createAssetThumb(asset) {
  const thumb = make('span', `asset-thumb asset-thumb--${asset.type || 'other'}`)
  const path = safeUrl(asset.path)
  if (asset.type === 'image') {
    const img = make('img')
    img.src = path
    img.alt = ''
    img.loading = 'lazy'
    img.addEventListener('error', () => {
      thumb.classList.add('asset-thumb-empty')
      thumb.replaceChildren(make('span', '', 'image'))
    })
    thumb.appendChild(img)
    return thumb
  }
  if (asset.type === 'video') {
    const video = make('video')
    video.src = path
    video.preload = 'metadata'
    video.muted = true
    video.playsInline = true
    thumb.appendChild(video)
    thumb.appendChild(make('span', 'asset-kind', 'video'))
    return thumb
  }
  if (asset.type === 'audio') {
    thumb.appendChild(make('span', 'asset-kind', 'audio'))
    return thumb
  }
  thumb.appendChild(make('span', 'asset-kind', asset.type || 'file'))
  return thumb
}

function handleImageFallback(container, label) {
  container.replaceChildren(make('div', 'image-fallback', firstLetter(label)))
}

function setupModal() {
  const modal = $('work-modal')
  const close = $('modal-close')
  close.addEventListener('click', closeWorkModal)
  modal.querySelector('[data-close-modal]').addEventListener('click', closeWorkModal)
  const contact = $('contact-modal')
  $('contact-modal-close').addEventListener('click', closeContactModal)
  contact.querySelector('[data-close-contact]').addEventListener('click', closeContactModal)
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !modal.classList.contains('is-hidden')) {
      closeWorkModal()
    }
    if (event.key === 'Escape' && !contact.classList.contains('is-hidden')) {
      closeContactModal()
    }
  })
}

function contactDisplayValue(url) {
  return String(url || '').replace(/^mailto:/, '')
}

function openContactModal(label, url) {
  const modal = $('contact-modal')
  const content = $('contact-modal-content')
  content.replaceChildren()
  content.appendChild(make('p', 'eyebrow', label))
  content.appendChild(make('h2', 'contact-value', contactDisplayValue(url)))
  modal.classList.remove('is-hidden')
  document.body.classList.add('modal-open')
}

function closeContactModal() {
  $('contact-modal').classList.add('is-hidden')
  document.body.classList.remove('modal-open')
}

function openWorkModal(work) {
  const modal = $('work-modal')
  const content = $('modal-content')
  content.replaceChildren()

  const header = make('div', 'modal-header')
  header.appendChild(make('span', 'content-type-badge', work.content_type || 'work'))
  header.appendChild(make('h2', '', work.title || 'Untitled work'))
  content.appendChild(header)

  const cover = safeUrl(work.cover)
  if (cover) {
    const media = make('div', 'modal-cover')
    const img = make('img')
    img.src = cover
    img.alt = work.title || 'Work cover'
    img.addEventListener('error', () => media.remove())
    media.appendChild(img)
    content.appendChild(media)
  }
  let primaryAssetPath = ''
  if (!cover) {
    const primaryMedia = (work.assets || []).find((asset) => safeUrl(asset.path) && ['image', 'video', 'audio'].includes(asset.type))
    if (primaryMedia) {
      primaryAssetPath = safeUrl(primaryMedia.path)
      content.appendChild(createRelatedAsset(primaryMedia))
    }
  }

  const text = make('p', 'modal-body', work.body || work.description || work.summary || 'No description.')
  content.appendChild(text)

  const meta = make('div', 'work-meta')
  ;(work.tags || []).forEach((tag) => meta.appendChild(make('span', 'tag-pill', tag)))
  if (work.authorization_status) {
    meta.appendChild(make('span', 'license-badge', work.authorization_status))
  }
  content.appendChild(meta)

  const related = (work.assets || []).filter((asset) => asset.path && safeUrl(asset.path) !== primaryAssetPath)
  if (related.length) {
    const section = make('div', 'related-assets')
    section.appendChild(make('h3', '', 'Related public assets'))
    related.forEach((asset) => {
      section.appendChild(createRelatedAsset(asset))
    })
    content.appendChild(section)
  }

  modal.classList.remove('is-hidden')
  document.body.classList.add('modal-open')
}

function closeWorkModal() {
  $('work-modal').classList.add('is-hidden')
  document.body.classList.remove('modal-open')
}

function createRelatedAsset(asset) {
  const item = make('div', 'related-asset-card')
  const path = safeUrl(asset.path)
  const type = asset.type || 'asset'
  if (type === 'image') {
    const img = make('img')
    img.src = path
    img.alt = ''
    img.loading = 'lazy'
    img.addEventListener('error', () => img.remove())
    item.appendChild(img)
  } else if (type === 'video') {
    const video = make('video')
    video.src = path
    video.controls = true
    video.preload = 'metadata'
    item.appendChild(video)
  } else if (type === 'audio') {
    const audioWrap = make('div', 'related-audio')
    audioWrap.appendChild(make('span', '', 'Audio asset'))
    const audio = make('audio')
    audio.src = path
    audio.controls = true
    audio.preload = 'metadata'
    audioWrap.appendChild(audio)
    item.appendChild(audioWrap)
  } else if (type === 'document' && isPdfAsset(asset) && path) {
    const documentWrap = make('div', 'related-document')
    documentWrap.appendChild(make('span', '', 'PDF preview'))
    const frame = make('iframe', 'pdf-preview')
    frame.src = path
    frame.title = 'PDF preview'
    frame.loading = 'lazy'
    documentWrap.appendChild(frame)
    item.appendChild(documentWrap)
  } else if (type === 'document' && asset.text) {
    const documentWrap = make('div', 'related-document')
    documentWrap.appendChild(make('span', '', isMarkdownAsset(asset) ? 'Markdown preview' : 'Document text preview'))
    if (isMarkdownAsset(asset)) {
      documentWrap.appendChild(renderMarkdown(asset.text))
    } else {
      documentWrap.appendChild(make('pre', '', asset.text))
    }
    item.appendChild(documentWrap)
  }
  const row = make('div', 'related-asset-row')
  row.appendChild(make('span', '', type))
  row.appendChild(make('span', '', path))
  item.appendChild(row)
  return item
}

function appendParagraph(container, lines) {
  if (!lines.length) return
  container.appendChild(make('p', '', lines.join(' ')))
  lines.length = 0
}

function renderMarkdown(text) {
  const root = make('div', 'markdown-preview')
  const lines = String(text || '').split(/\r?\n/)
  const paragraph = []
  let list = null
  let code = null
  lines.forEach((raw) => {
    const line = raw.replace(/\s+$/, '')
    if (line.trim().startsWith('```')) {
      appendParagraph(root, paragraph)
      list = null
      if (code) {
        root.appendChild(code)
        code = null
      } else {
        code = make('pre')
      }
      return
    }
    if (code) {
      code.textContent += `${line}\n`
      return
    }
    if (!line.trim()) {
      appendParagraph(root, paragraph)
      list = null
      return
    }
    const heading = line.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      appendParagraph(root, paragraph)
      list = null
      root.appendChild(make(`h${heading[1].length}`, '', heading[2]))
      return
    }
    const item = line.match(/^[-*]\s+(.+)$/)
    if (item) {
      appendParagraph(root, paragraph)
      if (!list) {
        list = make('ul')
        root.appendChild(list)
      }
      list.appendChild(make('li', '', item[1]))
      return
    }
    const quote = line.match(/^>\s?(.+)$/)
    if (quote) {
      appendParagraph(root, paragraph)
      list = null
      root.appendChild(make('blockquote', '', quote[1]))
      return
    }
    paragraph.push(line.trim())
  })
  if (code) root.appendChild(code)
  appendParagraph(root, paragraph)
  if (!root.children.length) root.appendChild(make('p', '', 'No preview text.'))
  return root
}

init(data)
