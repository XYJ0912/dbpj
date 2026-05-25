async function loadJson(path, fallback) {
  try {
    const response = await fetch(path)
    if (!response.ok) return fallback
    return await response.json()
  } catch {
    return fallback
  }
}

function workCard(work) {
  const image = work.cover
    ? `<img src="${work.cover}" alt="">`
    : `<div class="placeholder"></div>`
  const tags = (work.tags || []).map((tag) => `<span class="tag">${tag}</span>`).join('')
  return `
    <article class="work-card">
      ${image}
      <div class="work-card__body">
        <h2>${work.title || 'Untitled work'}</h2>
        <p>${work.body || ''}</p>
        <div class="tags">${tags}</div>
      </div>
    </article>
  `
}

async function boot() {
  const [profile, works] = await Promise.all([
    loadJson('./data/profile.json', {}),
    loadJson('./data/works.json', []),
  ])

  document.title = `${profile.username || 'Creator'} - Homepage`
  document.getElementById('app').innerHTML = `
    <section class="hero">
      <span class="eyebrow">Creator Homepage</span>
      <h1>${profile.username || 'Creator'}</h1>
      <p class="bio">${profile.bio || 'Selected works and public portfolio snapshot.'}</p>
    </section>
    <section class="work-grid">
      ${works.map(workCard).join('')}
    </section>
  `
}

boot()
